from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.payment import PaymentResponse, SimulatePaymentRequest
from app.services.order_service import OrderNotFoundError
from app.services.payment_service import (
    OrderNotPayableError,
    PaymentNotFoundError,
    PaymentService,
    PaymentValidationError,
)

router = APIRouter()


def get_payment_service() -> PaymentService:
    return PaymentService()


@router.post(
    "/{order_id}/payment/simulate",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate payment for an order (deterministic SUCCESS or FAILURE)",
)
@router.post(
    "/{order_id}/payment/simulate/",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def simulate_payment(
    order_id: str,
    request: SimulatePaymentRequest | None = None,
    service: PaymentService = Depends(get_payment_service),
):
    """
    Vertical Slice 3: Simulated Payment Execution.
    Supports deterministic 'SUCCESS' or 'FAILURE'.
    Updates order payment_status and order status in DynamoDB.
    """
    outcome = request.outcome if request else "SUCCESS"
    try:
        payment, updated_order = service.simulate_payment(order_id=order_id, outcome=outcome)
        return PaymentResponse(
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
            order_status=updated_order.status,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )
    except OrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except OrderNotPayableError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except PaymentValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "PAYMENT_SIMULATION_FAILED", "message": str(e)}},
        )


@router.get(
    "/{order_id}/payment",
    response_model=PaymentResponse,
    summary="Get payment details for an order",
)
@router.get(
    "/{order_id}/payment/",
    response_model=PaymentResponse,
    include_in_schema=False,
)
def get_payment(
    order_id: str,
    service: PaymentService = Depends(get_payment_service),
):
    """Retrieve payment details for an order from DynamoDB."""
    try:
        payment = service.get_payment_for_order(order_id)
        return PaymentResponse(
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
            order_status=None,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )
    except OrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except PaymentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "INTERNAL_ERROR", "message": str(e)}},
        )
