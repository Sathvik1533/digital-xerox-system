from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.order import CreateOrderRequest, OrderResponse
from app.schemas.staff import RejectOrderRequest
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


def _staff_to_order_response(res) -> OrderResponse:
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
        payment_status=res.payment_status or "SUCCESS",
        token_number=res.token_number,
        rejection_reason=res.rejection_reason,
        created_at=res.created_at,
        updated_at=res.updated_at,
    )


@router.post(
    "/{order_id}/process",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Accept and start processing an order (QUEUED -> PROCESSING)",
)
@router.post(
    "/{order_id}/process/",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def process_order(
    order_id: str,
):
    """Transition order to PROCESSING status (alias for staff accept)."""
    from app.services.staff_service import InvalidStateTransitionError, StaffService
    service = StaffService()
    try:
        res = service.accept_order(order_id)
        return _staff_to_order_response(res)
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


@router.post(
    "/{order_id}/accept",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Accept and start processing an order (QUEUED -> PROCESSING)",
)
@router.post(
    "/{order_id}/accept/",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def accept_order_alias(
    order_id: str,
):
    """Transition order from QUEUED to PROCESSING (alias under /orders)."""
    from app.services.staff_service import InvalidStateTransitionError, StaffService
    service = StaffService()
    try:
        res = service.accept_order(order_id)
        return _staff_to_order_response(res)
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
            detail={"error": {"code": "ORDER_ACCEPT_FAILED", "message": str(e)}},
        )


@router.post(
    "/{order_id}/reject",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject an order with mandatory reason (QUEUED -> REJECTED)",
)
@router.post(
    "/{order_id}/reject/",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def reject_order_alias(
    order_id: str,
    request: RejectOrderRequest | None = None,
):
    """Transition order from QUEUED to REJECTED (alias under /orders)."""
    from app.schemas.staff import RejectOrderRequest as ROR
    from app.services.staff_service import (
        InvalidStateTransitionError,
        RejectionReasonRequiredError,
        StaffService,
    )
    service = StaffService()
    reason = request.rejection_reason if request else None
    try:
        res = service.reject_order(order_id, reason)
        return _staff_to_order_response(res)
    except OrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except RejectionReasonRequiredError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
            detail={"error": {"code": "ORDER_REJECT_FAILED", "message": str(e)}},
        )


@router.post(
    "/{order_id}/ready",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark order ready for pickup (PROCESSING -> READY)",
)
@router.post(
    "/{order_id}/ready/",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def ready_order_alias(
    order_id: str,
):
    """Transition order from PROCESSING to READY (alias under /orders)."""
    from app.services.staff_service import InvalidStateTransitionError, StaffService
    service = StaffService()
    try:
        res = service.mark_order_ready(order_id)
        return _staff_to_order_response(res)
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
            detail={"error": {"code": "ORDER_READY_FAILED", "message": str(e)}},
        )


@router.post(
    "/{order_id}/complete",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete order after pickup (READY -> COMPLETED)",
)
@router.post(
    "/{order_id}/complete/",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def complete_order_alias(
    order_id: str,
):
    """Transition order from READY to COMPLETED (alias under /orders)."""
    from app.services.staff_service import InvalidStateTransitionError, StaffService
    service = StaffService()
    try:
        res = service.complete_order(order_id)
        return _staff_to_order_response(res)
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
            detail={"error": {"code": "ORDER_COMPLETE_FAILED", "message": str(e)}},
        )

