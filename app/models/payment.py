from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class Payment(BaseModel):
    """
    Payment entity for deterministic simulation per Slice 3 requirements.
    Never trusts client payment state; persists amount and currency directly
    from authoritative order pricing breakdown.
    """
    model_config = ConfigDict(extra="ignore")

    payment_id: str
    order_id: str
    payment_reference: str
    payment_reference_id: str
    amount_paise: int
    amount_rupees: float
    currency: str = "INR"
    status: str = PaymentStatus.PENDING.value
    outcome: str = PaymentOutcome.SUCCESS.value
    failure_reason: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
