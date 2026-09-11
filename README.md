# Digital Xerox & Stationery Ordering System

A **modular monolith** backend for the Digital Xerox & Stationery Ordering System — built for the AWS Cloud Trek 2026 hackathon.

## Architecture

```
Frontend (React/HTML)
    ↓
FastAPI (Modular Monolith)
    ↓
Service / Business Logic Layer
    ↓
Repository / AWS Integration Layer
    ↓
Amazon DynamoDB (metadata + operational state)
Amazon S3 (document storage)
```

## AWS Services

| Service | Role |
|---|---|
| **Amazon S3** | Stores uploaded document files |
| **Amazon DynamoDB** | Stores orders, metadata, queue, payment state |
| **Amazon ECR** | Container image registry |
| **Amazon ECS** | Container runtime (Fargate) |
| **Amazon CloudWatch** | Logging & observability |
| **AWS IAM** | Least-privilege access control |

## Core Student Workflow

1. Upload document → S3 stores file, DynamoDB stores metadata
2. Specify print requirements → FastAPI validates
3. Price calculated → DynamoDB stores price
4. Simulated payment (SUCCESS/FAILURE deterministic) → DynamoDB persists result
5. Successful payment → unique token generated → order enters queue
6. Student can view queue position and ETA

## Core Staff Workflow

1. View incoming orders → accept or reject
2. Process accepted orders → update status
3. Mark order READY → student notified
4. Complete order

## Project Structure

```
app/
├── api/          # FastAPI route handlers (HTTP endpoints)
├── core/         # Config, settings, application startup
├── models/       # Domain models (Order, Document, Payment, Queue)
├── schemas/      # Pydantic request/response schemas
├── services/     # Business logic (pricing, payment sim, queue, ETA)
├── repositories/ # AWS integration (DynamoDB, S3)
tests/            # Unit and integration tests
scripts/          # Utility scripts (table setup, etc.)
infra/            # Docker, ECS task definitions
```

## Payment

Payment is **simulation-only**. No external gateways (Razorpay, Stripe, etc.) are implemented.
Simulated payment produces deterministic SUCCESS or FAILURE and is fully persisted.

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload

# Health check
curl http://localhost:8000/health

# Run tests
pytest tests/
```

## Environment Variables

```
AWS_REGION=ap-south-1
DYNAMODB_TABLE_NAME=digital-xerox-orders
S3_BUCKET_NAME=digital-xerox-documents
ENVIRONMENT=development
```

Never hard-code AWS credentials. Use IAM roles in production.
