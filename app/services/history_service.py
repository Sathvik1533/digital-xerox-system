from datetime import datetime, timezone
from app.models.document import Document
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.payment import Payment
from app.repositories.dynamodb_repo import DynamoDBRepository
from app.repositories.s3_repo import S3Repository
from app.schemas.history import (
    OrderTimelineResponse,
    PaymentReceipt,
    StudentOrderHistoryItem,
    TimelineEvent,
)
from app.services.order_service import OrderNotFoundError


class StudentIdRequiredError(Exception):
    """Raised when student_id is missing, empty, or whitespace."""

    def __init__(self):
        self.code = "STUDENT_ID_REQUIRED"
        self.message = "student_id parameter is required to access student orders."
        super().__init__(self.message)


class HistoryService:
    """
    Service for Student Order Portal: History, Tracking, Timelines, and Presigned Document Re-access.
    Vertical Slice 6: Complete Student Tracking + History.
    """

    def __init__(
        self,
        db_repo: DynamoDBRepository | None = None,
        s3_repo: S3Repository | None = None,
    ):
        self.db_repo = db_repo or DynamoDBRepository()
        self.s3_repo = s3_repo or S3Repository()

    def _generate_doc_url(self, document_key: str | None) -> str | None:
        """Generate time-limited presigned S3 GET URL for secure document access."""
        if not document_key:
            return None
        try:
            return self.s3_repo.generate_presigned_url(document_key, expiration=3600)
        except Exception:
            return None

    def build_timeline_events(
        self,
        order: Order,
        payment: Payment | None = None,
        queue_pos: int | None = None,
    ) -> list[TimelineEvent]:
        """
        Construct ordered, chronological lifecycle events with timestamps:
        - CREATED / DOCUMENT_UPLOADED
        - PAYMENT_PENDING / PAID / PAYMENT_FAILED
        - QUEUED (with token, position, ETA)
        - PROCESSING
        - READY (pickup ready)
        - COMPLETED
        - REJECTED (with rejection reason)
        """
        events: list[TimelineEvent] = []

        # 1. DOCUMENT_UPLOADED
        doc_name = order.filename or order.document_name or "file"
        events.append(
            TimelineEvent(
                event="DOCUMENT_UPLOADED",
                title="Document Uploaded",
                description=f"Document '{doc_name}' uploaded securely to S3",
                timestamp=order.created_at,
                status="COMPLETED",
                metadata={"document_id": order.document_id, "filename": doc_name},
            )
        )

        # 2. CREATED
        events.append(
            TimelineEvent(
                event="CREATED",
                title="Order Created",
                description=(
                    f"Print order created: {order.print_config.page_count} pages, "
                    f"{order.print_config.color_mode.upper()}, {order.print_config.copies} copy(ies), "
                    f"total ₹{order.pricing.total_price_rupees:.2f}"
                ),
                timestamp=order.created_at,
                status="COMPLETED",
                metadata={
                    "page_count": order.print_config.page_count,
                    "copies": order.print_config.copies,
                    "color_mode": order.print_config.color_mode,
                    "paper_size": order.print_config.paper_size,
                    "total_price_paise": order.pricing.total_price_paise,
                },
            )
        )

        # 3. PAYMENT_PENDING / PAID / PAYMENT_FAILED
        if (
            order.status == OrderStatus.PAYMENT_FAILED.value
            or order.payment_status == PaymentStatus.FAILED.value
        ):
            fail_reason = (
                payment.failure_reason
                if (payment and payment.failure_reason)
                else "Simulated payment transaction was declined."
            )
            pay_time = payment.created_at if payment else order.updated_at
            events.append(
                TimelineEvent(
                    event="PAYMENT_FAILED",
                    title="Payment Failed",
                    description=fail_reason,
                    timestamp=pay_time,
                    status="FAILED",
                    payment_id=payment.payment_id if payment else order.payment_id,
                    metadata={"failure_reason": fail_reason},
                )
            )
        elif (
            order.payment_status == PaymentStatus.SUCCESS.value
            or order.status
            in (
                OrderStatus.PAID.value,
                OrderStatus.QUEUED.value,
                OrderStatus.PROCESSING.value,
                OrderStatus.READY.value,
                OrderStatus.COMPLETED.value,
            )
        ):
            pay_time = payment.created_at if payment else order.updated_at
            events.append(
                TimelineEvent(
                    event="PAID",
                    title="Payment Confirmed",
                    description=f"Simulated payment of ₹{order.pricing.total_price_rupees:.2f} confirmed.",
                    timestamp=pay_time,
                    status="COMPLETED",
                    payment_id=payment.payment_id if payment else order.payment_id,
                    metadata={
                        "payment_reference": payment.payment_reference if payment else None,
                        "amount_paise": order.pricing.total_price_paise,
                    },
                )
            )
        else:
            events.append(
                TimelineEvent(
                    event="PAYMENT_PENDING",
                    title="Payment Pending",
                    description=f"Awaiting simulated payment of ₹{order.pricing.total_price_rupees:.2f}.",
                    timestamp=order.created_at,
                    status="CURRENT",
                )
            )

        # 4. QUEUED (with token, position, ETA)
        if order.token_number or order.status in (
            OrderStatus.QUEUED.value,
            OrderStatus.PROCESSING.value,
            OrderStatus.READY.value,
            OrderStatus.COMPLETED.value,
            OrderStatus.REJECTED.value,
        ):
            q_time = order.queue_entered_at or order.updated_at
            pos_text = f" (Queue Position #{queue_pos})" if queue_pos else ""
            events.append(
                TimelineEvent(
                    event="QUEUED",
                    title="Order Queued",
                    description=f"Print token {order.token_number} assigned. Entered operational queue{pos_text}.",
                    timestamp=q_time,
                    status="CURRENT" if order.status == OrderStatus.QUEUED.value else "COMPLETED",
                    token_number=order.token_number,
                    queue_position=queue_pos,
                    estimated_completion_at=order.estimated_completion_at,
                )
            )

        # 5. PROCESSING
        if order.status in (
            OrderStatus.PROCESSING.value,
            OrderStatus.READY.value,
            OrderStatus.COMPLETED.value,
        ):
            events.append(
                TimelineEvent(
                    event="PROCESSING",
                    title="Printing in Progress",
                    description="Operator accepted order. Printing has begun on production printers.",
                    timestamp=order.updated_at,
                    status="CURRENT" if order.status == OrderStatus.PROCESSING.value else "COMPLETED",
                    token_number=order.token_number,
                )
            )

        # 6. REJECTED (with rejection reason)
        if order.status == OrderStatus.REJECTED.value:
            events.append(
                TimelineEvent(
                    event="REJECTED",
                    title="Order Rejected",
                    description=f"Order rejected by operator: {order.rejection_reason or 'No reason provided.'}",
                    timestamp=order.updated_at,
                    status="FAILED",
                    rejection_reason=order.rejection_reason,
                    token_number=order.token_number,
                )
            )

        # 7. READY (pickup ready)
        if order.status in (OrderStatus.READY.value, OrderStatus.COMPLETED.value):
            events.append(
                TimelineEvent(
                    event="READY",
                    title="Ready for Pickup",
                    description="Print job completed! Package ready for pickup at stationery counter.",
                    timestamp=order.updated_at,
                    status="CURRENT" if order.status == OrderStatus.READY.value else "COMPLETED",
                    token_number=order.token_number,
                )
            )

        # 8. COMPLETED
        if order.status == OrderStatus.COMPLETED.value:
            events.append(
                TimelineEvent(
                    event="COMPLETED",
                    title="Order Completed",
                    description="Order collected by student. Thank you!",
                    timestamp=order.updated_at,
                    status="COMPLETED",
                    token_number=order.token_number,
                )
            )

        return events

    def get_student_order_history(self, student_id: str) -> list[StudentOrderHistoryItem]:
        """
        Retrieve complete order history for authenticated/requesting student.
        - Isolated strictly to student_id: returns [] if no orders found.
        - Orders sorted chronologically descending.
        - Generates fresh presigned S3 URL for each document.
        - Embeds payment receipt details, queue position, ETA, rejection reasons, and timeline.
        """
        if not student_id or not student_id.strip():
            raise StudentIdRequiredError()

        clean_student_id = student_id.strip()
        orders = self.db_repo.get_orders_by_student_id(clean_student_id)
        if not orders:
            return []

        # Load active queue items to compute current positions
        active_items = self.db_repo.get_active_queue_items()
        active_positions = {it.get("order_id"): idx + 1 for idx, it in enumerate(active_items)}

        now = datetime.now(timezone.utc)
        result: list[StudentOrderHistoryItem] = []

        for order in orders:
            # Fresh presigned S3 download URL
            doc_key = order.document_key
            if not doc_key and order.document_id:
                doc = self.db_repo.get_document(order.document_id)
                if doc:
                    doc_key = doc.s3_key

            doc_url = self._generate_doc_url(doc_key)

            # Payment receipt
            payment = self.db_repo.get_payment_by_order_id(order.order_id)
            payment_receipt = None
            if payment:
                payment_receipt = PaymentReceipt(
                    payment_id=payment.payment_id,
                    order_id=payment.order_id,
                    payment_reference=payment.payment_reference,
                    payment_reference_id=payment.payment_reference_id,
                    amount_paise=payment.amount_paise,
                    amount_rupees=payment.amount_rupees,
                    currency=payment.currency,
                    status=payment.status,
                    outcome=payment.outcome,
                    failure_reason=payment.failure_reason,
                    created_at=payment.created_at,
                )

            # Queue position & ETA
            queue_pos = active_positions.get(order.order_id)
            est_wait_min = None
            if queue_pos and order.estimated_completion_at:
                est_dt = order.estimated_completion_at
                if est_dt.tzinfo is None:
                    est_dt = est_dt.replace(tzinfo=timezone.utc)
                remaining_sec = max(0, int((est_dt - now).total_seconds()))
                est_wait_min = round(remaining_sec / 60.0, 1)

            # Status timeline events
            timeline = self.build_timeline_events(order, payment=payment, queue_pos=queue_pos)

            result.append(
                StudentOrderHistoryItem(
                    order_id=order.order_id,
                    document_id=order.document_id,
                    student_id=order.student_id,
                    filename=order.filename,
                    document_name=order.document_name or order.filename,
                    document_key=doc_key,
                    document_url=doc_url,
                    download_url=doc_url,
                    print_config=order.print_config,
                    pricing=order.pricing,
                    status=order.status,
                    payment_status=order.payment_status,
                    payment_id=order.payment_id or (payment.payment_id if payment else None),
                    payment_receipt=payment_receipt,
                    payment_details=payment_receipt,
                    token_number=order.token_number,
                    queue_position=queue_pos,
                    estimated_completion_at=order.estimated_completion_at,
                    estimated_wait_minutes=est_wait_min,
                    rejection_reason=order.rejection_reason,
                    timeline=timeline,
                    created_at=order.created_at,
                    updated_at=order.updated_at,
                )
            )

        return result

    def get_order_timeline(self, order_id: str) -> OrderTimelineResponse:
        """Retrieve status timeline for a specific order."""
        order = self.db_repo.get_order(order_id)
        if not order:
            raise OrderNotFoundError(order_id)

        payment = self.db_repo.get_payment_by_order_id(order_id)

        active_items = self.db_repo.get_active_queue_items()
        active_positions = {it.get("order_id"): idx + 1 for idx, it in enumerate(active_items)}
        queue_pos = active_positions.get(order_id)

        events = self.build_timeline_events(order, payment=payment, queue_pos=queue_pos)

        return OrderTimelineResponse(
            order_id=order.order_id,
            student_id=order.student_id,
            current_status=order.status,
            events=events,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
