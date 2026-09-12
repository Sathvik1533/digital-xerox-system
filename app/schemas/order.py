from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.order import PrintConfig, PricingBreakdown


class CreateOrderRequest(BaseModel):
    """Request schema for creating a new print order."""
    model_config = ConfigDict(extra="ignore")

    document_id: str = Field(..., description="ID of previously uploaded document")
    student_id: str = Field(default="anonymous", description="Student ID creating the order")
    page_count: int = Field(..., description="Number of pages in the document")
    color_mode: str = Field(default="bw", description="Print color mode ('bw' or 'color')")
    paper_size: str = Field(default="A4", description="Paper size ('A4', 'A3', 'Letter')")
    copies: int = Field(default=1, description="Number of copies")
    double_sided: bool = Field(default=False, description="Whether to print double-sided")
    sidedness: str | None = Field(default=None, description="Print sidedness ('SINGLE' or 'DOUBLE')")
    scheduled_time: str | None = Field(default=None, description="Optional scheduled print/pickup time")


class OrderResponse(BaseModel):
    """Response schema for order creation and retrieval according to DATA-001."""
    model_config = ConfigDict(extra="ignore")

    order_id: str
    document_id: str
    student_id: str
    filename: str | None = None
    document_key: str | None = None
    document_name: str | None = None
    document_content_type: str | None = None
    document_size: int | None = None
    print_config: PrintConfig
    pricing: PricingBreakdown
    status: str
    payment_status: str
    payment_id: str | None = None
    scheduled_time: str | None = None
    token_number: str | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime
