import pytest
from fastapi.testclient import TestClient
from jobsies.jobs import ZalandoJobsie


@pytest.fixture(autouse=True)
def seed_database(seeded_definition: None) -> None:
    """Seeds the initial definition for API tests."""


def test_list_definitions(client: TestClient) -> None:
    """Tests GET /api/v1/jobsie/definition retrieves all definitions."""
    response = client.get("/api/v1/jobsie/definition")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == "Initial Test Config"
    assert data[0]["subclass_name"] == "ExampleJobsie"
    assert "content" in data[0]["output_vars"]["properties"]


def test_get_definition_by_id_success(client: TestClient) -> None:
    """Tests GET /api/v1/jobsie/definition/{id} with valid definition ID."""
    response = client.get("/api/v1/jobsie/definition/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Initial Test Config"


def test_get_definition_by_id_not_found(client: TestClient) -> None:
    """Tests GET /api/v1/jobsie/definition/{id} with non-existent ID returns 404."""
    response = client.get("/api/v1/jobsie/definition/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_definition_success(client: TestClient) -> None:
    """Tests POST /api/v1/jobsie/definition creates new definition and derives output_vars from subclass."""
    payload = {
        "name": "New Zalando Watcher",
        "subclass_name": "ZalandoJobsie",
        "cron": "*/10 * * * *",
        "retention": "30d",
        "input_kwargs": {"url": "https://zalando.cz/item", "size": "M"},
        "output_monitoring": {},
        "enabled": True,
    }
    response = client.post("/api/v1/jobsie/definition", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "New Zalando Watcher"
    assert data["subclass_name"] == "ZalandoJobsie"
    assert data["output_vars"] == ZalandoJobsie.output_schema.model_json_schema()
    assert "price_czk" in data["output_vars"]["properties"]


def test_create_definition_invalid_subclass(client: TestClient) -> None:
    """Tests POST /api/v1/jobsie/definition with unknown subclass returns 400."""
    payload = {
        "name": "Invalid Subclass Job",
        "subclass_name": "NonExistentJobsie",
        "cron": "0 0 * * *",
    }
    response = client.post("/api/v1/jobsie/definition", json=payload)
    assert response.status_code == 400
    assert "unknown jobsie subclass" in response.json()["detail"].lower()


def test_create_definition_invalid_cron(client: TestClient) -> None:
    """Tests POST /api/v1/jobsie/definition with invalid cron expression returns validation error."""
    payload = {
        "name": "Bad Cron Job",
        "subclass_name": "ExampleJobsie",
        "cron": "not-a-cron-expression",
    }
    response = client.post("/api/v1/jobsie/definition", json=payload)
    assert response.status_code == 422


def test_update_definition_success(client: TestClient) -> None:
    """Tests PUT /api/v1/jobsie/definition/{id} updates definition and output_vars when subclass changes."""
    payload = {
        "name": "Updated Name",
        "subclass_name": "ZalandoJobsie",
        "cron": "*/15 * * * *",
    }
    response = client.put("/api/v1/jobsie/definition/1", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Updated Name"
    assert data["subclass_name"] == "ZalandoJobsie"
    assert data["output_vars"] == ZalandoJobsie.output_schema.model_json_schema()


def test_update_definition_not_found(client: TestClient) -> None:
    """Tests PUT /api/v1/jobsie/definition/{id} with non-existent ID returns 404."""
    response = client.put("/api/v1/jobsie/definition/999", json={"name": "Nope"})
    assert response.status_code == 404


def test_delete_definition_success(client: TestClient) -> None:
    """Tests DELETE /api/v1/jobsie/definition/{id} deletes the definition."""
    response = client.delete("/api/v1/jobsie/definition/1")
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

    get_resp = client.get("/api/v1/jobsie/definition/1")
    assert get_resp.status_code == 404


def test_delete_definition_not_found(client: TestClient) -> None:
    """Tests DELETE /api/v1/jobsie/definition/{id} with non-existent ID returns 404."""
    response = client.delete("/api/v1/jobsie/definition/999")
    assert response.status_code == 404
