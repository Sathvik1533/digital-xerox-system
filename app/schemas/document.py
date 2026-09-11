from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    """Response schema for uploaded/queried document."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str
    student_id: str
    filename: str
    s3_key: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime
    download_url: str | None = None


class DocumentAccessResponse(BaseModel):
    """Response schema for controlled document access."""

    document_id: str
    filename: str
    download_url: str
    expires_in_seconds: int
