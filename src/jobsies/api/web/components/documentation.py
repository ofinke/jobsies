import functools
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from justhtml import JustHTML
from loguru import logger
from mistune import create_markdown

from jobsies.settings import get_templates

router = APIRouter(prefix="/documentation", tags=["Web Components"])
templates = get_templates()

DOCUMENTATION_PAGES = {
    "about": {"label": "About", "filename": "about.md"},
    "plugins": {"label": "Plugins", "filename": "plugins.md"},
    "configuration": {"label": "Configuration", "filename": "configuration.md"},
    "services": {"label": "Services", "filename": "services.md"},
}


@functools.cache
def _load_documentation(page: str = "about") -> str:
    """Load a documentation page and convert it to an HTML fragment."""
    documentation_path = Path(__file__).resolve().parents[5] / "docs" / DOCUMENTATION_PAGES[page]["filename"]
    documentation_markdown = documentation_path.read_text(encoding="utf-8")
    documentation_html = create_markdown(plugins=["table"])(documentation_markdown)
    return JustHTML(documentation_html, fragment=True).to_html()


@router.get("/content", response_class=HTMLResponse)
async def documentation_get_content(page: str = "about") -> HTMLResponse:
    """Render a documentation page partial for HTMX."""
    if page not in DOCUMENTATION_PAGES:
        raise HTTPException(status_code=404, detail="Documentation page not found")

    logger.debug(f"Endpoint executed: GET /documentation/content?page={page}")
    content = templates.get_template("components/documentation_content.html").render(
        {"documentation_content": _load_documentation(page)},
    )
    return HTMLResponse(content)
