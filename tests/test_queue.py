"""
Tests for Vertical Slice 4: Token + Queue + ETA.
Tests cover:
- Concurrency-safe atomic token generation (X-101, X-102...)
- Queue admission eligibility guards (only successfully PAID orders)
- Unpaid orders rejected (PENDING_PAYMENT -> 400 ORDER_NOT_PAID)
- Payment failed orders rejected (PAYMENT_FAILED -> 400 ORDER_NOT_PAID)
- Duplicate admission prevention (400 ORDER_ALREADY_QUEUED)
- 404 for nonexistent order queue operations
- 404 for unqueued order query (ORDER_NOT_QUEUED)
- 1-based queue position calculation across multiple active orders
- Deterministic backend ETA engine calculation
- DynamoDB single-table persistence (Order record update and PK: QUEUE#ACTIVE items)
"""
import io
import pytest
from fastapi.testclient import TestClient
from boto3.dynamodb.conditions import Key
from app.repositories.dynamodb_repo import DynamoDBRepository


def _upload_test_document(client: TestClient, filename: str = "queue_test.pdf") -> str:
    """Helper to upload a test document and return its document_id."""
    files = {
        "file": (filename, io.BytesIO(b"%PDF-1.4 Mock binary test document for queue"), "application/pdf")
    }
    response = client.post("/documents/", files=files, data={"student_id": "STU-QUEUE-001"})
    assert response.status_code == 201
    return response.json()["document_id"]


def _create_and_pay_test_order(
    client: TestClient,
    page_count: int = 10,
    copies: int = 1,
    color_mode: str = "bw",
    paper_size: str = "A4",
    double_sided: bool = False,
) -> str:
    """Helper to create an order and successfully pay it, returning order_id."""
    doc_id = _upload_test_document(client)
    payload = {
        "document_id": doc_id,
        "student_id": "STU-QUEUE-001",
        "page_count": page_count,
        "color_mode": color_mode,
        "paper_size": paper_size,
        "copies": copies,
        "double_sided": double_sided,
    }
    order_res = client.post("/orders", json=payload)
    assert order_res.status_code == 201
    order_id = order_res.json()["order_id"]

    pay_res = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "SUCCESS"})
    assert pay_res.status_code == 200
    assert pay_res.json()["status"] == "SUCCESS"
    assert pay_res.json()["order_status"] == "PAID"
    return order_id


def test_token_generation_sequential_and_atomic(aws_env):
    """
    Test that token generation produces clean, sequential human-friendly tokens
    using DynamoDB atomic ADD counter (X-101, X-102, X-103...).
    """
    repo = DynamoDBRepository()

    token1 = repo.generate_next_token(prefix="X")
    assert token1 == "X-101"

    token2 = repo.generate_next_token(prefix="X")
    assert token2 == "X-102"

    token3 = repo.generate_next_token(prefix="X")
    assert token3 == "X-103"

    # Verify counter item in DynamoDB
    res = repo.table.get_item(
        Key={
            "PK": "COUNTER#TOKEN",
            "SK": "COUNTER#TOKEN",
        }
    )
    assert "Item" in res
    assert int(res["Item"]["last_token_number"]) == 3


def test_queue_admission_success_path(client: TestClient, aws_env):
    """
    Test successful queue admission of a PAID order:
    - Generates human-friendly sequential token
    - Transitions order status to QUEUED
    - Assigns 1-based queue position
    - Backend-calculates deterministic ETA
    - Persists in DynamoDB under Order item and PK: QUEUE#ACTIVE
    """
    order_id = _create_and_pay_test_order(client, page_count=5, copies=1, color_mode="bw")

    # Admit to queue
    res = client.post(f"/orders/{order_id}/queue")
    assert res.status_code == 200
    queue_data = res.json()

    assert queue_data["order_id"] == order_id
    assert queue_data["token_number"] == "X-101"
    assert queue_data["queue_position"] == 1
    assert queue_data["active_queue_length"] == 1
    assert queue_data["status"] == "QUEUED"
    assert "estimated_completion_at" in queue_data
    assert "queue_entered_at" in queue_data
    assert queue_data["estimated_wait_seconds"] > 0
    assert queue_data["estimated_wait_minutes"] > 0

    # Verify updated Order state via GET /orders/{order_id}
    order_res = client.get(f"/orders/{order_id}")
    assert order_res.status_code == 200
    order = order_res.json()
    assert order["status"] == "QUEUED"
    assert order["token_number"] == "X-101"

    # Verify active queue item in DynamoDB directly
    repo = DynamoDBRepository()
    queue_item = repo.get_queue_item(order_id)
    assert queue_item is not None
    assert queue_item["order_id"] == order_id
    assert queue_item["token_number"] == "X-101"
    assert queue_item["status"] == "QUEUED"
    assert queue_item["color_mode"] == "bw"


def test_queue_admission_unpaid_order_rejected(client: TestClient, aws_env):
    """
    Test that an unpaid order (status PENDING_PAYMENT) is rejected from entering the queue with 400.
    """
    doc_id = _upload_test_document(client)
    res = client.post(
        "/orders",
        json={
            "document_id": doc_id,
            "student_id": "STU-001",
            "page_count": 5,
            "copies": 1,
            "color_mode": "bw",
        },
    )
    order_id = res.json()["order_id"]
    assert res.json()["status"] == "PENDING_PAYMENT"

    # Try to admit unpaid order
    q_res = client.post(f"/orders/{order_id}/queue")
    assert q_res.status_code == 400
    err = q_res.json()["detail"]["error"]
    assert err["code"] == "ORDER_NOT_PAID"
    assert "not eligible for queue admission" in err["message"]


def test_queue_admission_payment_failed_order_rejected(client: TestClient, aws_env):
    """
    Test that an order with failed payment (status PAYMENT_FAILED) is rejected from entering the queue with 400.
    """
    doc_id = _upload_test_document(client)
    res = client.post(
        "/orders",
        json={
            "document_id": doc_id,
            "student_id": "STU-001",
            "page_count": 5,
            "copies": 1,
            "color_mode": "bw",
        },
    )
    order_id = res.json()["order_id"]

    # Simulate payment failure
    pay_res = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "FAILURE"})
    assert pay_res.status_code == 200
    assert pay_res.json()["status"] == "FAILED"
    assert pay_res.json()["order_status"] == "PAYMENT_FAILED"

    # Try to admit failed payment order
    q_res = client.post(f"/orders/{order_id}/queue")
    assert q_res.status_code == 400
    err = q_res.json()["detail"]["error"]
    assert err["code"] == "ORDER_NOT_PAID"


def test_queue_admission_nonexistent_order_rejected(client: TestClient, aws_env):
    """
    Test that queue admission for a nonexistent order returns 404 NOT_FOUND.
    """
    q_res = client.post("/orders/ORD-NONEXISTENT/queue")
    assert q_res.status_code == 404
    err = q_res.json()["detail"]["error"]
    assert err["code"] == "ORDER_NOT_FOUND"


def test_duplicate_admission_rejection(client: TestClient, aws_env):
    """
    Test that admitting an already queued order is rejected idempotently with 400 ORDER_ALREADY_QUEUED.
    """
    order_id = _create_and_pay_test_order(client, page_count=5)

    # First admission succeeds
    res1 = client.post(f"/orders/{order_id}/queue")
    assert res1.status_code == 200
    token = res1.json()["token_number"]
    assert token == "X-101"

    # Second admission is rejected
    res2 = client.post(f"/orders/{order_id}/queue")
    assert res2.status_code == 400
    err = res2.json()["detail"]["error"]
    assert err["code"] == "ORDER_ALREADY_QUEUED"
    assert f"Order '{order_id}' is already queued with token 'X-101'." in err["message"]

    # Verify order retains original token and status
    order_res = client.get(f"/orders/{order_id}")
    assert order_res.json()["token_number"] == "X-101"
    assert order_res.json()["status"] == "QUEUED"


def test_queue_position_across_multiple_orders(client: TestClient, aws_env):
    """
    Test that queue positions are 1-based and correctly reflect chronological arrival order.
    """
    order_id_1 = _create_and_pay_test_order(client, page_count=5)
    order_id_2 = _create_and_pay_test_order(client, page_count=10)
    order_id_3 = _create_and_pay_test_order(client, page_count=20)

    # Admit Order 1
    q1 = client.post(f"/orders/{order_id_1}/queue").json()
    assert q1["token_number"] == "X-101"
    assert q1["queue_position"] == 1
    assert q1["active_queue_length"] == 1

    # Admit Order 2
    q2 = client.post(f"/orders/{order_id_2}/queue").json()
    assert q2["token_number"] == "X-102"
    assert q2["queue_position"] == 2
    assert q2["active_queue_length"] == 2

    # Admit Order 3
    q3 = client.post(f"/orders/{order_id_3}/queue").json()
    assert q3["token_number"] == "X-103"
    assert q3["queue_position"] == 3
    assert q3["active_queue_length"] == 3

    # Query queue status individually
    status1 = client.get(f"/orders/{order_id_1}/queue").json()
    assert status1["queue_position"] == 1
    assert status1["token_number"] == "X-101"
    assert status1["active_queue_length"] == 3

    status2 = client.get(f"/orders/{order_id_2}/queue").json()
    assert status2["queue_position"] == 2
    assert status2["token_number"] == "X-102"
    assert status2["active_queue_length"] == 3

    status3 = client.get(f"/orders/{order_id_3}/queue").json()
    assert status3["queue_position"] == 3
    assert status3["token_number"] == "X-103"
    assert status3["active_queue_length"] == 3


def test_deterministic_eta_calculation_accuracy(client: TestClient, aws_env):
    """
    Test deterministic ETA engine calculations based on:
    - Base setup time = 60s
    - B&W rate = 2s/page
    - Color rate = 5s/page
    """
    # Order 1: 10 pages B&W => 60s setup + (10 * 2s) = 80s
    order_id_1 = _create_and_pay_test_order(client, page_count=10, color_mode="bw")
    q1 = client.post(f"/orders/{order_id_1}/queue").json()
    assert q1["estimated_wait_seconds"] == 80
    assert q1["estimated_wait_minutes"] == round(80 / 60.0, 1)

    # Order 2: 4 pages Color => 60s setup + (4 * 5s) = 80s
    # Total ETA for Order 2 = 80s (Order 1) + 80s (Order 2) = 160s
    order_id_2 = _create_and_pay_test_order(client, page_count=4, color_mode="color")
    q2 = client.post(f"/orders/{order_id_2}/queue").json()
    assert q2["estimated_wait_seconds"] == 160
    assert q2["estimated_wait_minutes"] == round(160 / 60.0, 1)

    # Order 3: 5 pages B&W, 2 copies => total_pages = 10 => 60s setup + (10 * 2s) = 80s
    # Total ETA for Order 3 = 160s + 80s = 240s (4.0 mins)
    order_id_3 = _create_and_pay_test_order(client, page_count=5, copies=2, color_mode="bw")
    q3 = client.post(f"/orders/{order_id_3}/queue").json()
    assert q3["estimated_wait_seconds"] == 240
    assert q3["estimated_wait_minutes"] == 4.0


def test_get_queue_status_unadmitted_order(client: TestClient, aws_env):
    """
    Test that querying queue status for an order that has not entered the queue returns 404 ORDER_NOT_QUEUED.
    """
    order_id = _create_and_pay_test_order(client)
    # Order is PAID but not yet queued
    res = client.get(f"/orders/{order_id}/queue")
    assert res.status_code == 404
    err = res.json()["detail"]["error"]
    assert err["code"] == "ORDER_NOT_QUEUED"


def test_get_queue_status_nonexistent_order(client: TestClient, aws_env):
    """
    Test that querying queue status for a nonexistent order returns 404 ORDER_NOT_FOUND.
    """
    res = client.get("/orders/ORD-MISSING/queue")
    assert res.status_code == 404
    err = res.json()["detail"]["error"]
    assert err["code"] == "ORDER_NOT_FOUND"


def test_queue_persists_in_dynamodb_active_partition(client: TestClient, aws_env):
    """
    Verify that queue admission populates DynamoDB partition PK: QUEUE#ACTIVE with all
    required print attributes for operational staff (Slice 5 readiness).
    """
    order_id = _create_and_pay_test_order(client, page_count=8, copies=3, color_mode="color", paper_size="A3")
    q_res = client.post(f"/orders/{order_id}/queue")
    assert q_res.status_code == 200

    repo = DynamoDBRepository()
    active_items = repo.get_active_queue_items()
    assert len(active_items) == 1

    item = active_items[0]
    assert item["PK"] == "QUEUE#ACTIVE"
    assert item["SK"] == f"ORDER#{order_id}"
    assert item["order_id"] == order_id
    assert item["token_number"] == "X-101"
    assert item["total_pages_printed"] == 24  # 8 pages * 3 copies
    assert item["color_mode"] == "color"
    assert item["paper_size"] == "A3"
    assert item["status"] == "QUEUED"
    assert "queue_entered_at" in item
    assert "estimated_completion_at" in item


def test_queue_endpoints_support_trailing_slash(client: TestClient, aws_env):
    """
    Test that POST and GET endpoints work with trailing slashes.
    """
    order_id = _create_and_pay_test_order(client)
    res = client.post(f"/orders/{order_id}/queue/")
    assert res.status_code == 200
    assert res.json()["token_number"] == "X-101"

    status_res = client.get(f"/orders/{order_id}/queue/")
    assert status_res.status_code == 200
    assert status_res.json()["token_number"] == "X-101"


def test_queue_status_when_order_is_no_longer_in_active_queue(client: TestClient, aws_env):
    """
    Test queue status when an order is updated to PROCESSING or READY and removed
    from active queue items (Slice 5 prep).
    """
    order_id = _create_and_pay_test_order(client)
    client.post(f"/orders/{order_id}/queue")

    # Simulate removal from active queue (as will happen in Slice 5)
    repo = DynamoDBRepository()
    repo.table.delete_item(
        Key={
            "PK": "QUEUE#ACTIVE",
            "SK": f"ORDER#{order_id}",
        }
    )

    status_res = client.get(f"/orders/{order_id}/queue")
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["order_id"] == order_id
    assert data["token_number"] == "X-101"
    assert data["queue_position"] == 0
    assert data["estimated_wait_seconds"] == 0
    assert data["estimated_wait_minutes"] == 0.0
