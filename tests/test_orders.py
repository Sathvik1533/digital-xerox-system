import io
import pytest
from fastapi.testclient import TestClient


def _upload_test_document(client: TestClient, filename: str = "project_spec.pdf") -> str:
    """Helper to upload a test document and return its document_id."""
    files = {
        "file": (filename, io.BytesIO(b"%PDF-1.4 Mock binary test document"), "application/pdf")
    }
    response = client.post("/documents/", files=files, data={"student_id": "STU-TEST-001"})
    assert response.status_code == 201
    return response.json()["document_id"]


def test_create_order_success(client: TestClient, aws_env):
    """Test successful order creation and DynamoDB persistence (DATA-001)."""
    doc_id = _upload_test_document(client)

    payload = {
        "document_id": doc_id,
        "student_id": "STU-TEST-001",
        "page_count": 10,
        "color_mode": "bw",
        "paper_size": "A4",
        "copies": 2,
        "double_sided": False,
    }

    response = client.post("/orders", json=payload)
    assert response.status_code == 201
    data = response.json()

    order_id = data["order_id"]
    assert order_id.startswith("ORD-")
    assert data["document_id"] == doc_id
    assert data["student_id"] == "STU-TEST-001"
    assert data["filename"] == "project_spec.pdf"
    assert data["status"] == "PENDING_PAYMENT"

    # Verify print configuration
    print_config = data["print_config"]
    assert print_config["page_count"] == 10
    assert print_config["color_mode"] == "bw"
    assert print_config["paper_size"] == "A4"
    assert print_config["copies"] == 2
    assert print_config["double_sided"] is False

    # Verify pricing breakdown
    pricing = data["pricing"]
    assert pricing["base_rate_per_page_paise"] == 100
    assert pricing["unit_price_paise"] == 1000
    assert pricing["total_price_paise"] == 2000
    assert pricing["total_price_rupees"] == 20.0
    assert pricing["currency"] == "INR"

    # Direct DynamoDB verification (DATA-001: PK: ORDER#{order_id}, SK: ORDER#{order_id})
    table = aws_env["table"]
    ddb_res = table.get_item(Key={"PK": f"ORDER#{order_id}", "SK": f"ORDER#{order_id}"})
    assert "Item" in ddb_res
    item = ddb_res["Item"]
    assert item["order_id"] == order_id
    assert item["document_id"] == doc_id
    assert item["status"] == "PENDING_PAYMENT"
    assert item["student_id"] == "STU-TEST-001"


def test_get_order_by_id_success(client: TestClient):
    """Test retrieving created order by ID via GET /orders/{order_id}."""
    doc_id = _upload_test_document(client, filename="lab_manual.pdf")

    create_res = client.post("/orders", json={
        "document_id": doc_id,
        "student_id": "STU-TEST-002",
        "page_count": 6,
        "color_mode": "color",
        "paper_size": "A4",
        "copies": 1,
        "double_sided": False,
    })
    assert create_res.status_code == 201
    order_id = create_res.json()["order_id"]

    get_res = client.get(f"/orders/{order_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["order_id"] == order_id
    assert data["document_id"] == doc_id
    assert data["pricing"]["unit_price_paise"] == 3000
    assert data["pricing"]["total_price_rupees"] == 30.0


def test_get_order_not_found(client: TestClient):
    """Test retrieving non-existent order ID returns 404 ORDER_NOT_FOUND."""
    response = client.get("/orders/ORD-NONEXISTENT-999")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["error"]["code"] == "ORDER_NOT_FOUND"


def test_create_order_document_not_found(client: TestClient):
    """Test creating order with non-existent document_id returns 404 DOCUMENT_NOT_FOUND."""
    payload = {
        "document_id": "non-existent-doc-uuid",
        "page_count": 5,
        "copies": 1,
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_create_order_invalid_copies(client: TestClient):
    """Test creating order with copies <= 0 returns 400 INVALID_COPIES."""
    doc_id = _upload_test_document(client)
    payload = {
        "document_id": doc_id,
        "page_count": 5,
        "copies": 0,
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error"]["code"] == "INVALID_COPIES"


def test_create_order_invalid_page_count(client: TestClient):
    """Test creating order with page_count <= 0 returns 400 INVALID_PAGE_COUNT."""
    doc_id = _upload_test_document(client)
    payload = {
        "document_id": doc_id,
        "page_count": 0,
        "copies": 1,
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error"]["code"] == "INVALID_PAGE_COUNT"


def test_create_order_unsupported_color_mode(client: TestClient):
    """Test creating order with unsupported color_mode returns 400 UNSUPPORTED_COLOR_MODE."""
    doc_id = _upload_test_document(client)
    payload = {
        "document_id": doc_id,
        "page_count": 5,
        "color_mode": "fluorescent",
        "copies": 1,
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error"]["code"] == "UNSUPPORTED_COLOR_MODE"


def test_create_order_unsupported_paper_size(client: TestClient):
    """Test creating order with unsupported paper_size returns 400 UNSUPPORTED_PAPER_SIZE."""
    doc_id = _upload_test_document(client)
    payload = {
        "document_id": doc_id,
        "page_count": 5,
        "paper_size": "POSTER_MAX",
        "copies": 1,
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error"]["code"] == "UNSUPPORTED_PAPER_SIZE"


def test_create_order_color_double_sided_a3(client: TestClient, aws_env):
    """Test end-to-end order creation with Color, A3 paper, double-sided, and multiple copies."""
    doc_id = _upload_test_document(client, filename="architecture_diagram.pdf")

    # 4 pages color A3 double sided:
    # 2 sheets, each sheet has 2 sides.
    # Base rate color: 500 paise, A3 multiplier: 2.0 -> 1000 paise per page
    # Double-sided discount: 2 * 1000 * 0.8 = 1600 paise per sheet
    # 2 sheets * 1600 = 3200 paise per copy.
    # 3 copies = 9600 paise (₹96.00).
    payload = {
        "document_id": doc_id,
        "student_id": "STU-ARCH-01",
        "page_count": 4,
        "color_mode": "color",
        "paper_size": "A3",
        "copies": 3,
        "double_sided": True,
    }

    response = client.post("/orders", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["pricing"]["unit_price_paise"] == 3200
    assert data["pricing"]["total_price_paise"] == 9600
    assert data["pricing"]["total_price_rupees"] == 96.0

    # Verify order retrieval
    order_id = data["order_id"]
    get_res = client.get(f"/orders/{order_id}")
    assert get_res.status_code == 200
    assert get_res.json()["order_id"] == order_id


def test_order_inherits_student_id_from_document(client: TestClient):
    """Test that student_id is inherited from document when anonymous in order request."""
    files = {
        "file": ("syllabus.pdf", io.BytesIO(b"%PDF syllabus"), "application/pdf")
    }
    upload_res = client.post("/documents/", files=files, data={"student_id": "STU-INHERIT-99"})
    doc_id = upload_res.json()["document_id"]

    order_res = client.post("/orders", json={
        "document_id": doc_id,
        "page_count": 3,
        "copies": 1,
    })
    assert order_res.status_code == 201
    assert order_res.json()["student_id"] == "STU-INHERIT-99"


def test_order_letter_paper_size(client: TestClient):
    """Test order with Letter paper size."""
    doc_id = _upload_test_document(client, filename="letter_doc.pdf")
    res = client.post("/orders", json={
        "document_id": doc_id,
        "page_count": 2,
        "paper_size": "Letter",
        "color_mode": "bw",
        "copies": 1,
    })
    assert res.status_code == 201
    assert res.json()["print_config"]["paper_size"] == "Letter"
    assert res.json()["pricing"]["total_price_rupees"] == 2.0


def test_multiple_orders_same_document(client: TestClient):
    """Test multiple distinct orders can reference the same uploaded document."""
    doc_id = _upload_test_document(client, filename="shared_handout.pdf")

    res1 = client.post("/orders", json={
        "document_id": doc_id,
        "page_count": 5,
        "copies": 1,
        "color_mode": "bw",
    })
    res2 = client.post("/orders", json={
        "document_id": doc_id,
        "page_count": 5,
        "copies": 2,
        "color_mode": "color",
    })

    assert res1.status_code == 201
    assert res2.status_code == 201
    assert res1.json()["order_id"] != res2.json()["order_id"]
    assert res1.json()["pricing"]["total_price_paise"] == 500
    assert res2.json()["pricing"]["total_price_paise"] == 5000
