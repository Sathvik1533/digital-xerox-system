"""Health check endpoint."""
from fastapi import APIRouter
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check() -> dict:
    """
    Health endpoint for load balancer and deployment checks.
    ECS will call this to verify the container is healthy.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }
