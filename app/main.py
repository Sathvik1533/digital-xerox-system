"""
FastAPI application entry point.

Architecture note:
    This is a MODULAR MONOLITH — one process, one codebase,
    one deployable unit. Modules are separated logically, not
    as separate services.

    Request flow:
        HTTP request → API router → Service → Repository → AWS (DynamoDB/S3)
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.api.health import router as health_router
from app.api.documents import router as documents_router
from app.api.orders import router as orders_router
from app.api.pricing import router as pricing_router

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

# Static files and Student UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
@app.get("/upload", include_in_schema=False)
def serve_student_ui():
    """Serve the student document upload UI."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": f"Welcome to {settings.app_name}"}


# Routers — each feature area gets its own router
app.include_router(health_router, tags=["Health"])
app.include_router(documents_router, prefix="/documents", tags=["Documents"])
app.include_router(pricing_router, prefix="/pricing", tags=["Pricing"])
app.include_router(orders_router, prefix="/orders", tags=["Orders"])

# Placeholder: future routers registered here as slices are implemented
# app.include_router(payments_router, prefix="/orders", tags=["Payments"])
# app.include_router(queue_router, prefix="/queue", tags=["Queue"])
# app.include_router(staff_router, prefix="/staff", tags=["Staff"])
