"""
Test configuration and fixtures.
Uses pytest + moto (AWS mocking library) so tests never hit real AWS.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    with TestClient(app) as c:
        yield c
