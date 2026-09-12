from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.schemas.staff import RejectOrderRequest, StaffOrderResponse
from app.services.order_service import OrderNotFoundError
from app.services.staff_service import (
    InvalidStateTransitionError,
    RejectionReasonRequiredError,
    StaffService,
)

router = APIRouter()


def get_staff_service() -> StaffService:
    return StaffService()


@router.get(
    "/orders",
    response_model=list[StaffOrderResponse],
    status_code=status.HTTP_200_OK,
    summary="List orders for staff operations",
)
@router.get(
    "/orders/",
    response_model=list[StaffOrderResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
@router.get(
    "/queue",
    response_model=list[StaffOrderResponse],
    status_code=status.HTTP_200_OK,
    summary="List active queue orders for staff operations",
)
@router.get(
    "/queue/",
    response_model=list[StaffOrderResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def list_staff_orders(
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Filter orders by status: ACTIVE (default), QUEUED, PROCESSING, READY, COMPLETED, REJECTED, ALL",
    ),
    service: StaffService = Depends(get_staff_service),
):
    """
    Vertical Slice 5: Staff Operations - View active incoming orders.
    Lists active orders (QUEUED, PROCESSING) with document metadata and S3 presigned URL.
    """
    try:
        return service.list_orders(status_filter=status_filter)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "STAFF_QUERY_FAILED", "message": str(e)}},
        )


@router.post(
    "/orders/{order_id}/accept",
    response_model=StaffOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Accept an order and start processing (QUEUED -> PROCESSING)",
)
@router.post(
    "/orders/{order_id}/accept/",
    response_model=StaffOrderResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
@router.post(
    "/orders/{order_id}/process",
    response_model=StaffOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Alias for accept order (QUEUED -> PROCESSING)",
)
@router.post(
    "/orders/{order_id}/process/",
    response_model=StaffOrderResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def accept_order(
    order_id: str,
    service: StaffService = Depends(get_staff_service),
):
    """Transition order from QUEUED to PROCESSING."""
    try:
        return service.accept_order(order_id)
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
            detail={"error": {"code": "STAFF_ACCEPT_FAILED", "message": str(e)}},
        )


@router.post(
    "/orders/{order_id}/reject",
    response_model=StaffOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject an order with mandatory reason (QUEUED -> REJECTED)",
)
@router.post(
    "/orders/{order_id}/reject/",
    response_model=StaffOrderResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def reject_order(
    order_id: str,
    request: RejectOrderRequest,
    service: StaffService = Depends(get_staff_service),
):
    """Transition order from QUEUED to REJECTED with mandatory reason."""
    try:
        return service.reject_order(order_id, request.rejection_reason)
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
            detail={"error": {"code": "STAFF_REJECT_FAILED", "message": str(e)}},
        )


@router.post(
    "/orders/{order_id}/ready",
    response_model=StaffOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark an order ready for pickup (PROCESSING -> READY)",
)
@router.post(
    "/orders/{order_id}/ready/",
    response_model=StaffOrderResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def mark_order_ready(
    order_id: str,
    service: StaffService = Depends(get_staff_service),
):
    """Transition order from PROCESSING to READY (removes from active queue)."""
    try:
        return service.mark_order_ready(order_id)
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
            detail={"error": {"code": "STAFF_READY_FAILED", "message": str(e)}},
        )


@router.post(
    "/orders/{order_id}/complete",
    response_model=StaffOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete an order after student pickup (READY -> COMPLETED)",
)
@router.post(
    "/orders/{order_id}/complete/",
    response_model=StaffOrderResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def complete_order(
    order_id: str,
    service: StaffService = Depends(get_staff_service),
):
    """Transition order from READY to COMPLETED."""
    try:
        return service.complete_order(order_id)
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
            detail={"error": {"code": "STAFF_COMPLETE_FAILED", "message": str(e)}},
        )
