from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SimulatePaymentRequest(BaseModel):
    """Request schema for simulated payment execution."""
    model_config = ConfigDict(extra="ignore")

    outcome: str = Field(
        default="SUCCESS",
        description="Deterministic simulated payment outcome: 'SUCCESS' or 'FAILURE'",
    )


class PaymentResponse(BaseModel):
    """Response schema for payment operations."""
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
    order_status: str | None = None
    created_at: datetime
    updated_at: datetime
