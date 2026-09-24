import functools
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from justhtml import JustHTML
from loguru import logger
from mistune import create_markdown
from starlette.requests import Request

from jobsies.settings import get_templates

router = APIRouter(tags=["Web Pages"])
templates = get_templates()


@functools.cache
def _load_about_docs() -> str:
    """Load the about page documentation and convert it to an HTML fragment."""
    about_path = Path(__file__).resolve().parents[4] / "docs" / "about.md"
    about_markdown = about_path.read_text(encoding="utf-8")
    about_html = create_markdown()(about_markdown)
    return JustHTML(about_html, fragment=True).to_html()


@router.get("/", response_class=HTMLResponse)
async def page_output(request: Request) -> HTMLResponse:
    """Render the index landing page."""
    logger.debug("GET results.html")
    return templates.TemplateResponse(
        request=request,
        name="results.html",
        context={"active_page": "results"},
    )


@router.get("/definition", response_class=HTMLResponse)
async def page_definitions(request: Request) -> HTMLResponse:
    """Render the jobsie definitions full page."""
    logger.debug("GET definition.html")
    return templates.TemplateResponse(
        request=request,
        name="definition.html",
        context={"active_page": "definitions"},
    )


@router.get("/worker", response_class=HTMLResponse)
async def page_worker(request: Request) -> HTMLResponse:
    """Render the jobsie worker full page."""
    logger.debug("GET worker.html")
    return templates.TemplateResponse(
        request=request,
        name="worker.html",
        context={"active_page": "worker"},
    )


@router.get("/trends", response_class=HTMLResponse)
async def page_trends(request: Request) -> HTMLResponse:
    """Render the jobsie trends full page."""
    logger.debug("GET trends.html")
    return templates.TemplateResponse(
        request=request,
        name="trends.html",
        context={"active_page": "trends"},
    )


@router.get("/about", response_class=HTMLResponse)
async def page_about(request: Request) -> HTMLResponse:
    """Render the jobsie about full page."""
    logger.debug("GET about.html")
    return templates.TemplateResponse(
        request=request,
        name="about.html",
        context={
            "active_page": "about",
            "about_content": _load_about_docs(),
        },
    )
