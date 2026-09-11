from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class ColorMode(str, Enum):
    BW = "bw"
    COLOR = "color"


class PaperSize(str, Enum):
    A4 = "A4"
    A3 = "A3"
    LETTER = "Letter"


class OrderStatus(str, Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    PROCESSING = "PROCESSING"
    READY = "READY"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    PAYMENT_FAILED = "PAYMENT_FAILED"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PrintConfig(BaseModel):
    """Print configuration options selected by student."""
    model_config = ConfigDict(extra="ignore")

    page_count: int = Field(default=1, description="Number of pages in the document")
    color_mode: str = Field(default="bw", description="Color mode: bw or color")
    paper_size: str = Field(default="A4", description="Paper size: A4, A3, Letter")
    copies: int = Field(default=1, description="Number of physical copies")
    double_sided: bool = Field(default=False, description="Print on both sides of each sheet")
    sidedness: str = Field(default="SINGLE", description="Sidedness: SINGLE or DOUBLE")


class PricingBreakdown(BaseModel):
    """Detailed pricing calculation breakdown."""
    model_config = ConfigDict(extra="ignore")

    base_rate_per_page_paise: int
    paper_multiplier: float
    sheets_per_copy: int
    total_sheets: int
    total_pages_printed: int
    unit_price_paise: int
    total_price_paise: int
    total_price_rupees: float
    currency: str = "INR"


class Order(BaseModel):
    """Order entity according to DATA-001 specification."""
    model_config = ConfigDict(extra="ignore")

    order_id: str
    document_id: str
    student_id: str = "anonymous"
    filename: str | None = None
    document_key: str | None = None
    document_name: str | None = None
    document_content_type: str | None = None
    document_size: int | None = None
    print_config: PrintConfig
    pricing: PricingBreakdown
    status: str = OrderStatus.PENDING_PAYMENT.value
    payment_status: str = PaymentStatus.PENDING.value
    payment_id: str | None = None
    token_number: str | None = None
    scheduled_time: str | None = None
    queue_entered_at: datetime | None = None
    estimated_completion_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
