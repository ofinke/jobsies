from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jobsies.schemas.enums import JobsieDefinitionStatus
from jobsies.schemas.tables import TableJobsiesDefinition
from jobsies.services import DefinitionService


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
    """Tests execution endpoints return 404 for a non-existent definition."""
    response = client.post("/api/v1/jobsie/execute/999")
    assert response.status_code == 404


def test_execute_unavailable_jobsie_returns_conflict(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tests execution endpoints reject definitions marked unavailable."""
    definition = TableJobsiesDefinition(
        id=1,
        name="Unavailable test jobsie",
        subclass_name="ExampleJobsie",
        cron="0 * * * *",
        input_kwargs={},
        output_vars={},
        output_monitoring={},
        status=JobsieDefinitionStatus.UNAVAILABLE,
    )
    monkeypatch.setattr(DefinitionService, "get_definition", lambda _self, _id: definition)

    response = client.post("/api/v1/jobsie/execute/1")

    assert response.status_code == 409
    assert "is unavailable" in response.json()["detail"]


def test_web_execute_unavailable_jobsie_returns_error_status_bar(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tests the HTMX execution endpoint renders an error status bar for unavailable definitions."""
    definition = TableJobsiesDefinition(
        id=1,
        name="Unavailable test jobsie",
        subclass_name="ExampleJobsie",
        cron="0 * * * *",
        input_kwargs={},
        output_vars={},
        output_monitoring={},
        status=JobsieDefinitionStatus.UNAVAILABLE,
    )
    apply_async = MagicMock()
    monkeypatch.setattr(DefinitionService, "get_definition", lambda _self, _id: definition)
    monkeypatch.setattr(
        "jobsies.api.web.components.definition.wrapper_run_dynamic_jobsie.apply_async",
        apply_async,
    )

    response = client.post("/definition/execute/1")

    assert response.status_code == 200
    assert "status-error" in response.text
    assert "is unavailable" in response.text
    apply_async.assert_not_called()


def test_web_execute_missing_jobsie_returns_error_status_bar(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tests the HTMX execution endpoint renders an error status bar for missing definitions."""
    monkeypatch.setattr(DefinitionService, "get_definition", lambda _self, _id: None)

    response = client.post("/definition/execute/999")

    assert response.status_code == 200
    assert "status-error" in response.text
    assert "not found" in response.text
