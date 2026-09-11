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
