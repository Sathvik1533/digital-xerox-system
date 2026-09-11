from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.pricing import QuoteRequest, QuoteResponse
from app.services.pricing_service import PricingService, PricingValidationError

router = APIRouter()


def get_pricing_service() -> PricingService:
    return PricingService()


@router.post(
    "/quote",
    response_model=QuoteResponse,
    summary="Get instant pricing quote for print configuration",
)
@router.post(
    "",
    response_model=QuoteResponse,
    include_in_schema=False,
)
@router.post(
    "/",
    response_model=QuoteResponse,
    include_in_schema=False,
)
def get_pricing_quote(
    request: QuoteRequest,
    service: PricingService = Depends(get_pricing_service),
):
    """
    Calculate and return a deterministic pricing quote based on page count,
    color mode, paper size, copies, and double-sided option.
    """
    try:
        config, breakdown = service.calculate_pricing(
            page_count=request.page_count,
            color_mode=request.color_mode,
            paper_size=request.paper_size,
            copies=request.copies,
            double_sided=request.double_sided,
        )
        return QuoteResponse(
            page_count=config.page_count,
            color_mode=config.color_mode,
            paper_size=config.paper_size,
            copies=config.copies,
            double_sided=config.double_sided,
            sheets_per_copy=breakdown.sheets_per_copy,
            total_sheets=breakdown.total_sheets,
            total_pages_printed=breakdown.total_pages_printed,
            base_rate_per_page_paise=breakdown.base_rate_per_page_paise,
            paper_multiplier=breakdown.paper_multiplier,
            unit_price_paise=breakdown.unit_price_paise,
            total_price_paise=breakdown.total_price_paise,
            total_price_rupees=breakdown.total_price_rupees,
            currency=breakdown.currency,
        )
    except PricingValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "PRICING_ERROR", "message": str(e)}},
        )
