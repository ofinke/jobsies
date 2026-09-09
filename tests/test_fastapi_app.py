import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from jobsies.api.health import router as health_router
from jobsies.api.v1 import jobsies_definition_router, jobsies_execution_router, jobsies_output_router
from jobsies.api.web import definition_component_router, results_component_router, web_pages_router
from jobsies.fastapi_app import app
from starlette.routing import Mount


@pytest.fixture
def client() -> TestClient:
    """Return a test client for the FastAPI application."""
    return TestClient(app)


@pytest.mark.parametrize(
    "router",
    [
        health_router,
        jobsies_definition_router,
        jobsies_output_router,
        jobsies_execution_router,
        web_pages_router,
        definition_component_router,
        results_component_router,
    ],
)
def test_all_router_routes_are_included(router: APIRouter) -> None:
    """Verify that every application router is included exactly on the app."""
    included_routers = [route.original_router for route in app.routes if hasattr(route, "original_router")]

    assert router in included_routers


def test_docs_url_is_configured(client: TestClient) -> None:
    """Verify that the configured docs URL is available at /docs."""
    assert app.docs_url == "/docs"

    response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text


def test_static_files_are_mounted(client: TestClient) -> None:
    """Verify that static files are mounted at /static and can be served."""
    static_mounts = [route for route in app.routes if isinstance(route, Mount) and route.name == "static"]

    assert len(static_mounts) == 1
    assert static_mounts[0].path == "/static"
    assert client.get("/static/css/style.css").status_code == 200


def test_static_mount_does_not_expose_files_outside_directory(client: TestClient) -> None:
    """Verify that path traversal cannot access files outside the static directory."""
    response = client.get("/static/%2E%2E/fastapi_app.py")

    assert response.status_code == 404
