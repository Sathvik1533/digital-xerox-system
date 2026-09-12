from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.order import PricingBreakdown, PrintConfig


class RejectOrderRequest(BaseModel):
    """Request payload for staff rejecting an order."""
    model_config = ConfigDict(extra="ignore")

    rejection_reason: str | None = Field(
        default=None,
        description="Formal mandatory reason for rejecting the print order",
    )


class StaffOrderResponse(BaseModel):
    """Response payload for orders displayed in the Staff Operations Portal."""
    model_config = ConfigDict(extra="ignore")

    order_id: str
    token_number: str | None = None
    status: str
    payment_status: str | None = Field(default="SUCCESS", description="Payment status of the order")
    student_id: str
    document_id: str
    document_key: str | None = None
    filename: str | None = None
    document_url: str | None = Field(default=None, description="Presigned S3 GET URL for secure document inspection")
    print_config: PrintConfig
    pricing: PricingBreakdown
    queue_position: int = 0
    rejection_reason: str | None = None
    queue_entered_at: datetime | None = None
    estimated_completion_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

