from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.order import CreateOrderRequest, OrderResponse
from app.services.document_service import DocumentNotFoundError
from app.services.order_service import OrderNotFoundError, OrderService, OrderValidationError

router = APIRouter()


def get_order_service() -> OrderService:
    return OrderService()


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new print order",
)
@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_order(
    request: CreateOrderRequest,
    service: OrderService = Depends(get_order_service),
):
    """
    Vertical Slice 2: Student Print Options & Order Creation.
    Flow: Validate print options & document → Calculate price → Persist in DynamoDB → Return order details.
    """
    try:
        order = service.create_order(request)
        return OrderResponse(
            order_id=order.order_id,
            document_id=order.document_id,
            student_id=order.student_id,
            filename=order.filename,
            document_key=order.document_key,
            document_name=order.document_name,
            document_content_type=order.document_content_type,
            document_size=order.document_size,
            print_config=order.print_config,
            pricing=order.pricing,
            status=order.status,
            payment_status=order.payment_status,
            payment_id=order.payment_id,
            scheduled_time=order.scheduled_time,
            token_number=order.token_number,
            rejection_reason=order.rejection_reason,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except OrderValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "ORDER_CREATION_FAILED", "message": str(e)}},
        )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order details by order ID from DynamoDB",
)
def get_order(
    order_id: str,
    service: OrderService = Depends(get_order_service),
):
    """Retrieve order details from DynamoDB by order_id."""
    try:
        order = service.get_order(order_id)
        return OrderResponse(
            order_id=order.order_id,
            document_id=order.document_id,
            student_id=order.student_id,
            filename=order.filename,
            document_key=order.document_key,
            document_name=order.document_name,
            document_content_type=order.document_content_type,
            document_size=order.document_size,
            print_config=order.print_config,
            pricing=order.pricing,
            status=order.status,
            payment_status=order.payment_status,
            payment_id=order.payment_id,
            scheduled_time=order.scheduled_time,
            token_number=order.token_number,
            rejection_reason=order.rejection_reason,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
    except OrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "INTERNAL_ERROR", "message": str(e)}},
        )


@router.post(
    "/{order_id}/process",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Accept and start processing an order (QUEUED -> PROCESSING)",
)
def process_order(
    order_id: str,
):
    """Transition order to PROCESSING status (alias for staff accept)."""
    from app.services.staff_service import InvalidStateTransitionError, StaffService
    service = StaffService()
    try:
        res = service.accept_order(order_id)
        return OrderResponse(
            order_id=res.order_id,
            document_id=res.document_id,
            student_id=res.student_id,
            filename=res.filename,
            document_key=res.document_key,
            document_name=res.filename,
            print_config=res.print_config,
            pricing=res.pricing,
            status=res.status,
            payment_status="SUCCESS",
            token_number=res.token_number,
            rejection_reason=res.rejection_reason,
            created_at=res.created_at,
            updated_at=res.updated_at,
        )
    except OrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "ORDER_PROCESS_FAILED", "message": str(e)}},
        )
