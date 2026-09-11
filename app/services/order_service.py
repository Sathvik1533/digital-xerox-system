import uuid
from datetime import datetime, timezone
from app.models.order import Order, OrderStatus
from app.repositories.dynamodb_repo import DynamoDBRepository
from app.schemas.order import CreateOrderRequest
from app.services.document_service import DocumentNotFoundError
from app.services.pricing_service import PricingService, PricingValidationError


class OrderValidationError(Exception):
    """Raised when order input validation fails."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class OrderNotFoundError(Exception):
    """Raised when the requested order is not found."""

    def __init__(self, order_id: str):
        self.code = "ORDER_NOT_FOUND"
        self.message = f"Order '{order_id}' not found."
        super().__init__(self.message)


class OrderService:
    def __init__(
        self,
        db_repo: DynamoDBRepository | None = None,
        pricing_service: PricingService | None = None,
    ):
        self.db_repo = db_repo or DynamoDBRepository()
        self.pricing_service = pricing_service or PricingService()

    def create_order(self, request: CreateOrderRequest) -> Order:
        """
        Validate document reference and print options, calculate pricing,
        and create order in DynamoDB according to DATA-001.
        """
        # 1. Validate document reference
        doc = self.db_repo.get_document(request.document_id)
        if not doc:
            raise DocumentNotFoundError(request.document_id)

        # 2. Validate print configuration
        if request.copies < 1:
            raise OrderValidationError("INVALID_COPIES", "copies must be at least 1.")
        if request.page_count < 1:
            raise OrderValidationError("INVALID_PAGE_COUNT", "page_count must be at least 1.")

        try:
            print_config, pricing = self.pricing_service.calculate_pricing(
                page_count=request.page_count,
                color_mode=request.color_mode,
                paper_size=request.paper_size,
                copies=request.copies,
                double_sided=request.double_sided,
                sidedness=request.sidedness,
            )
        except PricingValidationError as e:
            raise OrderValidationError(e.code, e.message)

        # 3. Create Order entity according to DATA-001
        order_id = f"ORD-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.now(timezone.utc)
        student_id = request.student_id if request.student_id != "anonymous" else doc.student_id

        order = Order(
            order_id=order_id,
            document_id=doc.document_id,
            student_id=student_id,
            filename=doc.filename,
            document_key=doc.s3_key,
            document_name=doc.filename,
            document_content_type=doc.content_type,
            document_size=doc.size_bytes,
            print_config=print_config,
            pricing=pricing,
            status=OrderStatus.PENDING_PAYMENT.value,
            payment_status="PENDING",
            scheduled_time=request.scheduled_time,
            created_at=now,
            updated_at=now,
        )

        # 4. Persist in DynamoDB (PK: ORDER#{order_id}, SK: ORDER#{order_id})
        self.db_repo.save_order(order)

        return order

    def get_order(self, order_id: str) -> Order:
        """Retrieve order from DynamoDB by order_id."""
        order = self.db_repo.get_order(order_id)
        if not order:
            raise OrderNotFoundError(order_id)
        return order
