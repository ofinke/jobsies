import pytest
from fastapi.testclient import TestClient
from jobsies.fastapi_app import app


@pytest.fixture
def client() -> TestClient:
    """Returns a TestClient instance for the FastAPI application."""
    return TestClient(app)
