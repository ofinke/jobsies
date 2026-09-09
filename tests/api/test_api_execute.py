from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def seed_database(seeded_definition: None) -> None:
    """Seeds the initial definition for API tests."""


@patch("jobsies.api.v1.jobsies.wrapper_run_dynamic_jobsie.apply_async")
def test_execute_jobsie_post_success(mock_apply_async: MagicMock, client: TestClient) -> None:
    """Tests POST /api/v1/jobsie/execute/{id} calls apply_async on wrapper_run_dynamic_jobsie."""
    mock_task = MagicMock()
    mock_task.id = "mocked-task-uuid-123"
    mock_apply_async.return_value = mock_task

    response = client.post("/api/v1/jobsie/execute/1")
    assert response.status_code == 200
    data = response.json()
    assert data["definition_id"] == 1
    assert data["task_id"] == "mocked-task-uuid-123"
    mock_apply_async.assert_called_once_with(args=[1])


@patch("jobsies.api.v1.jobsies.wrapper_run_dynamic_jobsie.apply_async")
def test_execute_jobsie_get_success(mock_apply_async: MagicMock, client: TestClient) -> None:
    """Tests GET /api/v1/jobsie/execute/{id} also triggers execution."""
    mock_task = MagicMock()
    mock_task.id = "mocked-task-uuid-456"
    mock_apply_async.return_value = mock_task

    response = client.get("/api/v1/jobsie/execute/1")
    assert response.status_code == 200
    data = response.json()
    assert data["definition_id"] == 1
    assert data["task_id"] == "mocked-task-uuid-456"
    mock_apply_async.assert_called_once_with(args=[1])


def test_execute_jobsie_not_found(client: TestClient) -> None:
    """Tests /api/v1/jobsie/execute/{id} with non-existent ID returns 500."""
    response = client.post("/api/v1/jobsie/execute/999")
    assert response.status_code == 500
