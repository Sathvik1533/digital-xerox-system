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
- `pyproject.toml` with ruff linter config

### Exit criteria met (from Notion roadmap)
> Application starts locally and `/health` passes. ✅

### Architecture confirmed from Notion specs
- **Backend:** FastAPI modular monolith
- **Database:** Amazon DynamoDB (orders, metadata, queue, payment state)
- **Document storage:** Amazon S3 (actual files only)
- **Container:** Docker → ECR → ECS (Fargate)
- **Observability:** CloudWatch
- **Access:** IAM roles (least privilege)
- **Payment:** Simulation-only (deterministic SUCCESS/FAILURE)
- **AI/Bedrock:** Not yet — after core workflow is stable

### Vertical slices planned (awaiting approval)
1. Document Upload: Student UI → FastAPI → S3 → DynamoDB → UI
2. Print Config + Order Creation: → validation → pricing → DynamoDB
3. Simulated Payment: → SUCCESS/FAILURE → DynamoDB
4. Token + Queue + ETA: → token/queue/ETA → DynamoDB
5. Staff Processing: Staff UI → accept/reject/process/READY
6. Student Tracking + History
7. Full End-to-End Validation
8. Dockerization
9. AWS Deployment (guided)
