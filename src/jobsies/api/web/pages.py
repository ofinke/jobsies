from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

router = APIRouter(tags=["Web Pages"])
templates = Jinja2Templates(directory="src/jobsies/templates")


@router.get("/", response_class=HTMLResponse)
async def page_results(request: Request) -> HTMLResponse:
    """Render the index landing page."""
    return templates.TemplateResponse(
        request=request,
        name="results.html",
    )


@router.get("/definition", response_class=HTMLResponse)
async def page_definitions(request: Request) -> HTMLResponse:
    """Render the jobsie definitions full page."""
    return templates.TemplateResponse(
        request=request,
        name="definition.html",
    )
