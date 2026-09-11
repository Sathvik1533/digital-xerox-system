from decimal import Decimal
import boto3
from app.core.config import get_settings
from app.models.document import Document
from app.models.order import Order


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
