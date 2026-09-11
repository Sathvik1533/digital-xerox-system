"""
FastAPI application entry point.

Architecture note:
    This is a MODULAR MONOLITH — one process, one codebase,
    one deployable unit. Modules are separated logically, not
    as separate services.

    Request flow:
        HTTP request → API router → Service → Repository → AWS (DynamoDB/S3)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.health import router as health_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Digital Xerox & Stationery Ordering System. "
        "Modular monolith backend with FastAPI + DynamoDB + S3."
    ),
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# CORS — restrict in production to your actual frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers — each feature area gets its own router
app.include_router(health_router, tags=["Health"])

# Placeholder: future routers registered here as slices are implemented
# app.include_router(orders_router, prefix="/orders", tags=["Orders"])
# app.include_router(documents_router, prefix="/orders", tags=["Documents"])
# app.include_router(payments_router, prefix="/orders", tags=["Payments"])
# app.include_router(queue_router, prefix="/queue", tags=["Queue"])
# app.include_router(pricing_router, prefix="/pricing", tags=["Pricing"])
# app.include_router(staff_router, prefix="/staff", tags=["Staff"])
