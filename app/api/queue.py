from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.queue import QueueAdmissionResponse, QueueStatusResponse
from app.services.order_service import OrderNotFoundError
from app.services.queue_service import (
    OrderAlreadyQueuedError,
    OrderNotEligibleForQueueError,
    OrderNotQueuedError,
    QueueService,
)

router = APIRouter()


def get_queue_service() -> QueueService:
    return QueueService()


@router.post(
    "/{order_id}/queue",
    response_model=QueueAdmissionResponse,
    status_code=status.HTTP_200_OK,
    summary="Admit paid order to operational queue and generate token",
)
@router.post(
    "/{order_id}/queue/",
    response_model=QueueAdmissionResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def admit_order_to_queue(
    order_id: str,
    service: QueueService = Depends(get_queue_service),
):
    """
    Vertical Slice 4: Queue Admission & Token Generation.
    - Requires order in PAID status with payment_status SUCCESS.
    - Issues atomic sequential token (e.g. X-101, X-102...).
    - Computes 1-based queue position and deterministic ETA.
    - Transitions order status to QUEUED.
    - Idempotently rejects duplicate admissions (ORDER_ALREADY_QUEUED).
    """
    try:
        return service.admit_to_queue(order_id)
    except OrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except OrderAlreadyQueuedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except OrderNotEligibleForQueueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "QUEUE_ADMISSION_FAILED", "message": str(e)}},
        )


@router.get(
    "/{order_id}/queue",
    response_model=QueueStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get live queue status, position, and deterministic ETA for an order",
)
@router.get(
    "/{order_id}/queue/",
    response_model=QueueStatusResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_order_queue_status(
    order_id: str,
    service: QueueService = Depends(get_queue_service),
):
    """
    Vertical Slice 4: Live Queue Status & ETA Inspection.
    - Returns token number, 1-based queue position, deterministic ETA, and active queue length.
    """
    try:
        return service.get_order_queue_status(order_id)
    except OrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except OrderNotQueuedError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "QUEUE_QUERY_FAILED", "message": str(e)}},
        )
