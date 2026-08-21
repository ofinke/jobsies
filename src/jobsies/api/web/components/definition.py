from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import ValidationError

from jobsies.schemas.api import RequestJobsieDefinitionCreate
from jobsies.services import DefinitionService

router = APIRouter(prefix="/definitions", tags=["Web Components"])
templates = Jinja2Templates(directory="src/jobsies/templates")


async def _extract_form_data(request: Request) -> dict:
    """Extract form data from request safely."""
    try:
        form = await request.form()
        return dict(form)
    except AssertionError:
        body = await request.body()
        parsed = parse_qs(body.decode("utf-8"))
        return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}


@router.get("/table", response_class=HTMLResponse)
async def get_definitions_table(request: Request) -> HTMLResponse:
    """Render the jobsie definitions HTMX partial table."""
    service = DefinitionService()
    definitions = service.list_definitions()
    return templates.TemplateResponse(
        request=request,
        name="components/definitions_table.html",
        context={"definitions": definitions},
    )


@router.get("/create", response_class=HTMLResponse)
async def get_create_definitions_form(request: Request) -> HTMLResponse:
    """Render the jobsie definition creation dialog."""
    service = DefinitionService()
    subclasses = service.list_jobsie_types()
    return templates.TemplateResponse(
        request=request,
        name="components/definitions_create_form.html",
        context={"subclasses": subclasses},
    )


@router.post("/create", response_class=HTMLResponse)
async def create_definition(request: Request) -> HTMLResponse:
    """Create a new jobsie definition via HTMX form submission."""
    form_data = await _extract_form_data(request)
    logger.debug(f"Received form data for definition creation: {form_data}")

    service = DefinitionService()
    try:
        definition_in = RequestJobsieDefinitionCreate(**form_data)
        service.create_definition(definition_in)
    except (KeyError, ValueError, ValidationError) as err:
        logger.error(str(err))
        raise HTTPException(status_code=400, detail=str(err)) from None

    definitions = service.list_definitions()
    return templates.TemplateResponse(
        request=request,
        name="components/definitions_table.html",
        context={"definitions": definitions},
        headers={"HX-Trigger": "definition-created"},
    )


@router.delete("/{definition_id}", response_class=HTMLResponse)
async def delete_definition(request: Request, definition_id: int) -> HTMLResponse:
    """Delete a jobsie definition via HTMX and re-render the table."""
    service = DefinitionService()
    deleted = service.delete_definition(definition_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Definition {definition_id} not found")

    definitions = service.list_definitions()
    return templates.TemplateResponse(
        request=request,
        name="components/definitions_table.html",
        context={"definitions": definitions},
        headers={"HX-Trigger": "definition-deleted"},
    )
