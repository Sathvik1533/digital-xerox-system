from datetime import datetime, timezone
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from app.core.config import get_settings
from app.models.document import Document
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.payment import Payment


class OrderStateConflictError(Exception):
    """Raised when DynamoDB conditional check fails during order state update."""
    pass


def _convert_floats_to_decimals(obj):
    """Recursively convert float values to Decimal for DynamoDB compatibility."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _convert_floats_to_decimals(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_floats_to_decimals(v) for v in obj]
    return obj


def _convert_decimals_to_native(obj):
    """Recursively convert Decimal values back to int/float for Pydantic models."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {k: _convert_decimals_to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_decimals_to_native(v) for v in obj]
    return obj


class DynamoDBRepository:
    def __init__(self):
        settings = get_settings()
        self.table_name = settings.dynamodb_table_name

        db_kwargs = {
            "region_name": settings.aws_region,
        }
        if settings.dynamodb_endpoint_url:
            db_kwargs["endpoint_url"] = settings.dynamodb_endpoint_url
        if settings.aws_access_key_id:
            db_kwargs["aws_access_key_id"] = settings.aws_access_key_id
            db_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key

        self.dynamodb = boto3.resource("dynamodb", **db_kwargs)
        self.table = self.dynamodb.Table(self.table_name)

    def save_document(self, document: Document) -> None:
        """Persist document metadata in DynamoDB."""
        item = document.model_dump()
        item["PK"] = f"DOC#{document.document_id}"
        item["SK"] = f"DOC#{document.document_id}"
        item["uploaded_at"] = item["uploaded_at"].isoformat()

        self.table.put_item(Item=item)

    def get_document(self, document_id: str) -> Document | None:
        """Retrieve document metadata by document_id."""
        response = self.table.get_item(
            Key={
                "PK": f"DOC#{document_id}",
                "SK": f"DOC#{document_id}",
            }
        )
        item = response.get("Item")
        if not item:
            return None
        return Document(**item)

    def save_order(self, order: Order) -> None:
        """
        Persist order in DynamoDB according to DATA-001:
        PK: ORDER#{order_id} / SK: ORDER#{order_id}
        """
        item = order.model_dump()
        item["PK"] = f"ORDER#{order.order_id}"
        item["SK"] = f"ORDER#{order.order_id}"
        item["created_at"] = item["created_at"].isoformat()
        item["updated_at"] = item["updated_at"].isoformat()
        if item.get("queue_entered_at"):
            item["queue_entered_at"] = item["queue_entered_at"].isoformat()
        if item.get("estimated_completion_at"):
            item["estimated_completion_at"] = item["estimated_completion_at"].isoformat()

        # Flat canonical attributes for index and direct access patterns (DATA-001)
        item["color_mode"] = order.print_config.color_mode
        item["paper_size"] = order.print_config.paper_size
        item["copies"] = order.print_config.copies
        item["sidedness"] = order.print_config.sidedness
        item["total_price_paise"] = order.pricing.total_price_paise
        item["total_price_rupees"] = order.pricing.total_price_rupees

        item = _convert_floats_to_decimals(item)

        self.table.put_item(Item=item)

    def get_order(self, order_id: str) -> Order | None:
        """Retrieve order by order_id from DynamoDB."""
        response = self.table.get_item(
            Key={
                "PK": f"ORDER#{order_id}",
                "SK": f"ORDER#{order_id}",
            }
        )
        item = response.get("Item")
        if not item:
            return None
        item = _convert_decimals_to_native(item)
        return Order(**item)

    def save_payment(self, payment: Payment) -> None:
        """
        Persist payment in DynamoDB according to DATA-001 single-table design:
        PK: ORDER#{order_id} / SK: PAYMENT#{payment_id}
        Also writes aliases for fast direct lookup.
        """
        item = payment.model_dump()
        item["PK"] = f"ORDER#{payment.order_id}"
        item["SK"] = f"PAYMENT#{payment.payment_id}"
        item["created_at"] = item["created_at"].isoformat()
        item["updated_at"] = item["updated_at"].isoformat()
        item = _convert_floats_to_decimals(item)
        self.table.put_item(Item=item)

        # Alias for direct order payment key lookup
        order_key_item = dict(item)
        order_key_item["SK"] = f"PAYMENT#{payment.order_id}"
        self.table.put_item(Item=order_key_item)

        # Alias for direct payment ID key lookup
        pay_id_item = dict(item)
        pay_id_item["PK"] = f"PAYMENT#{payment.payment_id}"
        pay_id_item["SK"] = f"PAYMENT#{payment.payment_id}"
        self.table.put_item(Item=pay_id_item)

    def get_payment_by_order_id(self, order_id: str) -> Payment | None:
        """Retrieve latest payment for an order from DynamoDB."""
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"ORDER#{order_id}") & Key("SK").begins_with("PAYMENT#")
        )
        items = response.get("Items", [])
        if not items:
            res = self.table.get_item(
                Key={
                    "PK": f"ORDER#{order_id}",
                    "SK": f"PAYMENT#{order_id}",
                }
            )
            item = res.get("Item")
            if not item:
                return None
            items = [item]

        # Deduplicate and sort by created_at descending
        unique = {}
        for it in items:
            pid = it.get("payment_id")
            if pid and pid not in unique:
                unique[pid] = it

        target_items = list(unique.values()) if unique else items
        target_items.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        latest = _convert_decimals_to_native(target_items[0])
        return Payment(**latest)

    def update_order_payment_state(
        self,
        order_id: str,
        payment_status: str,
        order_status: str,
        payment_id: str | None = None,
    ) -> Order:
        """
        Atomically update order payment_status and order status in DynamoDB.
        On SUCCESS: payment_status='SUCCESS', status='PAID'
        On FAILURE: payment_status='FAILED', status='PAYMENT_FAILED'
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        update_expr = "SET #ps = :ps, #st = :st, #ua = :ua"
        expr_names = {
            "#ps": "payment_status",
            "#st": "status",
            "#ua": "updated_at",
        }
        expr_values = {
            ":ps": payment_status,
            ":st": order_status,
            ":ua": now_iso,
            ":st_pending": OrderStatus.PENDING_PAYMENT.value,
            ":st_failed": OrderStatus.PAYMENT_FAILED.value,
        }
        if payment_id:
            update_expr += ", #pid = :pid"
            expr_names["#pid"] = "payment_id"
            expr_values[":pid"] = payment_id

        try:
            response = self.table.update_item(
                Key={
                    "PK": f"ORDER#{order_id}",
                    "SK": f"ORDER#{order_id}",
                },
                UpdateExpression=update_expr,
                ConditionExpression="attribute_exists(PK) AND #st IN (:st_pending, :st_failed)",
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values,
                ReturnValues="ALL_NEW",
            )
            item = response.get("Attributes", {})
            item = _convert_decimals_to_native(item)
            return Order(**item)
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                raise OrderStateConflictError(
                    f"Order '{order_id}' cannot be updated: order does not exist or is not in a payable state."
                ) from e
            raise

    def generate_next_token(self, prefix: str = "X") -> str:
        """
        Atomically generate sequential, human-friendly token (e.g. X-101, X-102...).
        Uses atomic DynamoDB ADD counter on PK: COUNTER#TOKEN / SK: COUNTER#TOKEN.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        response = self.table.update_item(
            Key={
                "PK": "COUNTER#TOKEN",
                "SK": "COUNTER#TOKEN",
            },
            UpdateExpression="ADD last_token_number :inc SET updated_at = :now",
            ExpressionAttributeValues={
                ":inc": 1,
                ":now": now_iso,
            },
            ReturnValues="UPDATED_NEW",
        )
        counter_val = int(response["Attributes"]["last_token_number"])
        return f"{prefix}-{100 + counter_val}"

    def get_active_queue_items(self) -> list[dict]:
        """
        Retrieve all operational items currently in active queue (PK: QUEUE#ACTIVE),
        sorted chronologically by queue_entered_at.
        """
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq("QUEUE#ACTIVE")
        )
        raw_items = response.get("Items", [])
        items = [_convert_decimals_to_native(item) for item in raw_items]
        items.sort(key=lambda x: (str(x.get("queue_entered_at", "")), str(x.get("token_number", ""))))
        return items

    def get_queue_item(self, order_id: str) -> dict | None:
        """Retrieve an active queue item by order_id."""
        response = self.table.get_item(
            Key={
                "PK": "QUEUE#ACTIVE",
                "SK": f"ORDER#{order_id}",
            }
        )
        item = response.get("Item")
        if not item:
            return None
        return _convert_decimals_to_native(item)

    def add_order_to_queue(
        self,
        order: Order,
        token_number: str,
        queue_entered_at: datetime,
        estimated_completion_at: datetime,
    ) -> Order:
        """
        Atomically admit a paid order to the queue.
        1. Conditionally updates the Order item (must be in PAID status with payment_status SUCCESS and no existing token).
        2. Persists active queue record in PK: QUEUE#ACTIVE / SK: ORDER#{order_id}.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        q_entered_iso = queue_entered_at.isoformat()
        est_completion_iso = estimated_completion_at.isoformat()

        update_expr = (
            "SET #st = :st_queued, #token = :token, #qe = :qe, #ec = :ec, #ua = :ua"
        )
        expr_names = {
            "#st": "status",
            "#token": "token_number",
            "#qe": "queue_entered_at",
            "#ec": "estimated_completion_at",
            "#ua": "updated_at",
            "#ps": "payment_status",
        }
        expr_values = {
            ":st_queued": OrderStatus.QUEUED.value,
            ":st_paid": OrderStatus.PAID.value,
            ":ps_success": PaymentStatus.SUCCESS.value,
            ":token": token_number,
            ":qe": q_entered_iso,
            ":ec": est_completion_iso,
            ":ua": now_iso,
            ":null": None,
        }

        try:
            response = self.table.update_item(
                Key={
                    "PK": f"ORDER#{order.order_id}",
                    "SK": f"ORDER#{order.order_id}",
                },
                UpdateExpression=update_expr,
                ConditionExpression="attribute_exists(PK) AND #st = :st_paid AND #ps = :ps_success AND (#token = :null OR attribute_not_exists(#token))",
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values,
                ReturnValues="ALL_NEW",
            )
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                raise OrderStateConflictError(
                    f"Order '{order.order_id}' cannot enter queue: not in PAID state or already queued."
                ) from e
            raise

        # Add to PK: QUEUE#ACTIVE
        queue_item = {
            "PK": "QUEUE#ACTIVE",
            "SK": f"ORDER#{order.order_id}",
            "order_id": order.order_id,
            "token_number": token_number,
            "queue_entered_at": q_entered_iso,
            "estimated_completion_at": est_completion_iso,
            "page_count": order.print_config.page_count,
            "copies": order.print_config.copies,
            "total_pages_printed": order.pricing.total_pages_printed,
            "color_mode": order.print_config.color_mode,
            "paper_size": order.print_config.paper_size,
            "sidedness": order.print_config.sidedness,
            "status": OrderStatus.QUEUED.value,
            "student_id": order.student_id,
            "filename": order.filename,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        queue_item = _convert_floats_to_decimals(queue_item)
        self.table.put_item(Item=queue_item)

        updated_order_dict = _convert_decimals_to_native(response.get("Attributes", {}))
        return Order(**updated_order_dict)
