from datetime import datetime
from pydantic import BaseModel, ConfigDict


class Document(BaseModel):
    """Document model representing an uploaded file and its metadata."""

    model_config = ConfigDict(extra="ignore")

    document_id: str
    student_id: str = "anonymous"
    filename: str
    s3_key: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime
