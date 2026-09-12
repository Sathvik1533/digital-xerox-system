from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class QueueAdmissionResponse(BaseModel):
    """Response schema returned when an order enters the queue."""
    model_config = ConfigDict(extra="ignore")

    order_id: str
    token_number: str
    queue_position: int = Field(..., description="1-based position in active queue")
    estimated_completion_at: datetime = Field(..., description="Backend-calculated deterministic ETA")
    estimated_wait_minutes: float = Field(..., description="Estimated wait time in minutes")
    estimated_wait_seconds: int = Field(..., description="Estimated wait time in seconds")
    active_queue_length: int = Field(..., description="Total number of active orders in queue")
    status: str = Field(default="QUEUED")
    queue_entered_at: datetime


class QueueStatusResponse(BaseModel):
    """Response schema for checking current queue status and ETA."""
    model_config = ConfigDict(extra="ignore")

    order_id: str
    token_number: str
    queue_position: int = Field(..., description="Current 1-based position in queue")
    estimated_completion_at: datetime = Field(..., description="Current backend-calculated deterministic ETA")
    estimated_wait_minutes: float = Field(..., description="Estimated wait time remaining in minutes")
    estimated_wait_seconds: int = Field(..., description="Estimated wait time remaining in seconds")
    active_queue_length: int = Field(..., description="Total number of active orders in queue")
    status: str
    queue_entered_at: datetime
    total_pages_printed: int | None = None
    color_mode: str | None = None
    paper_size: str | None = None
    copies: int | None = None
    rejection_reason: str | None = None
