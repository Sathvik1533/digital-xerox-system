import uuid
from datetime import datetime, timezone
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentOutcome, PaymentStatus
from app.repositories.dynamodb_repo import DynamoDBRepository
from app.services.order_service import OrderNotFoundError


class PaymentValidationError(Exception):
    """Raised when payment simulation or validation fails."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class OrderNotPayableError(PaymentValidationError):
    """Raised when an order is not in a payable state."""
    pass


class PaymentNotFoundError(Exception):
    """Raised when no payment record exists for an order."""

    def __init__(self, order_id: str):
        self.code = "PAYMENT_NOT_FOUND"
        self.message = f"No payment record found for order '{order_id}'."
        super().__init__(self.message)


class PaymentService:
    """
    Simulated payment processing service for Vertical Slice 3.
    Deterministic simulation only — NO live payment gateways or external SDKs.
    Authoritatively takes amounts from persisted Order pricing, recalculates and validates.
    """

    def __init__(self, db_repo: DynamoDBRepository | None = None):
        self.db_repo = db_repo or DynamoDBRepository()

    def simulate_payment(
        self,
        order_id: str,
        outcome: str = "SUCCESS",
    ) -> tuple[Payment, Order]:
        """
        Execute deterministic payment simulation for an existing order.
        Validates order status and never trusts client-provided amounts.
        """
        # 1. Fetch authoritative order from DynamoDB
        order = self.db_repo.get_order(order_id)
        if not order:
            raise OrderNotFoundError(order_id)

        # 2. Check if order is in a payable state
        if order.payment_status == PaymentStatus.SUCCESS.value or order.status == OrderStatus.PAID.value:
            raise OrderNotPayableError(
                "ORDER_ALREADY_PAID",
                f"Order '{order_id}' is already paid and cannot be paid again.",
            )

        allowed_statuses = [
            OrderStatus.PENDING_PAYMENT.value,
            OrderStatus.PAYMENT_FAILED.value,
        ]
        if order.status not in allowed_statuses:
            raise OrderNotPayableError(
                "ORDER_NOT_PAYABLE",
                f"Order '{order_id}' in status '{order.status}' is not eligible for payment.",
            )

        # 3. Validate and normalize simulation outcome
        norm_outcome = outcome.strip().upper() if outcome else PaymentOutcome.SUCCESS.value
        if norm_outcome not in (PaymentOutcome.SUCCESS.value, PaymentOutcome.FAILURE.value):
            raise PaymentValidationError(
                "INVALID_PAYMENT_OUTCOME",
                f"Simulated outcome '{outcome}' is invalid. Allowed values: 'SUCCESS', 'FAILURE'.",
            )

        # 4. Generate reference IDs and extract authoritative pricing
        payment_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        payment_reference = f"SIMPAY-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.now(timezone.utc)

        amount_paise = order.pricing.total_price_paise
        amount_rupees = order.pricing.total_price_rupees
        currency = getattr(order.pricing, "currency", "INR") or "INR"

        if norm_outcome == PaymentOutcome.SUCCESS.value:
            payment_status = PaymentStatus.SUCCESS.value
            new_order_status = OrderStatus.PAID.value
            failure_reason = None
        else:
            payment_status = PaymentStatus.FAILED.value
            new_order_status = OrderStatus.PAYMENT_FAILED.value
            failure_reason = "Simulated payment failure requested by client."

        # 5. Construct domain model
        payment = Payment(
            payment_id=payment_id,
            order_id=order.order_id,
            payment_reference=payment_reference,
            payment_reference_id=payment_reference,
            amount_paise=amount_paise,
            amount_rupees=amount_rupees,
            currency=currency,
            status=payment_status,
            outcome=norm_outcome,
            failure_reason=failure_reason,
            created_at=now,
            updated_at=now,
        )

        # 6. Persist payment record
        self.db_repo.save_payment(payment)

        # 7. Atomically update order payment status and order status in DynamoDB
        updated_order = self.db_repo.update_order_payment_state(
            order_id=order.order_id,
            payment_status=payment_status,
            order_status=new_order_status,
            payment_id=payment_id,
        )

        return payment, updated_order

    def get_payment_for_order(self, order_id: str) -> Payment:
        """Retrieve payment details for an order."""
        order = self.db_repo.get_order(order_id)
        if not order:
            raise OrderNotFoundError(order_id)

        payment = self.db_repo.get_payment_by_order_id(order_id)
        if not payment:
            raise PaymentNotFoundError(order_id)

        return payment
