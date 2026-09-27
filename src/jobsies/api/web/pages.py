from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from loguru import logger
from starlette.requests import Request

from jobsies.api.web.components.documentation import DOCUMENTATION_PAGES
from jobsies.settings import get_templates

router = APIRouter(tags=["Web Pages"])
templates = get_templates()


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


@router.get("/documentation", response_class=HTMLResponse)
async def page_documentation(request: Request, page: str = "about") -> HTMLResponse:
    """Render the jobsie documentation full page."""
    if page not in DOCUMENTATION_PAGES:
        raise HTTPException(status_code=404, detail="Documentation page not found")

    logger.debug("GET documentation.html")
    return templates.TemplateResponse(
        request=request,
        name="documentation.html",
        context={
            "active_page": "documentation",
            "documentation_pages": DOCUMENTATION_PAGES,
            "selected_documentation_page": page,
        },
    )
