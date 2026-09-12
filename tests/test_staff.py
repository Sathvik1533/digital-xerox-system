"""
Tests for Vertical Slice 5: Staff Processing.
Tests cover:
- Staff Operations Portal orders query (GET /staff/orders, GET /staff/queue)
- Document metadata and S3 presigned URL generation for staff document inspection
- Order acceptance (QUEUED -> PROCESSING) via /staff/orders/{id}/accept and /orders/{id}/process
- Order rejection with formal mandatory reason (QUEUED -> REJECTED)
- Rejection rejected when reason is missing, empty, or whitespace (400 REJECTION_REASON_REQUIRED)
- Order marked ready for pickup (PROCESSING -> READY) and removal from active queue
- Order completion (READY -> COMPLETED)
- Strict state machine enforcement: invalid transitions rejected with 400 INVALID_STATE_TRANSITION
- Dynamic operational queue position shift: Order behind shifts from #2 to #1 when order ahead is marked ready
- Student tracking visibility reflecting PROCESSING, READY, COMPLETED, and REJECTED states
- Nonexistent order handling across all staff operations (404 ORDER_NOT_FOUND)
"""
import io
import pytest
from fastapi.testclient import TestClient
from boto3.dynamodb.conditions import Key
from app.repositories.dynamodb_repo import DynamoDBRepository


def _upload_test_doc(client: TestClient, filename: str = "thesis_doc.pdf") -> str:
    """Helper to upload a test PDF and return its document_id."""
    files = {
        "file": (filename, io.BytesIO(b"%PDF-1.4 Mock document content for staff slice"), "application/pdf")
    }
    res = client.post("/documents/", files=files, data={"student_id": "STU-STAFF-001"})
    assert res.status_code == 201
    return res.json()["document_id"]


def _create_paid_and_queued_order(
    client: TestClient,
    filename: str = "staff_test.pdf",
    page_count: int = 5,
    copies: int = 1,
    color_mode: str = "bw",
) -> dict:
    """Helper to upload, order, pay, and admit order to queue."""
    doc_id = _upload_test_doc(client, filename=filename)
    payload = {
        "document_id": doc_id,
        "student_id": "STU-STAFF-001",
        "page_count": page_count,
        "color_mode": color_mode,
        "paper_size": "A4",
        "copies": copies,
        "double_sided": False,
    }
    order_res = client.post("/orders", json=payload)
    assert order_res.status_code == 201
    order_data = order_res.json()
    order_id = order_data["order_id"]

    # Simulate payment success
    pay_res = client.post(f"/orders/{order_id}/payment/simulate", json={"outcome": "SUCCESS"})
    assert pay_res.status_code == 200

    # Admit to queue
    q_res = client.post(f"/orders/{order_id}/queue")
    assert q_res.status_code == 200
    q_data = q_res.json()

    return {
        "order_id": order_id,
        "document_id": doc_id,
        "token_number": q_data["token_number"],
        "queue_position": q_data["queue_position"],
    }


class TestStaffListOrders:
    """Tests for GET /staff/orders and GET /staff/queue."""

    def test_list_active_orders_empty(self, client: TestClient):
        """When no orders are queued, staff list returns empty list."""
        res = client.get("/staff/orders")
        assert res.status_code == 200
        assert res.json() == []

        res_queue = client.get("/staff/queue")
        assert res_queue.status_code == 200
        assert res_queue.json() == []

    def test_list_active_orders_with_presigned_s3_url(self, client: TestClient):
        """Active orders include document metadata, print config, and secure presigned S3 URL."""
        order_info = _create_paid_and_queued_order(client, filename="biology_notes.pdf")
        order_id = order_info["order_id"]

        res = client.get("/staff/orders")
        assert res.status_code == 200
        items = res.json()
        assert len(items) == 1
        item = items[0]

        assert item["order_id"] == order_id
        assert item["status"] == "QUEUED"
        assert item["token_number"] == order_info["token_number"]
        assert item["filename"] == "biology_notes.pdf"
        assert item["queue_position"] == 1
        # S3 presigned URL check
        assert item["document_url"] is not None
        assert "http" in item["document_url"]
        assert "biology_notes.pdf" in item["document_key"]

    def test_list_orders_status_filter(self, client: TestClient):
        """Staff list respects status filter parameter."""
        order_1 = _create_paid_and_queued_order(client, filename="doc1.pdf")
        order_2 = _create_paid_and_queued_order(client, filename="doc2.pdf")

        # Accept order 1 -> PROCESSING
        client.post(f"/staff/orders/{order_1['order_id']}/accept")

        # Filter by QUEUED
        q_res = client.get("/staff/orders?status=QUEUED")
        assert q_res.status_code == 200
        queued_items = q_res.json()
        assert len(queued_items) == 1
        assert queued_items[0]["order_id"] == order_2["order_id"]

        # Filter by PROCESSING
        p_res = client.get("/staff/orders?status=PROCESSING")
        assert p_res.status_code == 200
        proc_items = p_res.json()
        assert len(proc_items) == 1
        assert proc_items[0]["order_id"] == order_1["order_id"]


class TestStaffAcceptOrder:
    """Tests for POST /staff/orders/{order_id}/accept and /orders/{order_id}/process."""

    def test_accept_order_success(self, client: TestClient):
        """Staff accepts order: status transitions from QUEUED to PROCESSING."""
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]

        res = client.post(f"/staff/orders/{order_id}/accept")
        assert res.status_code == 200
        data = res.json()
        assert data["order_id"] == order_id
        assert data["status"] == "PROCESSING"
        assert data["token_number"] == order_info["token_number"]
        assert data["document_url"] is not None

        # Verify DynamoDB order record
        order_res = client.get(f"/orders/{order_id}")
        assert order_res.status_code == 200
        assert order_res.json()["status"] == "PROCESSING"

        # Verify active queue record still present with PROCESSING status
        repo = DynamoDBRepository()
        q_item = repo.get_queue_item(order_id)
        assert q_item is not None
        assert q_item["status"] == "PROCESSING"

    def test_accept_order_via_process_alias(self, client: TestClient):
        """POST /orders/{order_id}/process works as alias for accept."""
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]

        res = client.post(f"/orders/{order_id}/process")
        assert res.status_code == 200
        assert res.json()["status"] == "PROCESSING"

    def test_accept_order_via_orders_accept_alias(self, client: TestClient):
        """POST /orders/{order_id}/accept works as alias for accept."""
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]

        res = client.post(f"/orders/{order_id}/accept")
        assert res.status_code == 200
        assert res.json()["status"] == "PROCESSING"

    def test_accept_order_via_process_trailing_slash(self, client: TestClient):
        """POST /orders/{order_id}/process/ supports trailing slash."""
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]

        res = client.post(f"/orders/{order_id}/process/")
        assert res.status_code == 200
        assert res.json()["status"] == "PROCESSING"

    def test_staff_order_response_includes_payment_status(self, client: TestClient):
        """StaffOrderResponse includes payment_status."""
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]

        res = client.get(f"/staff/orders?status=ACTIVE")
        assert res.status_code == 200
        items = res.json()
        assert len(items) >= 1
        matched = next(i for i in items if i["order_id"] == order_id)
        assert matched["payment_status"] == "SUCCESS"



class TestStaffRejectOrder:
    """Tests for POST /staff/orders/{order_id}/reject."""

    def test_reject_order_with_valid_reason(self, client: TestClient):
        """Staff rejects order with formal reason: status becomes REJECTED and leaves active queue."""
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]

        payload = {"rejection_reason": "File corrupted, unreadable formatting on pages 3-5."}
        res = client.post(f"/staff/orders/{order_id}/reject", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "REJECTED"
        assert data["rejection_reason"] == payload["rejection_reason"]
        assert data["queue_position"] == 0

        # Verify removed from PK: QUEUE#ACTIVE
        repo = DynamoDBRepository()
        assert repo.get_queue_item(order_id) is None
        active_items = repo.get_active_queue_items()
        assert len(active_items) == 0

        # Verify student order query reflects REJECTED with reason
        order_res = client.get(f"/orders/{order_id}")
        assert order_res.status_code == 200
        assert order_res.json()["status"] == "REJECTED"
        assert order_res.json()["rejection_reason"] == payload["rejection_reason"]

    def test_reject_order_missing_reason_fails(self, client: TestClient):
        """Rejecting without rejection_reason body field strictly returns 400 REJECTION_REASON_REQUIRED."""
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]

        # Missing field in JSON
        res = client.post(f"/staff/orders/{order_id}/reject", json={})
        assert res.status_code == 400
        assert res.json()["detail"]["error"]["code"] == "REJECTION_REASON_REQUIRED"

        # Completely empty request body
        res_empty = client.post(f"/staff/orders/{order_id}/reject")
        assert res_empty.status_code == 400
        assert res_empty.json()["detail"]["error"]["code"] == "REJECTION_REASON_REQUIRED"

        # Explicit null rejection_reason
        res_null = client.post(f"/staff/orders/{order_id}/reject", json={"rejection_reason": None})
        assert res_null.status_code == 400
        assert res_null.json()["detail"]["error"]["code"] == "REJECTION_REASON_REQUIRED"


    def test_reject_order_empty_or_whitespace_reason_fails(self, client: TestClient):
        """Rejecting with empty string or whitespace reason returns 400 REJECTION_REASON_REQUIRED."""
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]

        # Empty string
        res = client.post(f"/staff/orders/{order_id}/reject", json={"rejection_reason": ""})
        assert res.status_code == 400
        assert res.json()["detail"]["error"]["code"] == "REJECTION_REASON_REQUIRED"

        # Whitespace only
        res2 = client.post(f"/staff/orders/{order_id}/reject", json={"rejection_reason": "   \n\t  "})
        assert res2.status_code == 400
        assert res2.json()["detail"]["error"]["code"] == "REJECTION_REASON_REQUIRED"

    def test_reject_order_via_orders_alias(self, client: TestClient):
        """POST /orders/{order_id}/reject works as alias for reject."""
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]

        payload = {"rejection_reason": "Rejected via /orders alias route"}
        res = client.post(f"/orders/{order_id}/reject", json=payload)
        assert res.status_code == 200
        assert res.json()["status"] == "REJECTED"
        assert res.json()["rejection_reason"] == payload["rejection_reason"]



class TestStaffReadyAndComplete:
    """Tests for POST /staff/orders/{order_id}/ready and complete."""

    def test_ready_and_complete_lifecycle(self, client: TestClient):
        """Full happy path: QUEUED -> PROCESSING -> READY -> COMPLETED."""
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]

        # 1. QUEUED -> PROCESSING
        accept_res = client.post(f"/staff/orders/{order_id}/accept")
        assert accept_res.status_code == 200
        assert accept_res.json()["status"] == "PROCESSING"

        # 2. PROCESSING -> READY (removes from active queue)
        ready_res = client.post(f"/staff/orders/{order_id}/ready")
        assert ready_res.status_code == 200
        ready_data = ready_res.json()
        assert ready_data["status"] == "READY"
        assert ready_data["queue_position"] == 0

        # Verify order is removed from PK: QUEUE#ACTIVE
        repo = DynamoDBRepository()
        assert repo.get_queue_item(order_id) is None
        assert len(repo.get_active_queue_items()) == 0

        # 3. READY -> COMPLETED
        comp_res = client.post(f"/staff/orders/{order_id}/complete")
        assert comp_res.status_code == 200
        assert comp_res.json()["status"] == "COMPLETED"

        # Verify DynamoDB order record
        final_order = client.get(f"/orders/{order_id}")
        assert final_order.status_code == 200
        assert final_order.json()["status"] == "COMPLETED"

    def test_ready_and_complete_via_orders_alias(self, client: TestClient):
        """POST /orders/{order_id}/ready and /orders/{order_id}/complete work as aliases."""
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]

        # Accept via /orders/accept
        client.post(f"/orders/{order_id}/accept")

        # Ready via /orders/ready
        ready_res = client.post(f"/orders/{order_id}/ready")
        assert ready_res.status_code == 200
        assert ready_res.json()["status"] == "READY"

        # Complete via /orders/complete
        comp_res = client.post(f"/orders/{order_id}/complete")
        assert comp_res.status_code == 200
        assert comp_res.json()["status"] == "COMPLETED"

    def test_phantom_item_not_created_in_active_queue_when_accepting(self, client: TestClient):
        """When an order is accepted, no phantom active queue item is created if not already in queue."""
        repo = DynamoDBRepository()
        initial_items = repo.get_active_queue_items()

        # Try to accept a nonexistent order
        res = client.post("/staff/orders/ORD-GHOST-999/accept")
        assert res.status_code == 404

        after_items = repo.get_active_queue_items()
        assert len(after_items) == len(initial_items)
        assert repo.get_queue_item("ORD-GHOST-999") is None



class TestStaffInvalidStateTransitions:
    """Tests verifying strict backend state machine constraints (400 INVALID_STATE_TRANSITION)."""

    def test_cannot_accept_already_processing_order(self, client: TestClient):
        """Accepting an order that is already PROCESSING is rejected."""
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]
        client.post(f"/staff/orders/{order_id}/accept")

        res = client.post(f"/staff/orders/{order_id}/accept")
        assert res.status_code == 400
        assert res.json()["detail"]["error"]["code"] == "INVALID_STATE_TRANSITION"

    def test_cannot_mark_ready_from_queued(self, client: TestClient):
        """Marking READY directly from QUEUED without ACCEPT is rejected."""
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]

        res = client.post(f"/staff/orders/{order_id}/ready")
        assert res.status_code == 400
        assert res.json()["detail"]["error"]["code"] == "INVALID_STATE_TRANSITION"

    def test_cannot_complete_from_queued_or_processing(self, client: TestClient):
        """Completing an order before READY is rejected."""
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]

        # From QUEUED
        res = client.post(f"/staff/orders/{order_id}/complete")
        assert res.status_code == 400
        assert res.json()["detail"]["error"]["code"] == "INVALID_STATE_TRANSITION"

        # From PROCESSING
        client.post(f"/staff/orders/{order_id}/accept")
        res2 = client.post(f"/staff/orders/{order_id}/complete")
        assert res2.status_code == 400
        assert res2.json()["detail"]["error"]["code"] == "INVALID_STATE_TRANSITION"

    def test_cannot_reject_processing_order(self, client: TestClient):
        """Cannot reject an order once printing has started (PROCESSING)."""
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]
        client.post(f"/staff/orders/{order_id}/accept")

        res = client.post(
            f"/staff/orders/{order_id}/reject",
            json={"rejection_reason": "Too late to cancel"},
        )
        assert res.status_code == 400
        assert res.json()["detail"]["error"]["code"] == "INVALID_STATE_TRANSITION"

    def test_cannot_transition_from_completed(self, client: TestClient):
        """A COMPLETED order cannot be accepted, rejected, or readied again."""
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]
        client.post(f"/staff/orders/{order_id}/accept")
        client.post(f"/staff/orders/{order_id}/ready")
        client.post(f"/staff/orders/{order_id}/complete")

        for endpoint in ["accept", "ready", "complete"]:
            res = client.post(f"/staff/orders/{order_id}/{endpoint}")
            assert res.status_code == 400
            assert res.json()["detail"]["error"]["code"] == "INVALID_STATE_TRANSITION"

        reject_res = client.post(
            f"/staff/orders/{order_id}/reject",
            json={"rejection_reason": "Cannot reject done job"},
        )
        assert reject_res.status_code == 400
        assert reject_res.json()["detail"]["error"]["code"] == "INVALID_STATE_TRANSITION"

    def test_cannot_accept_unpaid_order(self, client: TestClient):
        """An order in PENDING_PAYMENT status cannot be accepted by staff."""
        doc_id = _upload_test_doc(client)
        order_res = client.post("/orders", json={
            "document_id": doc_id,
            "student_id": "STU-STAFF-001",
            "page_count": 2,
            "color_mode": "bw",
            "paper_size": "A4",
            "copies": 1,
        })
        order_id = order_res.json()["order_id"]

        res = client.post(f"/staff/orders/{order_id}/accept")
        assert res.status_code == 400
        assert res.json()["detail"]["error"]["code"] == "INVALID_STATE_TRANSITION"


class TestDynamicQueuePositionShift:
    """Tests verifying operational queue updates when an order leaves the queue."""

    def test_order_behind_moves_from_pos_2_to_pos_1(self, client: TestClient):
        """
        When Order 1 leaves the active queue (e.g. READY),
        Order 2's position dynamically moves from #2 to #1.
        """
        order_1 = _create_paid_and_queued_order(client, filename="job_1.pdf")
        order_2 = _create_paid_and_queued_order(client, filename="job_2.pdf")

        # Check initial positions
        q1_init = client.get(f"/orders/{order_1['order_id']}/queue").json()
        q2_init = client.get(f"/orders/{order_2['order_id']}/queue").json()
        assert q1_init["queue_position"] == 1
        assert q2_init["queue_position"] == 2
        assert q2_init["active_queue_length"] == 2

        # Order 1 is accepted (now PROCESSING)
        client.post(f"/staff/orders/{order_1['order_id']}/accept")

        # Order 1 is still active job #1 on printer, Order 2 is still behind it
        q2_mid = client.get(f"/orders/{order_2['order_id']}/queue").json()
        assert q2_mid["queue_position"] == 2
        assert q2_mid["active_queue_length"] == 2

        # Order 1 finishes printing -> marked READY (leaves active queue)
        ready_res = client.post(f"/staff/orders/{order_1['order_id']}/ready")
        assert ready_res.status_code == 200

        # Now Order 2 MUST dynamically be #1 in line!
        q2_after = client.get(f"/orders/{order_2['order_id']}/queue").json()
        assert q2_after["queue_position"] == 1
        assert q2_after["active_queue_length"] == 1

        # Order 1 status query reflects READY and position 0
        q1_after = client.get(f"/orders/{order_1['order_id']}/queue").json()
        assert q1_after["queue_position"] == 0
        assert q1_after["status"] == "READY"
        assert q1_after["estimated_wait_seconds"] == 0


class TestStudentTrackingReflectsStaffChanges:
    """Tests verifying student tracking endpoint (/orders/{id}/queue) reflects staff operations."""

    def test_student_tracking_processing_state(self, client: TestClient):
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]

        client.post(f"/staff/orders/{order_id}/accept")
        status_res = client.get(f"/orders/{order_id}/queue")
        assert status_res.status_code == 200
        assert status_res.json()["status"] == "PROCESSING"

    def test_student_tracking_ready_state(self, client: TestClient):
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]

        client.post(f"/staff/orders/{order_id}/accept")
        client.post(f"/staff/orders/{order_id}/ready")

        status_res = client.get(f"/orders/{order_id}/queue")
        assert status_res.status_code == 200
        data = status_res.json()
        assert data["status"] == "READY"
        assert data["queue_position"] == 0

    def test_student_tracking_completed_state(self, client: TestClient):
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]

        client.post(f"/staff/orders/{order_id}/accept")
        client.post(f"/staff/orders/{order_id}/ready")
        client.post(f"/staff/orders/{order_id}/complete")

        status_res = client.get(f"/orders/{order_id}/queue")
        assert status_res.status_code == 200
        data = status_res.json()
        assert data["status"] == "COMPLETED"
        assert data["queue_position"] == 0

    def test_student_tracking_rejected_state_with_reason(self, client: TestClient):
        order_info = _create_paid_and_queued_order(client)
        order_id = order_info["order_id"]

        reason = "File contains corrupted raster fonts."
        client.post(f"/staff/orders/{order_id}/reject", json={"rejection_reason": reason})

        status_res = client.get(f"/orders/{order_id}/queue")
        assert status_res.status_code == 200
        data = status_res.json()
        assert data["status"] == "REJECTED"
        assert data["queue_position"] == 0
        assert data["rejection_reason"] == reason


class TestStaffNonexistentOrder:
    """Tests verifying 404 for invalid order IDs across all staff endpoints."""

    def test_accept_nonexistent_order_returns_404(self, client: TestClient):
        res = client.post("/staff/orders/ORD-NONEXISTENT/accept")
        assert res.status_code == 404
        assert res.json()["detail"]["error"]["code"] == "ORDER_NOT_FOUND"

    def test_reject_nonexistent_order_returns_404(self, client: TestClient):
        res = client.post(
            "/staff/orders/ORD-NONEXISTENT/reject",
            json={"rejection_reason": "Order does not exist"},
        )
        assert res.status_code == 404
        assert res.json()["detail"]["error"]["code"] == "ORDER_NOT_FOUND"

    def test_ready_nonexistent_order_returns_404(self, client: TestClient):
        res = client.post("/staff/orders/ORD-NONEXISTENT/ready")
        assert res.status_code == 404
        assert res.json()["detail"]["error"]["code"] == "ORDER_NOT_FOUND"

    def test_complete_nonexistent_order_returns_404(self, client: TestClient):
        res = client.post("/staff/orders/ORD-NONEXISTENT/complete")
        assert res.status_code == 404
        assert res.json()["detail"]["error"]["code"] == "ORDER_NOT_FOUND"


class TestStaffUI:
    """Tests verifying Staff Operations Portal UI serving and HTML elements."""

    def test_staff_route_serves_html(self, client: TestClient):
        """GET /staff serves the web UI with text/html content type."""
        res = client.get("/staff")
        assert res.status_code == 200
        assert "text/html" in res.headers.get("content-type", "")

    def test_staff_ui_elements_present(self, client: TestClient):
        """GET /staff HTML includes all required Staff Operations Portal DOM elements."""
        res = client.get("/staff")
        assert res.status_code == 200
        html = res.text

        # Header badge includes Slice 5
        assert "Slice 5: Staff Processing" in html

        # Navigation tabs
        assert 'id="tabStudentPortal"' in html
        assert 'id="tabStaffPortal"' in html
        assert 'id="staffQueueCountBadge"' in html

        # Staff Portal Section & Controls
        assert 'id="staffPortalSection"' in html
        assert 'id="staffStatusFilter"' in html
        assert 'id="refreshStaffBtn"' in html
        assert 'id="staffOrdersContainer"' in html
        assert 'id="staffAlertBox"' in html

        # Rejection Modal & Controls
        assert 'id="rejectModal"' in html
        assert 'id="modalOrderId"' in html
        assert 'id="modalOrderToken"' in html
        assert 'id="modalRejectReason"' in html
        assert 'id="modalCancelBtn"' in html
        assert 'id="modalConfirmBtn"' in html
