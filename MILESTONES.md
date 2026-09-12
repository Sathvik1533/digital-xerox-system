# Milestone Log

## Milestone 0 — Repository & Project Foundation
**Status:** ✅ Complete  
**Date:** 2026-09-12

### What was delivered
- Repository initialized with full project structure
- FastAPI application skeleton (`app/main.py`)
- Configuration module (`app/core/config.py`) — environment-driven, no hard-coded secrets
- Health endpoint (`/health`) — ECS load balancer check
- Test framework (pytest + fixtures)
- Phase 0 tests: 3/3 passing
- `.env.example` template
- `pyproject.toml` with ruff config

---

## Milestone 1 — Vertical Slice 1: Document Upload
**Status:** ✅ Complete  
**Date:** 2026-09-12

### What was delivered
- Document upload API (`POST /documents`, `POST /documents/upload`)
- Secure access endpoint (`GET /documents/{document_id}/access`) with presigned S3 URLs
- Document retrieval endpoint (`GET /documents/{document_id}`)
- Validation for file size (max 25MB), empty files, and allowed file formats (PDF, DOCX, DOC, TXT, PNG, JPG)
- S3 binary storage (`digital-xerox-documents`) and DynamoDB metadata persistence (`digital-xerox-orders`) with PK `DOC#{doc_id}` / SK `DOC#{doc_id}`
- Interactive Student UI with drag-and-drop file upload and DynamoDB metadata inspection
- Automated pytest test suite (13 passing tests)

---

## Milestone 2 — Vertical Slice 2: Print Configuration & Order Creation
**Status:** ✅ Complete  
**Date:** 2026-09-12

### What was delivered
- Pricing calculation engine (`PricingService`) supporting:
  - Base page rates: B&W (₹1.00 / 100 paise) vs Color (₹5.00 / 500 paise)
  - Paper sizes: A4 (1.0x), A3 (2.0x), Letter (1.0x)
  - Single-sided vs Double-sided printing (20% sheet discount on 2-sided sheets)
  - Arbitrary positive copies multiplier
  - Grounded in integer paise to avoid IEEE-754 floating point rounding errors
- Live quote endpoint (`POST /pricing/quote`) returning full cost breakdown
- Order creation endpoint (`POST /orders`) validating referenced document, print options, and persisting order in DynamoDB according to DATA-001 (`PK: ORDER#{order_id}` / `SK: ORDER#{order_id}`)
- Order retrieval endpoint (`GET /orders/{order_id}`)
- Validation error handling with structured `{ "error": { "code": "...", "message": "..." } }`
- DynamoDB single-table persistence with recursive Decimal conversion for float attributes
- Student UI integration in `app/static/index.html` with:
  - Step 2 print configuration form
  - Live quote preview dynamically updating on any input change
  - Order submission and formatted order summary
  - Direct DynamoDB order lookup by Order ID
- Comprehensive automated test suite: 46/46 tests passing
- Strict compliance with DATA-001 canonical order schema (`payment_status: PENDING`, `document_key`, `document_name`, `document_content_type`, `document_size`, `color_mode`, `paper_size`, `copies`, `sidedness`, `scheduled_time`)

## Milestone 3 — Vertical Slice 3: Simulated Payment
**Status:** ✅ Complete  
**Date:** 2026-09-12

### What was delivered
- Simulated payment processing engine (`PaymentService`) supporting:
  - Deterministic simulation only (SUCCESS or FAILURE) without external gateways or SDKs
  - Authoritative amount derivation from persisted order pricing breakdown (recalculated/validated on backend; client payment state never trusted)
  - Validation of order eligibility (only `PENDING_PAYMENT` and `PAYMENT_FAILED` orders can be paid)
  - Duplicate payment rejection (`ORDER_ALREADY_PAID` with 400 Bad Request) on already paid orders
  - Retry capability on payment failure transitioning to `PAID` on subsequent success
- DynamoDB single-table persistence according to DATA-001:
  - Payment record: `PK: ORDER#{order_id}` / `SK: PAYMENT#{payment_id}`
  - Fast lookup aliases: `PK: ORDER#{order_id}` / `SK: PAYMENT#{order_id}` and `PK: PAYMENT#{payment_id}` / `SK: PAYMENT#{payment_id}`
  - Atomic order state update (`update_order_payment_state`):
    - On SUCCESS: `payment_status: "SUCCESS"`, `status: "PAID"`, `payment_id: payment_id`
    - On FAILURE: `payment_status: "FAILED"`, `status: "PAYMENT_FAILED"`, `payment_id: payment_id`
- REST API endpoints in `app/api/payments.py` (mounted at `/orders` router):
  - `POST /orders/{order_id}/payment/simulate`
  - `GET /orders/{order_id}/payment`
- Student UI integration in `app/static/index.html`:
  - Step 3 Simulated Payment card with auto-population of Order ID from Step 2
  - Toggle between "Simulate SUCCESS" and "Simulate FAILURE"
  - Interactive payment execution button with live feedback
  - Formatted payment result summary (Payment ID, Reference, charged amount, order status, DynamoDB keys)
  - Dedicated DynamoDB payment verification lookup section (`GET /orders/{order_id}/payment`)
- Comprehensive automated test suite in `tests/test_payments.py`: 18 passing tests (64/64 total project tests passing)

---

## Milestone 4 — Vertical Slice 4: Token + Queue + ETA
**Status:** ✅ Complete  
**Date:** 2026-09-12

### What was delivered
- Concurrency-safe atomic token generator (`DynamoDBRepository.generate_next_token`):
  - Uses atomic DynamoDB `ADD` counter on dedicated item (`PK: COUNTER#TOKEN`, `SK: COUNTER#TOKEN`)
  - Issues clean, sequential, human-friendly tokens (`X-101`, `X-102`, `X-103`...) with zero duplicate or collision risk
- Operational Queue Admission engine (`QueueService.admit_to_queue`):
  - Strict admission guard: Only successfully paid orders (`status == 'PAID'` and `payment_status == 'SUCCESS'`) can enter the queue
  - Rejects unpaid (`PENDING_PAYMENT`) and failed (`PAYMENT_FAILED`) orders with HTTP 400 (`ORDER_NOT_PAID`)
  - Idempotent duplicate admission rejection with HTTP 400 (`ORDER_ALREADY_QUEUED`) preventing multiple tokens or queue entries
  - Transitions order status to `QUEUED`
- Deterministic ETA Engine (`QueueService.calculate_job_duration_seconds`):
  - 100% backend-calculated ETA (never client-calculated)
  - Evaluates active queue depth and job complexity: base setup time (60s) + pages printed per active job ahead (B&W: 2s/page, Color: 5s/page)
  - Computes exact `queue_position` (1-based), `estimated_wait_seconds`, `estimated_wait_minutes`, and ISO `estimated_completion_at`
- DynamoDB single-table persistence:
  - Atomic conditional update on order record (`PK: ORDER#{order_id}`, `SK: ORDER#{order_id}`)
  - Active operational queue partition (`PK: QUEUE#ACTIVE`, `SK: ORDER#{order_id}`) storing real-time print metadata for staff processing
- REST API endpoints in `app/api/queue.py` (mounted under `/orders` router):
  - `POST /orders/{order_id}/queue` — admits paid order, issues token, returns queue position and ETA
  - `GET /orders/{order_id}/queue` — returns live queue position, updated ETA, and active queue length
- Student UI integration in `app/static/index.html`:
  - Step 4 Operational Queue & Token card with auto-advance from successful Step 3 payment
  - Prominent, luminous Token Number display (`X-101`) in monospace hero banner
  - Live Queue Position badge ("You are #1 in line")
  - Real-time Estimated Ready Time (ETA) and remaining minutes
  - Dedicated "Refresh Live ETA & Position" button (`GET /orders/{order_id}/queue`)
  - Direct DynamoDB queue verification inspection tool
- Comprehensive automated test suite in `tests/test_queue.py`:
  - 13 passing tests covering sequential token generation, admission guards, duplicate admission rejection, queue position across multiple orders, deterministic ETA accuracy, and DynamoDB persistence
  - 77/77 total project tests passing

---

## Vertical Slice 5: Staff Processing (Completed)
**Date:** 2026-09-12

### What was delivered
- Authoritative Backend State Machine & Lifecycle Transitions:
  - Strict lifecycle transitions: `QUEUED` -> `PROCESSING` (Accept) or `REJECTED` (with mandatory reason)
  - `PROCESSING` -> `READY` (marked ready for collection; automatically removes order from active print queue)
  - `READY` -> `COMPLETED` (order collected/finished)
  - Disallows invalid transitions with HTTP 400 (`INVALID_STATE_TRANSITION`)
  - Enforces mandatory non-empty formal rejection reason with HTTP 400 (`REJECTION_REASON_REQUIRED`)
- Staff Service & Endpoints (`app/api/staff.py` mounted at `/staff` and `/orders`):
  - `GET /staff/orders` & `GET /staff/queue` — lists active queue orders with document metadata and S3 presigned URL
  - `POST /staff/orders/{order_id}/accept` & `POST /orders/{order_id}/process` — transitions order to `PROCESSING`
  - `POST /staff/orders/{order_id}/reject` — transitions order to `REJECTED` with formal reason, removing it from active queue
  - `POST /staff/orders/{order_id}/ready` — transitions order to `READY`, removing it from `PK: QUEUE#ACTIVE`
  - `POST /staff/orders/{order_id}/complete` — transitions order to `COMPLETED`
- S3 Secure Document Access:
  - Staff can securely inspect documents via time-limited private S3 presigned URLs (`S3Repository.generate_presigned_url`)
- Dynamic Operational Queue Management:
  - When an order transitions to `READY` or `REJECTED`, it is removed from `PK: QUEUE#ACTIVE`
  - Subsequent orders dynamically move up in line (e.g. #2 becomes #1) with reduced queue depth and recalculated ETA
- Student Tracking Visibility:
  - Student status checks (`GET /orders/{order_id}/queue` and `GET /orders/{order_id}`) immediately reflect `PROCESSING`, `READY`, `COMPLETED`, and `REJECTED` (including rejection reason)
- Staff Operations Dashboard UI in `app/static/index.html`:
  - Dedicated Portal Navigation tab switcher (`Student Ordering Portal` vs `Staff Operations Portal`)
  - Filter by status (`ACTIVE`, `QUEUED`, `PROCESSING`, `READY`, `COMPLETED`, `REJECTED`, `ALL`)
  - Document inspection button opening presigned S3 URL in new tab
  - One-click Accept, Ready, Complete action buttons
  - Interactive Rejection Modal requiring non-empty formal justification
  - Live active count badge and auto-detection on `/staff` route
- Comprehensive automated test suite in `tests/test_staff.py`:
  - 32 passing tests covering listing with presigned URLs, accept, reject, ready, complete, invalid transitions, dynamic queue position shift, student tracking visibility, missing reason validation, endpoint aliases, and UI serving
  - 113/113 total project tests passing

---

## Vertical Slice 6: Complete Student Tracking + History ✅
- DynamoDB Single-Table Student Order Indexing:
  - Partitioned student order mapping `PK: STUDENT#{student_id}`, `SK: ORDER#{created_at}#{order_id}`
  - Authoritative repository query `get_orders_by_student_id(student_id: str) -> list[Order]` returning orders sorted chronologically descending
  - Resilient fallback scan with student_id filter for test robustness
- Domain & Schemas (`app/schemas/history.py`):
  - `TimelineEvent`: Ordered lifecycle events with UTC timestamps, status (`COMPLETED`, `CURRENT`, `FAILED`), and event-specific metadata (token, queue position, ETA, rejection reason, payment ID)
  - `OrderTimelineResponse`: Comprehensive status timeline inspection schema
  - `PaymentReceipt`: Structured payment details and audit record
  - `StudentOrderHistoryItem`: Complete order record including print config, pricing breakdown, payment receipt, live queue position, ETA, rejection reason, full status timeline, and fresh presigned S3 download URL
- Authoritative History Service (`app/services/history_service.py`):
  - Strictly isolated to requesting student (zero cross-student data leakage)
  - Returns `[]` when student has no history
  - Dynamic live queue position and ETA integration for active orders
  - Generates time-limited presigned S3 GET URLs for secure document re-access/download
- REST API Endpoints:
  - `GET /orders?student_id={student_id}`: Primary query endpoint for student order history
  - `GET /students/{student_id}/orders`: Canonical student-scoped REST resource endpoint
  - `GET /orders/{order_id}/timeline`: Standalone lifecycle timeline inspection endpoint
  - Route handlers for `/tracking` and `/history` serving student tracking portal
  - Strict 400 `STUDENT_ID_REQUIRED` validation when `student_id` is omitted
- Student Portal UI (`app/static/index.html`):
  - Dedicated "Order Tracking & History (Slice 6)" portal tab in header navigation
  - Student ID input with instant search and enter-key submission
  - Filter pills: All, Active / In Queue, Ready for Pickup, Completed, Rejected / Failed
  - Visual status timeline stepper with chronological event icons, timestamps, status badges, and descriptions
  - 🔗 Re-download Document action button opening secure presigned S3 URL
  - Simulated payment receipt cards with transaction references and failure details
  - Live queue position and completion ETA banner for active print jobs
  - Prominent operator rejection reason callout box for rejected orders
  - Direct "Track Order in History" jump link from Step 4 Queue view
- Automated Test Suite (`tests/test_history.py`):
  - 13 comprehensive tests covering empty history `[]`, missing student_id rejection (400), cross-student isolation, chronological sorting, fresh presigned S3 URLs, payment receipts, payment failures, queue token & live position, operator rejection reasons, complete status timeline across all 8 lifecycle states, 404 handling, endpoint alias parity, and static UI routes
  - 126/126 total project tests passing

---

### Vertical slices planned (awaiting approval)
1. Document Upload: Student UI → FastAPI → S3 → DynamoDB → UI ✅
2. Print Config + Order Creation: → validation → pricing → DynamoDB ✅
3. Simulated Payment: → SUCCESS/FAILURE → DynamoDB ✅
4. Token + Queue + ETA: → token/queue/ETA → DynamoDB ✅
5. Staff Processing: Staff UI → accept/reject/process/READY ✅
6. Student Tracking + History: → history/timeline/presigned S3/UI ✅
7. Full End-to-End Validation (Awaiting approval)
8. Dockerization
9. AWS Deployment (guided)
