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
- Comprehensive automated test suite in `tests/test_payments.py`: 13 passing tests (59/59 total project tests passing)

---

### Vertical slices planned (awaiting approval)
1. Document Upload: Student UI → FastAPI → S3 → DynamoDB → UI ✅
2. Print Config + Order Creation: → validation → pricing → DynamoDB ✅
3. Simulated Payment: → SUCCESS/FAILURE → DynamoDB ✅
4. Token + Queue + ETA: → token/queue/ETA → DynamoDB (Awaiting approval)
5. Staff Processing: Staff UI → accept/reject/process/READY
6. Student Tracking + History
7. Full End-to-End Validation
8. Dockerization
9. AWS Deployment (guided)
