"""
Automated tests for Vertical Slice 6: Complete Student Tracking + History.
Tests cover:
- Orders list query by student_id (GET /orders?student_id=... and GET /students/{id}/orders)
- Strict isolation to requesting student (no cross-student data leakage)
- Empty history returns empty list []
- Missing/empty student_id returns 400 (STUDENT_ID_REQUIRED)
- Chronologically descending sorting of orders
- Fresh presigned S3 download URL generation for previous documents
- Payment receipt verification within order history item
- Simulated payment failure visible in history and timeline
- Token, live queue position, and deterministic ETA display for active queued orders
- Operator rejection reason display for rejected orders
- Complete status timeline verification across all order lifecycle states:
    - PENDING_PAYMENT
    - PAID
    - QUEUED
    - PROCESSING
    - READY
    - COMPLETED
    - REJECTED
    - PAYMENT_FAILED
- Standalone timeline inspection endpoint (GET /orders/{id}/timeline)
- 404 ORDER_NOT_FOUND for invalid order timeline queries
"""
import io
import pytest
from fastapi.testclient import TestClient


def _upload_test_document(
    client: TestClient,
    student_id: str = "STU-HIST-001",
    filename: str = "history_sample.pdf",
    content: bytes = b"%PDF-1.4 Mock PDF content for Slice 6 history testing",
) -> str:
    """Helper to upload a document for a student and return document_id."""
    files = {"file": (filename, io.BytesIO(content), "application/pdf")}
    res = client.post("/documents/", files=files, data={"student_id": student_id})
    assert res.status_code == 201
    return res.json()["document_id"]


def _create_order(
    client: TestClient,
    student_id: str = "STU-HIST-001",
    filename: str = "order_doc.pdf",
    page_count: int = 4,
    color_mode: str = "bw",
    copies: int = 1,
) -> dict:
    """Helper to upload a document and place an order."""
    doc_id = _upload_test_document(client, student_id=student_id, filename=filename)
    payload = {
        "document_id": doc_id,
        "student_id": student_id,
        "page_count": page_count,
        "color_mode": color_mode,
        "paper_size": "A4",
        "copies": copies,
        "double_sided": False,
    }
    res = client.post("/orders", json=payload)
    assert res.status_code == 201
    return res.json()


# ==============================================================================
# 1. EMPTY HISTORY & INPUT VALIDATION
# ==============================================================================

def test_empty_history_returns_empty_list(client: TestClient):
    """Querying a student with no prior orders returns an empty list []."""
    res = client.get("/orders?student_id=STU-NEVER-ORDERED")
    assert res.status_code == 200
    assert res.json() == []

    # Test alias route /students/{id}/orders
    res_alias = client.get("/students/STU-NEVER-ORDERED/orders")
    assert res_alias.status_code == 200
    assert res_alias.json() == []


def test_get_orders_requires_student_id(client: TestClient):
    """GET /orders without student_id query parameter returns 400 Bad Request."""
    res = client.get("/orders")
    assert res.status_code == 400
    data = res.json()
    assert data["detail"]["error"]["code"] == "STUDENT_ID_REQUIRED"

    # Whitespace-only student_id also rejected
    res_ws = client.get("/orders?student_id=   ")
    assert res_ws.status_code == 400
    assert res_ws.json()["detail"]["error"]["code"] == "STUDENT_ID_REQUIRED"


# ==============================================================================
# 2. STUDENT ISOLATION & CHRONOLOGICAL SORTING
# ==============================================================================

def test_orders_isolated_to_requesting_student(client: TestClient):
    """Ensure student A only sees student A's orders, preventing cross-student leakage."""
    stu_a = "STU-ALICE-101"
    stu_b = "STU-BOB-202"

    order_a1 = _create_order(client, student_id=stu_a, filename="alice_notes.pdf")
    order_a2 = _create_order(client, student_id=stu_a, filename="alice_report.pdf")
    order_b1 = _create_order(client, student_id=stu_b, filename="bob_assignment.pdf")

    # Alice queries her orders
    res_a = client.get(f"/orders?student_id={stu_a}")
    assert res_a.status_code == 200
    alice_orders = res_a.json()
    assert len(alice_orders) == 2
    alice_order_ids = {o["order_id"] for o in alice_orders}
    assert order_a1["order_id"] in alice_order_ids
    assert order_a2["order_id"] in alice_order_ids
    assert order_b1["order_id"] not in alice_order_ids

    # Bob queries his orders
    res_b = client.get(f"/orders?student_id={stu_b}")
    assert res_b.status_code == 200
    bob_orders = res_b.json()
    assert len(bob_orders) == 1
    assert bob_orders[0]["order_id"] == order_b1["order_id"]
    assert bob_orders[0]["filename"] == "bob_assignment.pdf"


def test_orders_sorted_chronologically_descending(client: TestClient):
    """Multiple orders for the same student are sorted chronologically descending."""
    stu = "STU-CHRONO-303"
    order1 = _create_order(client, student_id=stu, filename="doc1.pdf")
    order2 = _create_order(client, student_id=stu, filename="doc2.pdf")
    order3 = _create_order(client, student_id=stu, filename="doc3.pdf")

    res = client.get(f"/orders?student_id={stu}")
    assert res.status_code == 200
    orders = res.json()
    assert len(orders) == 3

    # Order 3 is newest, Order 1 is oldest
    assert orders[0]["order_id"] == order3["order_id"]
    assert orders[1]["order_id"] == order2["order_id"]
    assert orders[2]["order_id"] == order1["order_id"]

    # Verify timestamps are strictly descending
    t0 = orders[0]["created_at"]
    t1 = orders[1]["created_at"]
    t2 = orders[2]["created_at"]
    assert t0 >= t1 >= t2


# ==============================================================================
# 3. PRESIGNED S3 DOCUMENT ACCESS
# ==============================================================================

def test_fresh_presigned_s3_url_on_history_retrieval(client: TestClient):
    """Each order in student history provides a valid, fresh presigned S3 GET URL."""
    stu = "STU-DOC-404"
    order = _create_order(client, student_id=stu, filename="secure_thesis.pdf")

    res = client.get(f"/orders?student_id={stu}")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    item = items[0]

    assert item["document_url"] is not None
    assert item["download_url"] is not None
    assert "https://" in item["document_url"] or "http://" in item["document_url"]
    assert "X-Amz-Signature=" in item["document_url"] or "AWSAccessKeyId=" in item["document_url"]
    assert item["filename"] == "secure_thesis.pdf"


# ==============================================================================
# 4. PAYMENT RECEIPT & PAYMENT FAILED HANDLING
# ==============================================================================

def test_payment_receipt_in_history_item(client: TestClient):
    """Successfully paid order includes complete payment receipt in history."""
    stu = "STU-PAY-505"
    order = _create_order(client, student_id=stu, filename="paid_syllabus.pdf")
    order_id = order["order_id"]

    # Simulate payment success
    pay_res = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "SUCCESS"})
    assert pay_res.status_code == 200
    pay_data = pay_res.json()

    # Query history
    res = client.get(f"/orders?student_id={stu}")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    item = items[0]

    assert item["payment_status"] == "SUCCESS"
    assert item["status"] == "PAID"
    receipt = item["payment_receipt"]
    assert receipt is not None
    assert receipt["payment_id"] == pay_data["payment_id"]
    assert receipt["payment_reference"] == pay_data["payment_reference"]
    assert receipt["status"] == "SUCCESS"
    assert receipt["amount_paise"] == order["pricing"]["total_price_paise"]
    assert receipt["amount_rupees"] == order["pricing"]["total_price_rupees"]
    assert receipt["currency"] == "INR"


def test_payment_failed_status_and_reason_in_history(client: TestClient):
    """Declined payment reflects PAYMENT_FAILED with failure details in history and timeline."""
    stu = "STU-FAIL-606"
    order = _create_order(client, student_id=stu, filename="failed_print.pdf")
    order_id = order["order_id"]

    # Simulate payment failure
    pay_res = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "FAILURE"})
    assert pay_res.status_code == 200

    # Query history
    res = client.get(f"/orders?student_id={stu}")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    item = items[0]

    assert item["payment_status"] == "FAILED"
    assert item["status"] == "PAYMENT_FAILED"
    receipt = item["payment_receipt"]
    assert receipt is not None
    assert receipt["status"] == "FAILED"
    assert receipt["outcome"] == "FAILURE"
    assert receipt["failure_reason"] is not None

    # Verify timeline reflects PAYMENT_FAILED
    timeline_events = [e["event"] for e in item["timeline"]]
    assert "PAYMENT_FAILED" in timeline_events
    fail_event = next(e for e in item["timeline"] if e["event"] == "PAYMENT_FAILED")
    assert fail_event["status"] == "FAILED"


# ==============================================================================
# 5. QUEUE TOKEN, LIVE POSITION, AND ETA
# ==============================================================================

def test_queue_token_position_eta_in_history(client: TestClient):
    """Admitted order reflects issued token, 1-based queue position, and ETA."""
    stu = "STU-QUEUE-707"
    order = _create_order(client, student_id=stu, filename="queue_doc.pdf")
    order_id = order["order_id"]

    client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "SUCCESS"})
    queue_res = client.post(f"/orders/{order_id}/queue")
    assert queue_res.status_code == 200
    queue_data = queue_res.json()

    # Query history
    res = client.get(f"/orders?student_id={stu}")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    item = items[0]

    assert item["status"] == "QUEUED"
    assert item["token_number"] == queue_data["token_number"]
    assert item["queue_position"] == 1
    assert item["estimated_completion_at"] is not None

    # Check timeline contains QUEUED event with token and ETA
    q_event = next((e for e in item["timeline"] if e["event"] == "QUEUED"), None)
    assert q_event is not None
    assert q_event["token_number"] == queue_data["token_number"]
    assert q_event["queue_position"] == 1


# ==============================================================================
# 6. OPERATOR REJECTION REASON VISIBILITY
# ==============================================================================

def test_rejection_reason_display_for_rejected_order(client: TestClient):
    """Rejected order shows REJECTED status, formal reason, and REJECTED timeline event."""
    stu = "STU-REJ-808"
    order = _create_order(client, student_id=stu, filename="rejected_draft.pdf")
    order_id = order["order_id"]

    client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "SUCCESS"})
    client.post(f"/orders/{order_id}/queue")

    # Staff rejects the order with mandatory formal reason
    formal_reason = "Corrupt font raster on pages 3 and 7; unprintable format."
    rej_res = client.post(f"/staff/orders/{order_id}/reject", json={"rejection_reason": formal_reason})
    assert rej_res.status_code == 200

    # Query history
    res = client.get(f"/orders?student_id={stu}")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    item = items[0]

    assert item["status"] == "REJECTED"
    assert item["rejection_reason"] == formal_reason

    # Verify timeline reflects REJECTED
    rej_event = next((e for e in item["timeline"] if e["event"] == "REJECTED"), None)
    assert rej_event is not None
    assert rej_event["status"] == "FAILED"
    assert rej_event["rejection_reason"] == formal_reason


# ==============================================================================
# 7. COMPLETE STATUS TIMELINE ACROSS ALL LIFECYCLE STATES
# ==============================================================================

def test_complete_status_timeline_across_all_lifecycle_states(client: TestClient):
    """
    Comprehensive verification that every lifecycle transition accurately reflects
    the complete ordered sequence of timeline events:
    1. PENDING_PAYMENT: DOCUMENT_UPLOADED, CREATED, PAYMENT_PENDING
    2. PAID: DOCUMENT_UPLOADED, CREATED, PAID
    3. QUEUED: DOCUMENT_UPLOADED, CREATED, PAID, QUEUED
    4. PROCESSING: DOCUMENT_UPLOADED, CREATED, PAID, QUEUED, PROCESSING
    5. READY: DOCUMENT_UPLOADED, CREATED, PAID, QUEUED, PROCESSING, READY
    6. COMPLETED: DOCUMENT_UPLOADED, CREATED, PAID, QUEUED, PROCESSING, READY, COMPLETED
    """
    stu = "STU-TIMELINE-909"
    order = _create_order(client, student_id=stu, filename="lifecycle_doc.pdf")
    order_id = order["order_id"]

    # State 1: PENDING_PAYMENT
    t_res1 = client.get(f"/orders/{order_id}/timeline")
    assert t_res1.status_code == 200
    t1 = t_res1.json()
    events1 = [e["event"] for e in t1["events"]]
    assert events1 == ["DOCUMENT_UPLOADED", "CREATED", "PAYMENT_PENDING"]

    # State 2: PAID
    client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "SUCCESS"})
    t_res2 = client.get(f"/orders/{order_id}/timeline")
    assert t_res2.status_code == 200
    events2 = [e["event"] for e in t_res2.json()["events"]]
    assert events2 == ["DOCUMENT_UPLOADED", "CREATED", "PAID"]

    # State 3: QUEUED
    client.post(f"/orders/{order_id}/queue")
    t_res3 = client.get(f"/orders/{order_id}/timeline")
    assert t_res3.status_code == 200
    events3 = [e["event"] for e in t_res3.json()["events"]]
    assert events3 == ["DOCUMENT_UPLOADED", "CREATED", "PAID", "QUEUED"]

    # State 4: PROCESSING (Staff Accept)
    client.post(f"/staff/orders/{order_id}/accept")
    t_res4 = client.get(f"/orders/{order_id}/timeline")
    assert t_res4.status_code == 200
    events4 = [e["event"] for e in t_res4.json()["events"]]
    assert events4 == ["DOCUMENT_UPLOADED", "CREATED", "PAID", "QUEUED", "PROCESSING"]

    # State 5: READY (Staff Ready)
    client.post(f"/staff/orders/{order_id}/ready")
    t_res5 = client.get(f"/orders/{order_id}/timeline")
    assert t_res5.status_code == 200
    events5 = [e["event"] for e in t_res5.json()["events"]]
    assert events5 == ["DOCUMENT_UPLOADED", "CREATED", "PAID", "QUEUED", "PROCESSING", "READY"]

    # State 6: COMPLETED (Staff Complete)
    client.post(f"/staff/orders/{order_id}/complete")
    t_res6 = client.get(f"/orders/{order_id}/timeline")
    assert t_res6.status_code == 200
    events6 = [e["event"] for e in t_res6.json()["events"]]
    assert events6 == ["DOCUMENT_UPLOADED", "CREATED", "PAID", "QUEUED", "PROCESSING", "READY", "COMPLETED"]

    # Verify each event has valid timestamp and title
    for ev in t_res6.json()["events"]:
        assert ev["timestamp"] is not None
        assert len(ev["title"]) > 0
        assert len(ev["description"]) > 0


def test_order_timeline_endpoint_not_found(client: TestClient):
    """Querying timeline for nonexistent order returns 404 ORDER_NOT_FOUND."""
    res = client.get("/orders/ORD-NONEXISTENT/timeline")
    assert res.status_code == 404
    assert res.json()["detail"]["error"]["code"] == "ORDER_NOT_FOUND"


# ==============================================================================
# 8. STUDENTS ENDPOINT ALIAS CONSISTENCY
# ==============================================================================

def test_students_endpoint_alias_consistency(client: TestClient):
    """GET /students/{id}/orders returns identical payload to GET /orders?student_id={id}."""
    stu = "STU-ALIAS-010"
    _create_order(client, student_id=stu, filename="alias_doc.pdf")

    res_query = client.get(f"/orders?student_id={stu}")
    res_path = client.get(f"/students/{stu}/orders")

    assert res_query.status_code == 200
    assert res_path.status_code == 200
    assert res_query.json() == res_path.json()


# ==============================================================================
# 9. STUDENT HISTORY & TRACKING UI SERVING & ELEMENTS
# ==============================================================================

def test_history_ui_elements_and_routes(client: TestClient):
    """
    Verify /tracking and /history routes serve the UI containing
    Slice 6 Student Tracking & History components.
    """
    for route in ("/tracking", "/history", "/"):
        res = client.get(route)
        assert res.status_code == 200
        html = res.text

        # Header badge includes Slice 6
        assert "Slice 6: Student Tracking + History" in html

        # Navigation tabs
        assert 'id="tabStudentPortal"' in html
        assert 'id="tabHistoryPortal"' in html
        assert 'id="tabStaffPortal"' in html

        # Student History Portal Section & Controls
        assert 'id="historyPortalSection"' in html
        assert 'id="historyStudentId"' in html
        assert 'id="btnFetchHistory"' in html
        assert 'id="historyOrdersContainer"' in html
        assert 'id="historyAlertBox"' in html
        assert 'id="filterBtnAll"' in html
        assert 'id="jumpToHistoryBtn"' in html
