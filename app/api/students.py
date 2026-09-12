from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.history import StudentOrderHistoryItem
from app.services.history_service import HistoryService, StudentIdRequiredError

router = APIRouter()


def get_history_service() -> HistoryService:
    return HistoryService()


@router.get(
    "/{student_id}/orders",
    response_model=list[StudentOrderHistoryItem],
    status_code=status.HTTP_200_OK,
    summary="Get complete order history and tracking for a student",
)
@router.get(
    "/{student_id}/orders/",
    response_model=list[StudentOrderHistoryItem],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_student_orders(
    student_id: str,
    service: HistoryService = Depends(get_history_service),
):
    """
    Vertical Slice 6: Complete Student Tracking + History.
    - Returns chronologically descending order list for the student.
    - Each item includes payment details, timeline events, print config, price breakdown, and fresh presigned S3 document URL.
    - Returns [] when student has no orders.
    - Strictly isolated to the requested student's data.
    """
    try:
        return service.get_student_order_history(student_id)
    except StudentIdRequiredError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "HISTORY_QUERY_FAILED", "message": str(e)}},
        )
