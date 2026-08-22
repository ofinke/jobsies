from datetime import datetime
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from loguru import logger
from pydantic import ValidationError
from pytz import timezone as pytz_timezone

from jobsies.celery_app import wrapper_run_dynamic_jobsie
from jobsies.config import get_templates
from jobsies.schemas.api.definition import RequestJobsieDefinitionCreate, RequestJobsieDefinitionUpdate
from jobsies.services import DefinitionService

router = APIRouter(prefix="/definition", tags=["Web Components"])
templates = get_templates()


def _status_bar_html(message: str, status_type: str = "success") -> str:
    """Render the status bar as an HTML snippet for hx-swap-oob."""
    icon = "check" if status_type == "success" else "alert-circle"
    return templates.get_template("components/status_bar.html").render(
        {"message": message, "type": status_type, "icon": icon},
    )


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
async def definition_get_table() -> HTMLResponse:
    """Render the jobsie definitions HTMX partial table."""
    service = DefinitionService()
    definitions = service.list_definitions()
    table_html = templates.get_template("components/definition_table.html").render(
        {"definitions": definitions},
    )
    prague_tz = pytz_timezone("Europe/Prague")
    now = datetime.now(prague_tz).strftime("%H:%M:%S")
    status_bar = _status_bar_html(f"Definitions refreshed at {now}")
    logger.debug("Endpoint executed: GET /definition/table")
    return HTMLResponse(table_html + "\n" + status_bar)


@router.get("/create", response_class=HTMLResponse)
async def definition_get_create_form(request: Request) -> HTMLResponse:
    """Render the jobsie definition creation dialog."""
    service = DefinitionService()
    subclasses = service.list_jobsie_types()
    logger.debug("Endpoint executed: GET /definition/create")
    return templates.TemplateResponse(
        request=request,
        name="components/definition_create_form.html",
        context={"subclasses": subclasses},
    )


@router.get("/{definition_id}/update", response_class=HTMLResponse)
async def definition_get_update_form(request: Request, definition_id: int) -> HTMLResponse:
    """Render the jobsie definition update dialog with prefilled data."""
    service = DefinitionService()
    definition = service.get_definition(definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail=f"Definition {definition_id} not found")
    logger.debug(f"Endpoint executed: GET /definition/{definition_id}/update")
    return templates.TemplateResponse(
        request=request,
        name="components/definition_update_form.html",
        context={"definition": definition},
    )


@router.post("/create", response_class=HTMLResponse)
async def definition_create(request: Request) -> HTMLResponse:
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
    status_bar = _status_bar_html(f"Definition '{definition_in.name}' created successfully")
    table_html = templates.get_template("components/definition_table.html").render(
        {"definitions": definitions},
    )
    logger.debug("Endpoint executed: POST /definition/create")
    return HTMLResponse(table_html + "\n" + status_bar, headers={"HX-Retarget": "#definitions-table"})


@router.patch("/{definition_id}", response_class=HTMLResponse)
@router.put("/{definition_id}", response_class=HTMLResponse)
async def definintion_update(request: Request, definition_id: int) -> HTMLResponse:
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
    status_bar = _status_bar_html(f"Definition '{definition.id}' updated successfully")
    table_html = templates.get_template("components/definition_table.html").render(
        {"definitions": definitions},
    )
    logger.debug(f"Endpoint executed: PATCH|PUT /definition/{definition_id}")
    return HTMLResponse(table_html + "\n" + status_bar, headers={"HX-Retarget": "#definitions-table"})


@router.delete("/{definition_id}", response_class=HTMLResponse)
async def definition_delete(definition_id: int) -> HTMLResponse:
    """Delete a jobsie definition via HTMX and re-render the table."""
    service = DefinitionService()
    definition = service.get_definition(definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail=f"Definition {definition_id} not found")

    definition_name = definition.name
    service.delete_definition(definition_id)

    definitions = service.list_definitions()
    status_bar = _status_bar_html(f"Definition '{definition_name}' deleted successfully")
    table_html = templates.get_template("components/definition_table.html").render(
        {"definitions": definitions},
    )
    logger.debug(f"Endpoint executed: DELETE /definition/{definition_id}")
    return HTMLResponse(table_html + "\n" + status_bar, headers={"HX-Retarget": "#definitions-table"})


@router.post("/execute/{definition_id}", response_class=HTMLResponse)
async def definition_execute(definition_id: int) -> HTMLResponse:
    """Schedules jobsie execution via HTMX and returns status bar."""
    try:
        task = wrapper_run_dynamic_jobsie.apply_async(args=[definition_id])
        logger.debug(f"Triggered jobsie id {definition_id} with task id {task.id}")
        status_bar = _status_bar_html(
            f"Jobsie execution for ID '{definition_id}' queued successfully (task {task.id[:8]}...)",
        )
    except Exception as err:  # noqa: BLE001
        logger.error(f"Failed to trigger jobsie {definition_id}: {err}")
        status_bar = _status_bar_html(
            f"Failed to trigger jobsie execution: {err}",
            status_type="error",
        )
    return HTMLResponse(status_bar)
