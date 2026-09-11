"""
Tests for Vertical Slice 3: Simulated Payment.
Tests cover:
- Deterministic payment simulation SUCCESS path
- Deterministic payment simulation FAILURE path
- Retry payment after failure
- Duplicate payment rejection on already paid orders (ORDER_ALREADY_PAID)
- 404 for nonexistent order simulation and query
- 404 for order with no payments yet (PAYMENT_NOT_FOUND)
- Invalid payment outcome handling (INVALID_PAYMENT_OUTCOME)
- Authoritative order pricing extraction (no client payment spoofing)
- DynamoDB single-table persistence (PK/SK, aliases)
"""
import io
import pytest
from fastapi.testclient import TestClient
from boto3.dynamodb.conditions import Key


def _upload_test_document(client: TestClient, filename: str = "payment_spec.pdf") -> str:
    """Helper to upload a test document and return its document_id."""
    files = {
        "file": (filename, io.BytesIO(b"%PDF-1.4 Mock binary test document"), "application/pdf")
    }
    response = client.post("/documents/", files=files, data={"student_id": "STU-PAY-001"})
    assert response.status_code == 201
    return response.json()["document_id"]


def _create_test_order(
    client: TestClient,
    doc_id: str,
    page_count: int = 10,
    copies: int = 1,
    color_mode: str = "bw",
    paper_size: str = "A4",
    double_sided: bool = False,
) -> dict:
    """Helper to create an order in PENDING_PAYMENT status."""
    payload = {
        "document_id": doc_id,
        "student_id": "STU-PAY-001",
        "page_count": page_count,
        "color_mode": color_mode,
        "paper_size": paper_size,
        "copies": copies,
        "double_sided": double_sided,
    }
    res = client.post("/orders", json=payload)
    assert res.status_code == 201
    return res.json()


def test_simulate_payment_success_path(client: TestClient, aws_env):
    """
    Test deterministic payment simulation SUCCESS path:
    - Order status transitions from PENDING_PAYMENT to PAID
    - Order payment_status transitions to SUCCESS
    - Payment record is created and retrievable via GET /orders/{order_id}/payment
    """
    doc_id = _upload_test_document(client)
    order = _create_test_order(client, doc_id, page_count=10, copies=2)
    order_id = order["order_id"]

    assert order["status"] == "PENDING_PAYMENT"
    assert order["payment_status"] == "PENDING"
    assert order["pricing"]["total_price_paise"] == 2000
    assert order["pricing"]["total_price_rupees"] == 20.0

    # Simulate payment SUCCESS
    res = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "SUCCESS"})
    assert res.status_code == 200
    payment_data = res.json()

    assert payment_data["order_id"] == order_id
    assert payment_data["payment_id"].startswith("PAY-")
    assert payment_data["payment_reference"].startswith("SIMPAY-")
    assert payment_data["payment_reference_id"] == payment_data["payment_reference"]
    assert payment_data["amount_paise"] == 2000
    assert payment_data["amount_rupees"] == 20.0
    assert payment_data["currency"] == "INR"
    assert payment_data["status"] == "SUCCESS"
    assert payment_data["outcome"] == "SUCCESS"
    assert payment_data["failure_reason"] is None
    assert payment_data["order_status"] == "PAID"
    assert "created_at" in payment_data
    assert "updated_at" in payment_data

    # Verify Order state via GET /orders/{order_id}
    order_res = client.get(f"/orders/{order_id}")
    assert order_res.status_code == 200
    updated_order = order_res.json()
    assert updated_order["status"] == "PAID"
    assert updated_order["payment_status"] == "SUCCESS"
    assert updated_order["payment_id"] == payment_data["payment_id"]

    # Verify Payment retrieval via GET /orders/{order_id}/payment
    get_pay_res = client.get(f"/orders/{order_id}/payment")
    assert get_pay_res.status_code == 200
    fetched_pay = get_pay_res.json()
    assert fetched_pay["payment_id"] == payment_data["payment_id"]
    assert fetched_pay["status"] == "SUCCESS"
    assert fetched_pay["amount_paise"] == 2000


def test_simulate_payment_failure_path(client: TestClient, aws_env):
    """
    Test deterministic payment simulation FAILURE path:
    - Order status transitions from PENDING_PAYMENT to PAYMENT_FAILED
    - Order payment_status transitions to FAILED
    - Failure reason is captured
    """
    doc_id = _upload_test_document(client)
    order = _create_test_order(client, doc_id, page_count=5, copies=1)
    order_id = order["order_id"]

    # Simulate payment FAILURE
    res = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "FAILURE"})
    assert res.status_code == 200
    payment_data = res.json()

    assert payment_data["order_id"] == order_id
    assert payment_data["status"] == "FAILED"
    assert payment_data["outcome"] == "FAILURE"
    assert payment_data["failure_reason"] is not None
    assert payment_data["order_status"] == "PAYMENT_FAILED"

    # Verify Order state in DynamoDB
    order_res = client.get(f"/orders/{order_id}")
    assert order_res.status_code == 200
    updated_order = order_res.json()
    assert updated_order["status"] == "PAYMENT_FAILED"
    assert updated_order["payment_status"] == "FAILED"
    assert updated_order["payment_id"] == payment_data["payment_id"]


def test_simulate_payment_retry_after_failure(client: TestClient, aws_env):
    """
    Test student retry flow:
    - Payment fails on first attempt (order status PAYMENT_FAILED)
    - Student retries payment with SUCCESS
    - Order transitions to PAID and payment_status to SUCCESS
    """
    doc_id = _upload_test_document(client)
    order = _create_test_order(client, doc_id, page_count=8, copies=1)
    order_id = order["order_id"]

    # 1. First attempt: FAILURE
    res1 = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "FAILURE"})
    assert res1.status_code == 200
    pay1 = res1.json()
    assert pay1["status"] == "FAILED"

    # Verify intermediate state
    order_res1 = client.get(f"/orders/{order_id}")
    assert order_res1.json()["status"] == "PAYMENT_FAILED"

    # 2. Second attempt: SUCCESS (retry)
    res2 = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "SUCCESS"})
    assert res2.status_code == 200
    pay2 = res2.json()
    assert pay2["status"] == "SUCCESS"
    assert pay2["order_status"] == "PAID"
    assert pay2["payment_id"] != pay1["payment_id"]

    # Verify final order state
    order_res2 = client.get(f"/orders/{order_id}")
    final_order = order_res2.json()
    assert final_order["status"] == "PAID"
    assert final_order["payment_status"] == "SUCCESS"
    assert final_order["payment_id"] == pay2["payment_id"]

    # Verify latest payment query
    get_pay_res = client.get(f"/orders/{order_id}/payment")
    assert get_pay_res.status_code == 200
    latest_pay = get_pay_res.json()
    assert latest_pay["payment_id"] == pay2["payment_id"]
    assert latest_pay["status"] == "SUCCESS"


def test_duplicate_payment_rejection_on_paid_order(client: TestClient, aws_env):
    """
    Test duplicate payment prevention:
    - When order is already PAID, subsequent payment attempts are rejected with 400 Bad Request.
    """
    doc_id = _upload_test_document(client)
    order = _create_test_order(client, doc_id, page_count=4, copies=1)
    order_id = order["order_id"]

    # Pay successfully
    res1 = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "SUCCESS"})
    assert res1.status_code == 200

    # Attempt to pay again with SUCCESS
    res2 = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "SUCCESS"})
    assert res2.status_code == 400
    err2 = res2.json()
    assert err2["detail"]["error"]["code"] == "ORDER_ALREADY_PAID"

    # Attempt to pay again with FAILURE
    res3 = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "FAILURE"})
    assert res3.status_code == 400
    err3 = res3.json()
    assert err3["detail"]["error"]["code"] == "ORDER_ALREADY_PAID"


def test_simulate_payment_nonexistent_order_404(client: TestClient, aws_env):
    """Test 404 response when attempting payment on non-existent order."""
    res = client.post("/orders/ORD-NONEXISTENT/payment/simulate", json={"outcome": "SUCCESS"})
    assert res.status_code == 404
    data = res.json()
    assert data["detail"]["error"]["code"] == "ORDER_NOT_FOUND"


def test_get_payment_nonexistent_order_404(client: TestClient, aws_env):
    """Test 404 response when fetching payment for non-existent order."""
    res = client.get("/orders/ORD-NONEXISTENT/payment")
    assert res.status_code == 404
    data = res.json()
    assert data["detail"]["error"]["code"] == "ORDER_NOT_FOUND"


def test_get_payment_unpaid_order_404(client: TestClient, aws_env):
    """Test 404 response when fetching payment for an order with no payment records."""
    doc_id = _upload_test_document(client)
    order = _create_test_order(client, doc_id, page_count=5)
    order_id = order["order_id"]

    res = client.get(f"/orders/{order_id}/payment")
    assert res.status_code == 404
    data = res.json()
    assert data["detail"]["error"]["code"] == "PAYMENT_NOT_FOUND"


def test_simulate_payment_invalid_outcome(client: TestClient, aws_env):
    """Test rejection when invalid outcome string is supplied."""
    doc_id = _upload_test_document(client)
    order = _create_test_order(client, doc_id, page_count=5)
    order_id = order["order_id"]

    res = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "INVALID_OUTCOME"})
    assert res.status_code == 400
    data = res.json()
    assert data["detail"]["error"]["code"] == "INVALID_PAYMENT_OUTCOME"


def test_simulate_payment_default_payload(client: TestClient, aws_env):
    """Test payment simulation with default (omitted/empty) payload defaults to SUCCESS."""
    doc_id = _upload_test_document(client)
    order = _create_test_order(client, doc_id, page_count=5)
    order_id = order["order_id"]

    res = client.post(f"/orders/{order_id}/payment/simulate", json={})
    assert res.status_code == 200
    data = res.json()
    assert data["outcome"] == "SUCCESS"
    assert data["status"] == "SUCCESS"
    assert data["order_status"] == "PAID"


def test_payment_authoritative_pricing_calculation(client: TestClient, aws_env):
    """
    Test that backend recalculates/derives amount strictly from authoritative order pricing:
    Client cannot inject or spoof payment amount.
    """
    doc_id = _upload_test_document(client)
    # 20 pages, Color (5.00/pg), A3 (2.0x factor) = 20 * 500 * 2.0 = 20000 paise per copy. 2 copies = 40000 paise (Rs 400.00)
    order = _create_test_order(
        client,
        doc_id,
        page_count=20,
        copies=2,
        color_mode="color",
        paper_size="A3",
        double_sided=False,
    )
    order_id = order["order_id"]
    assert order["pricing"]["total_price_paise"] == 40000
    assert order["pricing"]["total_price_rupees"] == 400.0

    # Attempt to simulate payment with spoofed amount in payload (ignored by backend)
    res = client.post(
        f"/orders/{order_id}/payment/simulate",
        json={"outcome": "SUCCESS", "amount_paise": 100, "amount_rupees": 1.0},
    )
    assert res.status_code == 200
    data = res.json()
    # Backend authoritatively used 40000 paise / Rs 400.00
    assert data["amount_paise"] == 40000
    assert data["amount_rupees"] == 400.0
    assert data["currency"] == "INR"


def test_dynamodb_persistence_single_table_verification(client: TestClient, aws_env):
    """
    Directly verify DynamoDB single-table schema (DATA-001):
    - Primary record: PK=ORDER#{order_id}, SK=PAYMENT#{payment_id}
    - Alias record: PK=ORDER#{order_id}, SK=PAYMENT#{order_id}
    - Direct lookup: PK=PAYMENT#{payment_id}, SK=PAYMENT#{payment_id}
    """
    doc_id = _upload_test_document(client)
    order = _create_test_order(client, doc_id, page_count=12, copies=1)
    order_id = order["order_id"]

    res = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "SUCCESS"})
    assert res.status_code == 200
    pay_data = res.json()
    payment_id = pay_data["payment_id"]

    table = aws_env["table"]

    # 1. Check primary record
    primary_res = table.get_item(
        Key={
            "PK": f"ORDER#{order_id}",
            "SK": f"PAYMENT#{payment_id}",
        }
    )
    assert "Item" in primary_res
    p_item = primary_res["Item"]
    assert p_item["payment_id"] == payment_id
    assert p_item["order_id"] == order_id
    assert p_item["status"] == "SUCCESS"
    assert p_item["outcome"] == "SUCCESS"
    assert p_item["amount_paise"] == 1200
    assert p_item["currency"] == "INR"

    # 2. Check alias record for order payment
    alias_res = table.get_item(
        Key={
            "PK": f"ORDER#{order_id}",
            "SK": f"PAYMENT#{order_id}",
        }
    )
    assert "Item" in alias_res
    assert alias_res["Item"]["payment_id"] == payment_id

    # 3. Check alias record for direct payment ID lookup
    pay_direct_res = table.get_item(
        Key={
            "PK": f"PAYMENT#{payment_id}",
            "SK": f"PAYMENT#{payment_id}",
        }
    )
    assert "Item" in pay_direct_res
    assert pay_direct_res["Item"]["order_id"] == order_id


def test_simulate_payment_non_payable_order_status(client: TestClient, aws_env):
    """
    Test that orders in non-payable terminal states (e.g. REJECTED, COMPLETED)
    reject payment simulation with ORDER_NOT_PAYABLE.
    """
    doc_id = _upload_test_document(client)
    order = _create_test_order(client, doc_id, page_count=5)
    order_id = order["order_id"]

    # Manually update order in DynamoDB to REJECTED
    table = aws_env["table"]
    table.update_item(
        Key={"PK": f"ORDER#{order_id}", "SK": f"ORDER#{order_id}"},
        UpdateExpression="SET #st = :st",
        ExpressionAttributeNames={"#st": "status"},
        ExpressionAttributeValues={":st": "REJECTED"},
    )

    res = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "SUCCESS"})
    assert res.status_code == 400
    data = res.json()
    assert data["detail"]["error"]["code"] == "ORDER_NOT_PAYABLE"


def test_student_ui_serves_step3_elements(client: TestClient):
    """Test that student UI HTML contains Step 3 Simulated Payment elements."""
    res = client.get("/")
    assert res.status_code == 200
    assert "Step 3: Simulated Payment" in res.text
    assert "simulatePaymentBtn" in res.text
    assert "paymentOutcome" in res.text
    assert "queryPaymentOrderId" in res.text
    assert "queryPaymentBtn" in res.text


def test_get_payment_returns_order_status(client: TestClient, aws_env):
    """Test that GET /orders/{order_id}/payment returns authoritative order_status."""
    doc_id = _upload_test_document(client)
    order = _create_test_order(client, doc_id, page_count=3, copies=1)
    order_id = order["order_id"]

    # Pay order
    pay_res = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "SUCCESS"})
    assert pay_res.status_code == 200

    # Query payment
    get_res = client.get(f"/orders/{order_id}/payment")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["order_status"] == "PAID"
    assert data["status"] == "SUCCESS"


def test_simulate_payment_null_outcome_defaults_to_success(client: TestClient, aws_env):
    """Test that payload with outcome=None safely defaults to SUCCESS instead of raising 422."""
    doc_id = _upload_test_document(client)
    order = _create_test_order(client, doc_id, page_count=3)
    order_id = order["order_id"]

    res = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": None})
    assert res.status_code == 200
    data = res.json()
    assert data["outcome"] == "SUCCESS"
    assert data["status"] == "SUCCESS"
    assert data["order_status"] == "PAID"


def test_simulate_payment_case_insensitive_outcome(client: TestClient, aws_env):
    """Test that outcome string is normalized case-insensitively ('success', 'failure')."""
    doc_id = _upload_test_document(client)
    order1 = _create_test_order(client, doc_id, page_count=2)
    res1 = client.post(f"/orders/{order1['order_id']}/payment/simulate", json={"outcome": "  success  "})
    assert res1.status_code == 200
    assert res1.json()["outcome"] == "SUCCESS"

    order2 = _create_test_order(client, doc_id, page_count=2)
    res2 = client.post(f"/orders/{order2['order_id']}/payment/simulate", json={"outcome": "failure"})
    assert res2.status_code == 200
    assert res2.json()["outcome"] == "FAILURE"
    assert res2.json()["order_status"] == "PAYMENT_FAILED"


def test_simulate_payment_race_condition_protection(client: TestClient, aws_env):
    """
    Test concurrency / race condition protection:
    If an order has transitioned to PAID, subsequent payment state update attempts
    are rejected atomically at the DynamoDB level and cannot overwrite PAID with PAYMENT_FAILED.
    """
    from app.repositories.dynamodb_repo import DynamoDBRepository, OrderStateConflictError

    doc_id = _upload_test_document(client)
    order = _create_test_order(client, doc_id, page_count=5)
    order_id = order["order_id"]

    # First request marks it PAID
    res = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "SUCCESS"})
    assert res.status_code == 200

    repo = DynamoDBRepository()
    # Attempt concurrent update trying to mark it PAYMENT_FAILED
    with pytest.raises(OrderStateConflictError):
        repo.update_order_payment_state(
            order_id=order_id,
            payment_status="FAILED",
            order_status="PAYMENT_FAILED",
            payment_id="PAY-CONCURRENT-FAIL",
        )

    # Order must remain PAID in DynamoDB
    persisted_order = repo.get_order(order_id)
    assert persisted_order.status == "PAID"
    assert persisted_order.payment_status == "SUCCESS"


def test_update_order_payment_state_nonexistent_order_no_ghost_item(aws_env):
    """
    Test that calling update_order_payment_state on non-existent order raises OrderStateConflictError
    and does NOT create a phantom corrupted item in DynamoDB.
    """
    from app.repositories.dynamodb_repo import DynamoDBRepository, OrderStateConflictError

    repo = DynamoDBRepository()
    with pytest.raises(OrderStateConflictError):
        repo.update_order_payment_state(
            order_id="ORD-NONEXISTENT-PHANTOM",
            payment_status="SUCCESS",
            order_status="PAID",
            payment_id="PAY-PHANTOM",
        )

    # Verify no phantom item was written
    table = aws_env["table"]
    item = table.get_item(Key={"PK": "ORDER#ORD-NONEXISTENT-PHANTOM", "SK": "ORDER#ORD-NONEXISTENT-PHANTOM"}).get("Item")
    assert item is None

