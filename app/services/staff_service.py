from datetime import datetime, timezone
from app.models.order import Order, OrderStatus
from app.repositories.dynamodb_repo import DynamoDBRepository, OrderStateConflictError
from app.repositories.s3_repo import S3Repository
from app.schemas.staff import StaffOrderResponse
from app.services.order_service import OrderNotFoundError


class StaffError(Exception):
    """Base exception for staff operations."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class InvalidStateTransitionError(StaffError):
    """Raised when an invalid lifecycle state transition is attempted."""

    def __init__(self, current_status: str, target_status: str):
        super().__init__(
            code="INVALID_STATE_TRANSITION",
            message=(
                f"Cannot transition order from '{current_status}' to '{target_status}'. "
                f"Allowed transitions: QUEUED -> PROCESSING | REJECTED, "
                f"PROCESSING -> READY, READY -> COMPLETED."
            ),
        )
        self.current_status = current_status
        self.target_status = target_status


class RejectionReasonRequiredError(StaffError):
    """Raised when staff rejects an order without providing a non-empty reason."""

    def __init__(self):
        super().__init__(
            code="REJECTION_REASON_REQUIRED",
            message="A non-empty rejection reason is required to reject an order.",
        )


class StaffService:
    """
    Staff processing service for managing order lifecycle transitions:
    QUEUED -> PROCESSING (Accept) or REJECTED (with reason)
    PROCESSING -> READY (Mark ready for pickup; removed from active queue)
    READY -> COMPLETED (Collected by student)
    """

    def __init__(
        self,
        db_repo: DynamoDBRepository | None = None,
        s3_repo: S3Repository | None = None,
    ):
        self.db_repo = db_repo or DynamoDBRepository()
        self.s3_repo = s3_repo or S3Repository()

    def _generate_doc_url(self, document_key: str | None) -> str | None:
        """Generate a secure S3 presigned GET URL for staff inspection."""
        if not document_key:
            return None
        try:
            return self.s3_repo.generate_presigned_url(document_key, expiration=3600)
        except Exception:
            return None

    def _build_staff_response(
        self,
        order: Order,
        queue_position: int = 0,
    ) -> StaffOrderResponse:
        """Helper to construct StaffOrderResponse with document presigned URL."""
        doc_url = self._generate_doc_url(order.document_key)
        return StaffOrderResponse(
            order_id=order.order_id,
            token_number=order.token_number,
            status=order.status,
            student_id=order.student_id,
            document_id=order.document_id,
            document_key=order.document_key,
            filename=order.filename,
            document_url=doc_url,
            print_config=order.print_config,
            pricing=order.pricing,
            queue_position=queue_position,
            rejection_reason=order.rejection_reason,
            queue_entered_at=order.queue_entered_at,
            estimated_completion_at=order.estimated_completion_at,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    def list_orders(self, status_filter: str | None = None) -> list[StaffOrderResponse]:
        """
        List orders for staff view:
        - By default (or status_filter='ACTIVE'), returns all active queue orders (QUEUED, PROCESSING).
        - If status_filter='ALL', returns all orders across all states.
        - If status_filter is specific (e.g. READY, COMPLETED, REJECTED), returns matching orders.
        """
        active_items = self.db_repo.get_active_queue_items()
        active_order_ids = {it.get("order_id"): idx + 1 for idx, it in enumerate(active_items)}

        norm_filter = status_filter.upper().strip() if status_filter else "ACTIVE"

        if norm_filter == "ACTIVE":
            result = []
            for idx, item in enumerate(active_items):
                order_id = item.get("order_id")
                if not order_id:
                    continue
                order = self.db_repo.get_order(order_id)
                if order:
                    result.append(self._build_staff_response(order, queue_position=idx + 1))
            return result

        if norm_filter in (OrderStatus.QUEUED.value, OrderStatus.PROCESSING.value):
            result = []
            for idx, item in enumerate(active_items):
                if item.get("status") == norm_filter:
                    order_id = item.get("order_id")
                    if not order_id:
                        continue
                    order = self.db_repo.get_order(order_id)
                    if order:
                        result.append(self._build_staff_response(order, queue_position=idx + 1))
            return result

        # For ALL, READY, COMPLETED, REJECTED: fetch all orders
        all_orders = self.db_repo.get_all_orders()
        result = []
        for order in all_orders:
            if norm_filter != "ALL" and order.status != norm_filter:
                continue
            pos = active_order_ids.get(order.order_id, 0)
            result.append(self._build_staff_response(order, queue_position=pos))

        return result

    def accept_order(self, order_id: str) -> StaffOrderResponse:
        """
        Accept an incoming order:
        Transition: QUEUED -> PROCESSING
        Order remains in active queue with updated PROCESSING status.
        """
        order = self.db_repo.get_order(order_id)
        if not order:
            raise OrderNotFoundError(order_id)

        if order.status != OrderStatus.QUEUED.value:
            raise InvalidStateTransitionError(
                current_status=order.status,
                target_status=OrderStatus.PROCESSING.value,
            )

        try:
            updated_order = self.db_repo.update_order_status_accept(order_id)
        except OrderStateConflictError:
            latest = self.db_repo.get_order(order_id)
            current = latest.status if latest else "UNKNOWN"
            raise InvalidStateTransitionError(
                current_status=current,
                target_status=OrderStatus.PROCESSING.value,
            )

        # Get position in active queue
        active_items = self.db_repo.get_active_queue_items()
        pos = 1
        for idx, it in enumerate(active_items):
            if it.get("order_id") == order_id:
                pos = idx + 1
                break

        return self._build_staff_response(updated_order, queue_position=pos)

    def reject_order(self, order_id: str, rejection_reason: str | None) -> StaffOrderResponse:
        """
        Reject an incoming order with mandatory non-empty reason:
        Transition: QUEUED -> REJECTED
        Removes order from active queue (PK: QUEUE#ACTIVE).
        """
        if not rejection_reason or not rejection_reason.strip():
            raise RejectionReasonRequiredError()

        clean_reason = rejection_reason.strip()
        order = self.db_repo.get_order(order_id)
        if not order:
            raise OrderNotFoundError(order_id)

        if order.status != OrderStatus.QUEUED.value:
            raise InvalidStateTransitionError(
                current_status=order.status,
                target_status=OrderStatus.REJECTED.value,
            )

        try:
            updated_order = self.db_repo.update_order_status_reject(order_id, clean_reason)
        except OrderStateConflictError:
            latest = self.db_repo.get_order(order_id)
            current = latest.status if latest else "UNKNOWN"
            raise InvalidStateTransitionError(
                current_status=current,
                target_status=OrderStatus.REJECTED.value,
            )

        return self._build_staff_response(updated_order, queue_position=0)

    def mark_order_ready(self, order_id: str) -> StaffOrderResponse:
        """
        Mark an order as ready for pickup:
        Transition: PROCESSING -> READY
        Removes order from active operational queue so subsequent jobs shift forward.
        """
        order = self.db_repo.get_order(order_id)
        if not order:
            raise OrderNotFoundError(order_id)

        if order.status != OrderStatus.PROCESSING.value:
            raise InvalidStateTransitionError(
                current_status=order.status,
                target_status=OrderStatus.READY.value,
            )

        try:
            updated_order = self.db_repo.update_order_status_ready(order_id)
        except OrderStateConflictError:
            latest = self.db_repo.get_order(order_id)
            current = latest.status if latest else "UNKNOWN"
            raise InvalidStateTransitionError(
                current_status=current,
                target_status=OrderStatus.READY.value,
            )

        return self._build_staff_response(updated_order, queue_position=0)

    def complete_order(self, order_id: str) -> StaffOrderResponse:
        """
        Complete an order after pickup:
        Transition: READY -> COMPLETED
        Final terminal state for the order lifecycle.
        """
        order = self.db_repo.get_order(order_id)
        if not order:
            raise OrderNotFoundError(order_id)

        if order.status != OrderStatus.READY.value:
            raise InvalidStateTransitionError(
                current_status=order.status,
                target_status=OrderStatus.COMPLETED.value,
            )

        try:
            updated_order = self.db_repo.update_order_status_complete(order_id)
        except OrderStateConflictError:
            latest = self.db_repo.get_order(order_id)
            current = latest.status if latest else "UNKNOWN"
            raise InvalidStateTransitionError(
                current_status=current,
                target_status=OrderStatus.COMPLETED.value,
            )

        return self._build_staff_response(updated_order, queue_position=0)
