from datetime import datetime, timezone
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key
from app.core.config import get_settings
from app.models.document import Document
from app.models.order import Order
from app.models.payment import Payment


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
        }
        if payment_id:
            update_expr += ", #pid = :pid"
            expr_names["#pid"] = "payment_id"
            expr_values[":pid"] = payment_id

        response = self.table.update_item(
            Key={
                "PK": f"ORDER#{order_id}",
                "SK": f"ORDER#{order_id}",
            },
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues="ALL_NEW",
        )
        item = response.get("Attributes", {})
        item = _convert_decimals_to_native(item)
        return Order(**item)
