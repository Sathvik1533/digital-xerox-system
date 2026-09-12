from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.order import PrintConfig, PricingBreakdown


class TimelineEvent(BaseModel):
    """
    Represents an ordered lifecycle event in the order timeline.
    Ordered lifecycle states:
    - CREATED / DOCUMENT_UPLOADED
    - PAYMENT_PENDING / PAID / PAYMENT_FAILED
    - QUEUED (with token, position, ETA)
    - PROCESSING
    - READY (pickup ready)
    - COMPLETED
    - REJECTED (with rejection reason)
    """
    model_config = ConfigDict(extra="ignore")

    event: str = Field(..., description="Canonical event identifier, e.g. CREATED, PAID, QUEUED, READY")
    title: str = Field(..., description="Human-friendly event title")
    description: str = Field(..., description="Detailed description of what occurred")
    timestamp: datetime = Field(..., description="UTC timestamp of the event")
    status: str = Field(default="COMPLETED", description="Event state: COMPLETED, CURRENT, PENDING, or FAILED")
    token_number: str | None = Field(default=None, description="Print token (e.g. X-101) when queued")
    queue_position: int | None = Field(default=None, description="1-based queue position when queued/active")
    estimated_completion_at: datetime | None = Field(default=None, description="Deterministic completion ETA")
    rejection_reason: str | None = Field(default=None, description="Formal operator rejection reason if rejected")
    payment_id: str | None = Field(default=None, description="Associated payment ID if applicable")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context metadata")


class OrderTimelineResponse(BaseModel):
    """Response schema for order timeline inspection."""
    model_config = ConfigDict(extra="ignore")

    order_id: str
    student_id: str
    current_status: str
    events: list[TimelineEvent] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PaymentReceipt(BaseModel):
    """Receipt and details of simulated payment transaction."""
    model_config = ConfigDict(extra="ignore")

    payment_id: str
    order_id: str
    payment_reference: str
    payment_reference_id: str
    amount_paise: int
    amount_rupees: float
    currency: str = "INR"
    status: str
    outcome: str
    failure_reason: str | None = None
    created_at: datetime


class StudentOrderHistoryItem(BaseModel):
    """
    Complete student order record for history and tracking portal (Vertical Slice 6).
    Includes payment details, timeline events, print config, price breakdown,
    token/queue/ETA, rejection reason, and fresh presigned S3 document URL.
    """
    model_config = ConfigDict(extra="ignore")

    order_id: str
    document_id: str
    student_id: str
    filename: str | None = None
    document_name: str | None = None
    document_key: str | None = None
    document_url: str | None = Field(default=None, description="Fresh time-limited presigned S3 download URL")
    download_url: str | None = Field(default=None, description="Alias for document_url")
    print_config: PrintConfig
    pricing: PricingBreakdown
    status: str
    payment_status: str
    payment_id: str | None = None
    payment_receipt: PaymentReceipt | None = None
    payment_details: PaymentReceipt | None = None
    token_number: str | None = None
    queue_position: int | None = Field(default=None, description="Live 1-based queue position (null if not in active queue)")
    estimated_completion_at: datetime | None = None
    estimated_wait_minutes: float | None = None
    rejection_reason: str | None = None
    timeline: list[TimelineEvent] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
