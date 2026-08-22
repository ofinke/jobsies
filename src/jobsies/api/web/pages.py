from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from starlette.requests import Request

from jobsies.config import get_templates

router = APIRouter(tags=["Web Pages"])
templates = get_templates()


@router.get("/", response_class=HTMLResponse)
async def page_output(request: Request) -> HTMLResponse:
    """Render the index landing page."""
    return templates.TemplateResponse(
        request=request,
        name="results.html",
        context={"active_page": "results"},
    )


@router.get("/definition", response_class=HTMLResponse)
async def page_definitions(request: Request) -> HTMLResponse:
    """Render the jobsie definitions full page."""
    return templates.TemplateResponse(
        request=request,
        name="definition.html",
        context={"active_page": "definitions"},
    )
