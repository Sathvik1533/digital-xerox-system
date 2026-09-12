from datetime import datetime, timedelta, timezone
from app.core.config import get_settings
from app.models.order import Order, OrderStatus, PaymentStatus
from app.repositories.dynamodb_repo import DynamoDBRepository, OrderStateConflictError
from app.schemas.queue import QueueAdmissionResponse, QueueStatusResponse
from app.services.order_service import OrderNotFoundError


class QueueError(Exception):
    """Base exception for queue operations."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class OrderAlreadyQueuedError(QueueError):
    """Raised when an order is already admitted to the queue."""

    def __init__(self, order_id: str, token_number: str | None = None):
        tok_str = f" with token '{token_number}'" if token_number else ""
        super().__init__(
            code="ORDER_ALREADY_QUEUED",
            message=f"Order '{order_id}' is already queued{tok_str}.",
        )
        self.token_number = token_number


class OrderNotEligibleForQueueError(QueueError):
    """Raised when an order is not in PAID status with successful payment."""

    def __init__(self, order_id: str, status: str, payment_status: str):
        super().__init__(
            code="ORDER_NOT_PAID",
            message=(
                f"Order '{order_id}' is not eligible for queue admission. "
                f"Requires status 'PAID' and payment_status 'SUCCESS' "
                f"(current status: '{status}', payment_status: '{payment_status}')."
            ),
        )


class OrderNotQueuedError(QueueError):
    """Raised when queue status is requested for an order that is not queued."""

    def __init__(self, order_id: str):
        super().__init__(
            code="ORDER_NOT_QUEUED",
            message=f"Order '{order_id}' has not entered the queue yet.",
        )


class QueueService:
    """
    Operational print queue management and deterministic ETA calculation service.
    Vertical Slice 4: Token + Queue + ETA.
    """

    def __init__(self, db_repo: DynamoDBRepository | None = None):
        self.db_repo = db_repo or DynamoDBRepository()
        self.settings = get_settings()

    def calculate_job_duration_seconds(
        self,
        total_pages_printed: int,
        color_mode: str = "bw",
    ) -> int:
        """
        Deterministic print duration calculation for an individual job:
        duration = base_setup_time + (pages * rate_per_page)
        """
        base_setup = self.settings.queue_base_setup_seconds
        rate = (
            self.settings.queue_color_seconds_per_page
            if color_mode.lower() == "color"
            else self.settings.queue_bw_seconds_per_page
        )
        return int(base_setup + (total_pages_printed * rate))

    def _calculate_queue_schedule(
        self,
        active_items: list[dict],
        now: datetime | None = None,
    ) -> list[dict]:
        """
        Compute deterministic start time, completion time, and remaining seconds
        for all active items in the operational queue.
        Jobs run sequentially (FIFO) on the print station.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        scheduled_items = []
        prev_completion = None

        for idx, item in enumerate(active_items):
            pages = int(item.get("total_pages_printed", 1))
            cm = str(item.get("color_mode", "bw"))
            duration = self.calculate_job_duration_seconds(pages, cm)

            entered_str = item.get("queue_entered_at")
            if entered_str:
                try:
                    entered_at = datetime.fromisoformat(str(entered_str).replace("Z", "+00:00"))
                    if entered_at.tzinfo is None:
                        entered_at = entered_at.replace(tzinfo=timezone.utc)
                except Exception:
                    entered_at = now
            else:
                entered_at = now

            if idx == 0:
                # First active job: started at queue_entered_at
                initial_est_finish = entered_at + timedelta(seconds=duration)
                # If first job's initial estimate is in the past, printer completes any moment (max with now)
                completion_at = initial_est_finish if initial_est_finish > now else now
                remaining_seconds = max(0, int((initial_est_finish - now).total_seconds()))
            else:
                # Subsequent jobs start when previous job completes (or now if previous completed in past)
                start_at = prev_completion if prev_completion > now else now
                completion_at = start_at + timedelta(seconds=duration)
                remaining_seconds = max(0, int((completion_at - now).total_seconds()))

            prev_completion = completion_at
            item_copy = dict(item)
            item_copy["computed_completion_at"] = completion_at
            item_copy["computed_remaining_seconds"] = remaining_seconds
            item_copy["computed_wait_minutes"] = round(remaining_seconds / 60.0, 1)
            scheduled_items.append(item_copy)

        return scheduled_items

    def admit_to_queue(self, order_id: str) -> QueueAdmissionResponse:
        """
        Admit a successfully paid order to the operational queue:
        1. Validates order eligibility (must be PAID with payment_status SUCCESS).
        2. Rejects invalid states and duplicate admissions (ORDER_ALREADY_QUEUED).
        3. Concurrency-safe atomic token generation (e.g. X-101, X-102...).
        4. Calculates deterministic ETA and 1-based queue position.
        5. Persists operational queue state and updates order in DynamoDB.
        """
        order = self.db_repo.get_order(order_id)
        if not order:
            raise OrderNotFoundError(order_id)

        # Guard: Check for duplicate admission
        if order.status == OrderStatus.QUEUED.value or order.token_number is not None:
            raise OrderAlreadyQueuedError(order_id, order.token_number)

        # Guard: Only successfully PAID orders can enter the queue
        if (
            order.status != OrderStatus.PAID.value
            or order.payment_status != PaymentStatus.SUCCESS.value
        ):
            raise OrderNotEligibleForQueueError(order_id, order.status, order.payment_status)

        # 1. Fetch active queue items to calculate depth and ETA
        active_items = self.db_repo.get_active_queue_items()
        queue_position = len(active_items) + 1

        # 2. Deterministic ETA engine (base setup + pages printed per active job ahead + this job)
        duration_ahead_seconds = 0
        for item in active_items:
            pages = int(item.get("total_pages_printed", 1))
            cm = str(item.get("color_mode", "bw"))
            duration_ahead_seconds += self.calculate_job_duration_seconds(pages, cm)

        this_job_pages = order.pricing.total_pages_printed
        this_job_cm = order.print_config.color_mode
        this_job_duration = self.calculate_job_duration_seconds(this_job_pages, this_job_cm)

        total_wait_seconds = duration_ahead_seconds + this_job_duration
        now = datetime.now(timezone.utc)
        estimated_completion_at = now + timedelta(seconds=total_wait_seconds)
        estimated_wait_minutes = round(total_wait_seconds / 60.0, 1)

        # 3. Generate sequential, atomic token (e.g. X-101)
        token_number = self.db_repo.generate_next_token(prefix=self.settings.queue_token_prefix)

        # 4. Atomic conditional update of Order and insertion into QUEUE#ACTIVE
        try:
            updated_order = self.db_repo.add_order_to_queue(
                order=order,
                token_number=token_number,
                queue_entered_at=now,
                estimated_completion_at=estimated_completion_at,
            )
        except OrderStateConflictError:
            # Concurrency conflict: rollback token counter so no sequential number is wasted
            self.db_repo.rollback_token_counter(1)
            latest = self.db_repo.get_order(order_id)
            if not latest:
                raise OrderNotFoundError(order_id)
            if latest.status == OrderStatus.QUEUED.value or latest.token_number:
                raise OrderAlreadyQueuedError(order_id, latest.token_number)
            raise OrderNotEligibleForQueueError(order_id, latest.status, latest.payment_status)

        return QueueAdmissionResponse(
            order_id=updated_order.order_id,
            token_number=token_number,
            queue_position=queue_position,
            estimated_completion_at=estimated_completion_at,
            estimated_wait_minutes=estimated_wait_minutes,
            estimated_wait_seconds=total_wait_seconds,
            active_queue_length=queue_position,
            status=updated_order.status,
            queue_entered_at=now,
        )

    def get_order_queue_status(self, order_id: str) -> QueueStatusResponse:
        """
        Retrieve live queue position, deterministic ETA, and active queue length for an order.
        Counts down remaining wait time against stored completion timestamp without drifting into future.
        """
        order = self.db_repo.get_order(order_id)
        if not order:
            raise OrderNotFoundError(order_id)

        # Guard: Must have entered queue
        if (
            order.status
            not in (
                OrderStatus.QUEUED.value,
                OrderStatus.PROCESSING.value,
                OrderStatus.READY.value,
                OrderStatus.COMPLETED.value,
                OrderStatus.REJECTED.value,
            )
            and not order.token_number
        ):
            raise OrderNotQueuedError(order_id)

        active_items = self.db_repo.get_active_queue_items()
        active_queue_length = len(active_items)

        # Find order index in active queue
        order_idx = None
        for idx, item in enumerate(active_items):
            if item.get("order_id") == order_id:
                order_idx = idx
                break

        now = datetime.now(timezone.utc)
        stored_est = order.estimated_completion_at
        if stored_est and stored_est.tzinfo is None:
            stored_est = stored_est.replace(tzinfo=timezone.utc)

        if order_idx is not None:
            queue_position = order_idx + 1

            # Calculate theoretical duration ahead from current active items
            duration_ahead_seconds = 0
            for item in active_items[:order_idx]:
                pages = int(item.get("total_pages_printed", 1))
                cm = str(item.get("color_mode", "bw"))
                duration_ahead_seconds += self.calculate_job_duration_seconds(pages, cm)

            this_pages = order.pricing.total_pages_printed
            this_cm = order.print_config.color_mode
            this_job_duration = self.calculate_job_duration_seconds(this_pages, this_cm)
            max_remaining = duration_ahead_seconds + this_job_duration

            if stored_est:
                # Count down from stored completion without drifting into future
                countdown_remaining = max(0, int((stored_est - now).total_seconds()))
                # If jobs ahead were removed/completed early, cap remaining time
                remaining_seconds = min(countdown_remaining, max_remaining)
                if remaining_seconds < countdown_remaining and countdown_remaining > 0:
                    estimated_completion_at = now + timedelta(seconds=remaining_seconds)
                else:
                    estimated_completion_at = stored_est
            else:
                remaining_seconds = max_remaining
                estimated_completion_at = now + timedelta(seconds=remaining_seconds)

            estimated_wait_minutes = round(remaining_seconds / 60.0, 1)
        else:
            # Order is no longer in active queue (processed, ready, or completed)
            queue_position = 0
            remaining_seconds = 0
            estimated_wait_minutes = 0.0
            estimated_completion_at = stored_est or now

        order_entered = order.queue_entered_at
        if order_entered and order_entered.tzinfo is None:
            order_entered = order_entered.replace(tzinfo=timezone.utc)

        return QueueStatusResponse(
            order_id=order.order_id,
            token_number=order.token_number or "N/A",
            queue_position=queue_position,
            estimated_completion_at=estimated_completion_at,
            estimated_wait_minutes=estimated_wait_minutes,
            estimated_wait_seconds=remaining_seconds,
            active_queue_length=active_queue_length,
            status=order.status,
            queue_entered_at=order_entered or now,
            total_pages_printed=order.pricing.total_pages_printed,
            color_mode=order.print_config.color_mode,
            paper_size=order.print_config.paper_size,
            copies=order.print_config.copies,
            rejection_reason=order.rejection_reason,
        )
