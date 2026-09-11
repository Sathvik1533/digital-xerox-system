import pytest
from fastapi.testclient import TestClient
from app.services.pricing_service import PricingService, PricingValidationError


def test_pricing_bw_single_sided():
    """Test B&W single-sided A4 print pricing."""
    service = PricingService()
    config, breakdown = service.calculate_pricing(
        page_count=10,
        color_mode="bw",
        paper_size="A4",
        copies=1,
        double_sided=False,
    )
    assert config.page_count == 10
    assert config.color_mode == "bw"
    assert config.paper_size == "A4"
    assert breakdown.sheets_per_copy == 10
    assert breakdown.total_sheets == 10
    assert breakdown.total_pages_printed == 10
    assert breakdown.base_rate_per_page_paise == 100
    assert breakdown.paper_multiplier == 1.0
    assert breakdown.unit_price_paise == 1000
    assert breakdown.total_price_paise == 1000
    assert breakdown.total_price_rupees == 10.0


def test_pricing_color_single_sided():
    """Test Color single-sided A4 print pricing."""
    service = PricingService()
    config, breakdown = service.calculate_pricing(
        page_count=5,
        color_mode="color",
        paper_size="A4",
        copies=1,
        double_sided=False,
    )
    assert breakdown.base_rate_per_page_paise == 500
    assert breakdown.unit_price_paise == 2500
    assert breakdown.total_price_paise == 2500
    assert breakdown.total_price_rupees == 25.0


def test_pricing_a3_multiplier():
    """Test A3 paper size pricing with 2.0x multiplier."""
    service = PricingService()
    config, breakdown = service.calculate_pricing(
        page_count=4,
        color_mode="bw",
        paper_size="A3",
        copies=1,
        double_sided=False,
    )
    assert breakdown.paper_multiplier == 2.0
    assert breakdown.unit_price_paise == 4 * 100 * 2  # 800 paise
    assert breakdown.total_price_rupees == 8.0


def test_pricing_multiple_copies():
    """Test multiple copies calculation."""
    service = PricingService()
    config, breakdown = service.calculate_pricing(
        page_count=10,
        color_mode="bw",
        paper_size="A4",
        copies=3,
        double_sided=False,
    )
    assert breakdown.unit_price_paise == 1000
    assert breakdown.total_sheets == 30
    assert breakdown.total_pages_printed == 30
    assert breakdown.total_price_paise == 3000
    assert breakdown.total_price_rupees == 30.0


def test_pricing_double_sided_discount():
    """Test double-sided printing gives 20% discount on 2-sided sheets."""
    service = PricingService()
    # 10 pages B&W: 5 sheets. 5 * (2 * 100 * 0.8) = 5 * 160 = 800 paise
    config, breakdown = service.calculate_pricing(
        page_count=10,
        color_mode="bw",
        paper_size="A4",
        copies=1,
        double_sided=True,
    )
    assert breakdown.sheets_per_copy == 5
    assert breakdown.unit_price_paise == 800
    assert breakdown.total_price_rupees == 8.0

    # 11 pages B&W (odd): 5 double sheets (800) + 1 single sheet (100) = 900 paise
    _, odd_breakdown = service.calculate_pricing(
        page_count=11,
        color_mode="bw",
        paper_size="A4",
        copies=1,
        double_sided=True,
    )
    assert odd_breakdown.sheets_per_copy == 6
    assert odd_breakdown.unit_price_paise == 900
    assert odd_breakdown.total_price_rupees == 9.0


def test_pricing_validation_errors():
    """Test validation errors for invalid pricing inputs."""
    service = PricingService()

    with pytest.raises(PricingValidationError) as exc:
        service.calculate_pricing(page_count=0)
    assert exc.value.code == "INVALID_PAGE_COUNT"

    with pytest.raises(PricingValidationError) as exc:
        service.calculate_pricing(page_count=5, copies=0)
    assert exc.value.code == "INVALID_COPIES"

    with pytest.raises(PricingValidationError) as exc:
        service.calculate_pricing(page_count=5, color_mode="metallic")
    assert exc.value.code == "UNSUPPORTED_COLOR_MODE"

    with pytest.raises(PricingValidationError) as exc:
        service.calculate_pricing(page_count=5, paper_size="poster")
    assert exc.value.code == "UNSUPPORTED_PAPER_SIZE"


def test_api_quote_success(client: TestClient):
    """Test POST /pricing/quote returns 200 with breakdown."""
    payload = {
        "page_count": 8,
        "color_mode": "bw",
        "paper_size": "A4",
        "copies": 2,
        "double_sided": False,
    }
    response = client.post("/pricing/quote", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["page_count"] == 8
    assert data["color_mode"] == "bw"
    assert data["paper_size"] == "A4"
    assert data["copies"] == 2
    assert data["total_sheets"] == 16
    assert data["unit_price_paise"] == 800
    assert data["total_price_paise"] == 1600
    assert data["total_price_rupees"] == 16.0
    assert data["currency"] == "INR"


def test_api_quote_invalid_copies(client: TestClient):
    """Test POST /pricing/quote with invalid copies returns 400."""
    payload = {
        "page_count": 5,
        "copies": 0,
    }
    response = client.post("/pricing/quote", json=payload)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error"]["code"] == "INVALID_COPIES"


def test_pricing_case_insensitivity():
    """Test that color_mode and paper_size accept mixed casing and alternate terms."""
    service = PricingService()

    # B&W aliases
    _, b1 = service.calculate_pricing(page_count=2, color_mode="B&W", paper_size="a4")
    assert b1.base_rate_per_page_paise == 100

    _, b2 = service.calculate_pricing(page_count=2, color_mode="Black_And_White", paper_size="A4")
    assert b2.base_rate_per_page_paise == 100

    # Color alias
    _, b3 = service.calculate_pricing(page_count=2, color_mode="COLOUR", paper_size="a3")
    assert b3.base_rate_per_page_paise == 500
    assert b3.paper_multiplier == 2.0


def test_pricing_single_page_double_sided():
    """Test 1 page with double_sided=True occupies 1 sheet and has no discount."""
    service = PricingService()
    config, breakdown = service.calculate_pricing(
        page_count=1,
        color_mode="bw",
        paper_size="A4",
        copies=1,
        double_sided=True,
    )
    assert breakdown.sheets_per_copy == 1
    assert breakdown.total_sheets == 1
    assert breakdown.unit_price_paise == 100
    assert breakdown.total_price_rupees == 1.0


def test_api_quote_unsupported_color_mode(client: TestClient):
    """Test POST /pricing/quote with unsupported color mode returns 400."""
    response = client.post("/pricing/quote", json={"page_count": 5, "color_mode": "sepia"})
    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "UNSUPPORTED_COLOR_MODE"


def test_api_quote_unsupported_paper_size(client: TestClient):
    """Test POST /pricing/quote with unsupported paper size returns 400."""
    response = client.post("/pricing/quote", json={"page_count": 5, "paper_size": "Tabloid"})
    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "UNSUPPORTED_PAPER_SIZE"
