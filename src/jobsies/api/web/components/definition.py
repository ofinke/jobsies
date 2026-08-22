from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from loguru import logger
from pydantic import ValidationError

from jobsies.config import get_templates
from jobsies.schemas.api.definition import RequestJobsieDefinitionCreate, RequestJobsieDefinitionUpdate
from jobsies.services import DefinitionService

router = APIRouter(prefix="/definition", tags=["Web Components"])
templates = get_templates()


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
        name="components/definition_table.html",
        context={"definitions": definitions},
    )


@router.get("/create", response_class=HTMLResponse)
async def get_create_definitions_form(request: Request) -> HTMLResponse:
    """Render the jobsie definition creation dialog."""
    service = DefinitionService()
    subclasses = service.list_jobsie_types()
    return templates.TemplateResponse(
        request=request,
        name="components/definition_create_form.html",
        context={"subclasses": subclasses},
    )


@router.post("/create", response_class=HTMLResponse)
async def create_definition(request: Request) -> HTMLResponse:
    """Create a new jobsie definition via HTMX form submission."""
    form_data = await _extract_form_data(request)
    form_data["enabled"] = "enabled" in form_data
    logger.debug(f"Received form data for definition creation: {form_data}")

    service = DefinitionService()
    try:
        definition_in = RequestJobsieDefinitionCreate(**form_data)
        service.create_definition(definition_in)
    except (KeyError, ValueError, ValidationError) as err:
        logger.error(str(err))
        subclasses = service.list_jobsie_types()
        return templates.TemplateResponse(
            request=request,
            name="components/definition_create_form.html",
            context={"subclasses": subclasses, "errors": [f"{err!s}"], "form_data": form_data},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    definitions = service.list_definitions()
    return templates.TemplateResponse(
        request=request,
        name="components/definition_table.html",
        context={"definitions": definitions},
        headers={"HX-Retarget": "#definitions-table", "HX-Trigger": "definition-created"},
    )


@router.get("/{definition_id}/update", response_class=HTMLResponse)
async def get_update_definitions_form(request: Request, definition_id: int) -> HTMLResponse:
    """Render the jobsie definition update dialog with prefilled data."""
    service = DefinitionService()
    definition = service.get_definition(definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail=f"Definition {definition_id} not found")
    return templates.TemplateResponse(
        request=request,
        name="components/definition_update_form.html",
        context={"definition": definition},
    )


@router.patch("/{definition_id}", response_class=HTMLResponse)
@router.put("/{definition_id}", response_class=HTMLResponse)
async def update_definition(request: Request, definition_id: int) -> HTMLResponse:
    """Update a jobsie definition via HTMX form submission."""
    service = DefinitionService()
    definition = service.get_definition(definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail=f"Definition {definition_id} not found")

    form_data = await _extract_form_data(request)
    form_data["enabled"] = "enabled" in form_data
    form_data.pop("subclass_name", None)
    logger.debug(f"Received form data for definition update: {form_data}")

    try:
        definition_in = RequestJobsieDefinitionUpdate(**form_data)
        service.update_definition(definition_id, definition_in)
    except (KeyError, ValueError, ValidationError) as err:
        logger.error(str(err))
        return templates.TemplateResponse(
            request=request,
            name="components/definition_update_form.html",
            context={"definition": definition, "errors": [f"{err!s}"], "form_data": form_data},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    definitions = service.list_definitions()
    return templates.TemplateResponse(
        request=request,
        name="components/definition_table.html",
        context={"definitions": definitions},
        headers={"HX-Retarget": "#definitions-table", "HX-Trigger": "definition-updated"},
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
        name="components/definition_table.html",
        context={"definitions": definitions},
        headers={"HX-Trigger": "definition-deleted"},
    )
