from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from jobsies.database.handler import get_db_handler
from jobsies.fastapi_app import app
from jobsies.jobs import ExampleJobsie
from jobsies.schemas.tables import TableJobsiesDefinition
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture(autouse=True)
def test_db() -> Generator[None]:
    """Sets up an in-memory database for testing and overrides the database handler engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(bind=engine)

    handler = get_db_handler()
    original_engine = handler.engine
    handler.engine = engine

    with Session(engine) as session:
        definition = TableJobsiesDefinition(
            name="Initial Test Config",
            subclass_name="ExampleJobsie",
            cron="0 * * * *",
            retention="0",
            input_kwargs={},
            output_vars=ExampleJobsie.output_schema.model_json_schema(),
            output_monitoring={},
            enabled=True,
        )
        session.add(definition)
        session.commit()

    yield

    handler.engine = original_engine


@pytest.fixture
def client() -> TestClient:
    """Returns a TestClient instance for the FastAPI application."""
    return TestClient(app)


def test_index_page(client: TestClient) -> None:
    """Tests GET / returns full index HTML page with sidebar."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text
    assert "<!DOCTYPE html>" in html
    assert "Jobsies" in html
    assert "sidebar" in html


def test_definitions_page_full_load(client: TestClient) -> None:
    """
    Tests GET /definition returns full HTML page skeleton without table data.

    The definitions table is loaded asynchronously via HTMX after page load.
    """
    response = client.get("/definition")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text
    assert "<!DOCTYPE html>" in html
    assert "Jobsies - Definitions" in html
    assert "sidebar" in html
    assert "definitions-table" in html
    assert 'hx-get="/definition/table"' in html
    assert 'hx-trigger="load"' in html
    assert "dialog-container" in html


def test_definitions_table_component_partial_load(client: TestClient) -> None:
    """Tests GET /definition/table returns only partial table HTML."""
    response = client.get("/definition/table")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text
    assert "<!DOCTYPE html>" not in html
    assert "sidebar" not in html
    assert "definitions-table" in html
    assert "Initial Test Config" in html
    assert "ExampleJobsie" in html


def test_definitions_create_dialog_get(client: TestClient) -> None:
    """Tests GET /definition/create returns the dialog with form and subclass selector."""
    response = client.get("/definition/create")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text
    assert "<dialog" in html
    assert "Create Jobsie Definition" in html
    assert "subclass_name" in html
    assert "ExampleJobsie" in html
    assert "input_kwargs" in html
    assert 'name="cron"' in html
    assert 'name="retention"' in html
    assert 'name="enabled"' in html


def test_definitions_create_post_success(client: TestClient) -> None:
    """Tests POST /definition/create creates a new definition and returns updated table."""
    form_data = {
        "name": "New Test Jobsie",
        "subclass_name": "ExampleJobsie",
        "cron": "*/5 * * * *",
        "retention": "7d",
        "input_kwargs": '{"test_key": "test_val"}',
        "enabled": "on",
    }
    response = client.post("/definition/create", data=form_data)
    assert response.status_code == 200
    assert response.headers.get("HX-Trigger") == "definition-created"
    html = response.text
    assert "definitions-table" in html
    assert "New Test Jobsie" in html
    assert "ExampleJobsie" in html


def test_definitions_create_post_invalid_json(client: TestClient) -> None:
    """Tests POST /definition/create with invalid JSON in input_kwargs returns 422 and renders error."""
    form_data = {
        "name": "Invalid JSON Jobsie",
        "subclass_name": "ExampleJobsie",
        "cron": "*/5 * * * *",
        "retention": "0",
        "input_kwargs": "{invalid_json",
        "enabled": "on",
    }
    response = client.post("/definition/create", data=form_data)
    assert response.status_code == 422
    html = response.text
    assert "form-errors" in html
    assert "alert-error" in html
    assert "Invalid input_kwargs JSON" in html
    assert "{invalid_json" in html


def test_definitions_create_post_invalid_cron(client: TestClient) -> None:
    """Tests POST /definition/create with invalid cron expression returns 422 and renders error."""
    form_data = {
        "name": "Invalid Cron Jobsie",
        "subclass_name": "ExampleJobsie",
        "cron": "not-a-cron",
        "retention": "0",
        "input_kwargs": "{}",
        "enabled": "on",
    }
    response = client.post("/definition/create", data=form_data)
    assert response.status_code == 422
    html = response.text
    assert "form-errors" in html
    assert "alert-error" in html
    assert "Invalid cron expression" in html


def test_definitions_update_post_invalid_json(client: TestClient) -> None:
    """Tests PATCH /definition/{id} with invalid JSON in input_kwargs returns 422 and renders error."""
    form_data = {
        "name": "Initial Test Config",
        "cron": "0 * * * *",
        "retention": "0",
        "input_kwargs": "{invalid_json_kwargs",
        "enabled": "on",
    }
    response = client.patch("/definition/1", data=form_data)
    assert response.status_code == 422
    html = response.text
    assert "form-errors" in html
    assert "alert-error" in html
    assert "Invalid input_kwargs JSON" in html
    assert "{invalid_json_kwargs" in html


def test_definitions_update_post_invalid_cron(client: TestClient) -> None:
    """Tests PATCH /definition/{id} with invalid cron expression returns 422 and renders error."""
    form_data = {
        "name": "Initial Test Config",
        "cron": "not-a-valid-cron",
        "retention": "0",
        "input_kwargs": "{}",
        "enabled": "on",
    }
    response = client.patch("/definition/1", data=form_data)
    assert response.status_code == 422
    html = response.text
    assert "form-errors" in html
    assert "alert-error" in html
    assert "Invalid cron expression" in html


def test_definitions_update_dialog_get(client: TestClient) -> None:
    """Tests GET /definition/{id}/update returns update dialog with prefilled data."""
    response = client.get("/definition/1/update")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text
    assert "<dialog" in html
    assert "Update Jobsie Definition" in html
    assert 'value="Initial Test Config"' in html
    assert 'name="enabled"' in html


def test_definitions_update_post_disable(client: TestClient) -> None:
    """Tests PATCH /definition/{id} with unchecked enabled disables the definition."""
    form_data = {
        "name": "Updated Test Config",
        "subclass_name": "ExampleJobsie",
        "cron": "0 * * * *",
        "retention": "0",
        "input_kwargs": "{}",
    }
    response = client.patch("/definition/1", data=form_data)
    assert response.status_code == 200
    assert response.headers.get("HX-Trigger") == "definition-updated"
    html = response.text
    assert "Disabled" in html


def test_definitions_update_post_enable(client: TestClient) -> None:
    """Tests PATCH /definition/{id} with checked enabled enables the definition."""
    form_data = {
        "name": "Updated Test Config",
        "subclass_name": "ExampleJobsie",
        "cron": "0 * * * *",
        "retention": "0",
        "input_kwargs": "{}",
        "enabled": "on",
    }
    response = client.patch("/definition/1", data=form_data)
    assert response.status_code == 200
    assert response.headers.get("HX-Trigger") == "definition-updated"
    html = response.text
    assert "Enabled" in html
