from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def seed_database(seeded_definition: None) -> None:
    """Seeds the initial definition for API tests."""


def test_health_liveness(client: TestClient) -> None:
    """Tests GET /health/live without requiring external dependencies."""
    response = client.get("/health/live")
    response_content = response.json()

    assert response.status_code == 200
    assert response_content["status"] == "UP"


@patch("jobsies.api.health.get_redis_handler")
@patch("jobsies.api.health.get_db_handler")
def test_health_readiness_success(
    mock_get_db_handler: MagicMock,
    mock_get_redis_handler: MagicMock,
    client: TestClient,
) -> None:
    """Tests GET /health/ready reports healthy database and Redis dependencies."""
    database_handler = MagicMock()
    mock_get_db_handler.return_value = database_handler
    redis_handler = MagicMock()
    mock_get_redis_handler.return_value = redis_handler

    response = client.get("/health/ready")
    response_content = response.json()

    assert response.status_code == 200
    assert response_content["status"] == "UP"
    assert response_content["components"] == {"database": "UP", "redis": "UP"}

    database_handler.engine.connect.assert_called_once_with()
    database_handler.engine.connect.return_value.__enter__.return_value.execute.assert_called_once()
    redis_handler.client.ping.assert_called_once_with()


@patch("jobsies.api.health.get_redis_handler")
@patch("jobsies.api.health.get_db_handler")
def test_health_readiness_failure(
    mock_get_db_handler: MagicMock,
    mock_get_redis_handler: MagicMock,
    client: TestClient,
) -> None:
    """Tests GET /health/ready returns 503 when a dependency is unavailable."""
    database_handler = MagicMock()
    database_handler.engine.connect.side_effect = RuntimeError("database unavailable")
    mock_get_db_handler.return_value = database_handler
    redis_handler = MagicMock()
    redis_handler.client.ping.side_effect = RuntimeError("Redis unavailable")
    mock_get_redis_handler.return_value = redis_handler

    response = client.get("/health/ready")
    response_content = response.json()

    assert response.status_code == 503
    assert response_content["status"] == "DOWN"
    assert response_content["components"] == {"database": "DOWN", "redis": "DOWN"}
