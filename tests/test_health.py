"""
Phase 0 tests — verifies the application foundation.
Exit criteria from Notion roadmap: application starts and /health passes.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_health_endpoint(client: TestClient):
    """Health endpoint must return 200 with expected fields."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "environment" in data


def test_docs_available_in_development(client: TestClient):
    """Swagger docs should be accessible in development."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema(client: TestClient):
    """OpenAPI schema must be generated correctly."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Digital Xerox & Stationery Ordering System"
