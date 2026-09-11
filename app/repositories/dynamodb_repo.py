import boto3
from app.core.config import get_settings
from app.models.document import Document

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
                "SK": f"DOC#{document_id}"
            }
        )
        item = response.get("Item")
        if not item:
            return None
        return Document(**item)
