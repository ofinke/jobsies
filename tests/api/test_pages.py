import pytest
from fastapi.testclient import TestClient
from jobsies.api.web import pages
from starlette.requests import Request
from starlette.responses import HTMLResponse


@pytest.mark.parametrize(
    ("path", "template_name", "active_page"),
    [
        ("/", "results.html", "results"),
        ("/definition", "definition.html", "definitions"),
        ("/worker", "worker.html", "worker"),
        ("/trends", "trends.html", "trends"),
        ("/about", "about.html", "about"),
    ],
)
def test_page_endpoint_renders_expected_template_and_active_page(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    template_name: str,
    active_page: str,
) -> None:
    """Test each page route selects its template and active navigation page."""
    rendered: list[tuple[Request, str, dict[str, object]]] = []

    def render_template(
        *, request: Request, name: str, context: dict[str, object]
    ) -> HTMLResponse:
        rendered.append((request, name, context))
        return HTMLResponse("rendered page")

    monkeypatch.setattr(pages.templates, "TemplateResponse", render_template)
    monkeypatch.setattr(pages, "_load_about_docs", lambda: "about content")

    response = client.get(path)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert len(rendered) == 1
    assert rendered[0][1] == template_name
    assert rendered[0][2]["active_page"] == active_page


@pytest.mark.parametrize("path", ["/missing"])
def test_page_endpoints_reject_unknown_page_paths(client: TestClient, path: str) -> None:
    """Test page routes do not silently accept unknown or trailing-slash paths."""
    response = client.get(path)

    assert response.status_code == 404
