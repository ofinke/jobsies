import pytest
from fastapi.testclient import TestClient
from jobsies.api.web import pages
from starlette.requests import Request
from starlette.responses import HTMLResponse


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/", ("results.html", "results", None)),
        ("/definition", ("definition.html", "definitions", None)),
        ("/worker", ("worker.html", "worker", None)),
        ("/trends", ("trends.html", "trends", None)),
        ("/documentation", ("documentation.html", "documentation", "about")),
    ],
)
def test_page_endpoint_renders_expected_template_and_active_page(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    expected: tuple[str, str, str | None],
) -> None:
    """Test each page route selects its template and active navigation page."""
    rendered: list[tuple[Request, str, dict[str, object]]] = []

    def render_template(*, request: Request, name: str, context: dict[str, object]) -> HTMLResponse:
        rendered.append((request, name, context))
        return HTMLResponse("rendered page")

    monkeypatch.setattr(pages.templates, "TemplateResponse", render_template)

    response = client.get(path)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert len(rendered) == 1
    assert rendered[0][1] == expected[0]
    assert rendered[0][2]["active_page"] == expected[1]

    if expected[2] is not None:
        assert rendered[0][2]["selected_documentation_page"] == expected[2]


@pytest.mark.parametrize("path", ["/missing", "/documentation?page=missing"])
def test_page_endpoints_reject_unknown_page_paths(client: TestClient, path: str) -> None:
    """Test page routes do not silently accept unknown or trailing-slash paths."""
    response = client.get(path)

    assert response.status_code == 404
