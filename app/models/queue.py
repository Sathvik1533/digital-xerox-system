from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field


class QueueItem(BaseModel):
    """Operational queue item entity stored in DynamoDB under PK: QUEUE#ACTIVE."""
    model_config = ConfigDict(extra="ignore")

    order_id: str
    token_number: str
    queue_entered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    estimated_completion_at: datetime
    estimated_wait_seconds: int = 0
    queue_position: int = 1
    total_pages_printed: int = 1
    color_mode: str = "bw"
    paper_size: str = "A4"
    copies: int = 1
    sidedness: str = "SINGLE"
    status: str = "QUEUED"
    student_id: str = "anonymous"
    filename: str | None = None
    document_id: str | None = None
    document_key: str | None = None
    rejection_reason: str | None = None
