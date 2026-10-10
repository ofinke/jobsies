import json
from datetime import datetime
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from loguru import logger
from pydantic import ValidationError
from pytz import timezone

from jobsies.celery_app import wrapper_run_dynamic_jobsie
from jobsies.jobs import get_jobsie_registry
from jobsies.schemas.api.definition import RequestJobsieDefinitionCreate, RequestJobsieDefinitionUpdate
from jobsies.schemas.enums import JobsieDefinitionStatus
from jobsies.services import DefinitionService
from jobsies.settings import get_settings, get_templates

# Static values
router = APIRouter(prefix="/definition", tags=["Web Components"])
templates = get_templates()
settings = get_settings()


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
    now = datetime.now(timezone(settings.tz_info)).strftime("%H:%M:%S")
    status_bar = _status_bar_html(f"Definitions refreshed at {now}")
    logger.debug("Endpoint executed: GET /definition/table")
    return HTMLResponse(table_html + "\n" + status_bar)


@router.get("/jobsies", response_class=HTMLResponse)
async def definition_get_jobsies() -> HTMLResponse:
    """Render the installed jobsie classes HTMX partial."""
    jobsies = [
        {
            "name": name,
            "docstring": jobsie_class.__doc__,
            "config_class": (
                config_schema.__name__ if (config_schema := jobsie_class.config_schema()) is not None else None
            ),
        }
        for name, jobsie_class in get_jobsie_registry().registry.items()
    ]
    jobsies_html = templates.get_template("components/definition_jobsies.html").render({"jobsies": jobsies})
    logger.debug("Endpoint executed: GET /definition/jobsies")
    return HTMLResponse(jobsies_html)


@router.get("/create", response_class=HTMLResponse)
async def definition_get_create_form(request: Request) -> HTMLResponse:
    """Render the jobsie definition creation dialog."""
    service = DefinitionService()
    subclasses = service.list_jobsie_types()
    input_examples = service.get_input_examples()
    logger.debug("Endpoint executed: GET /definition/create")
    return templates.TemplateResponse(
        request=request,
        name="components/definition_create_form.html",
        context={"subclasses": subclasses, "input_examples": input_examples},
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


@router.get("/{definition_id}/copy", response_class=HTMLResponse)
async def definition_get_copy_form(request: Request, definition_id: int) -> HTMLResponse:
    """Render a prefilled creation dialog copied from an existing definition."""
    service = DefinitionService()
    definition = service.get_definition(definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail=f"Definition {definition_id} not found")

    form_data = {
        "name": f"{definition.name} (copy)",
        "subclass_name": definition.subclass_name,
        "cron": definition.cron,
        "retention": definition.retention,
        "status": definition.status,
        "input_kwargs": json.dumps(definition.input_kwargs, indent=2),
    }
    logger.debug(f"Endpoint executed: GET /definition/{definition_id}/copy")
    return templates.TemplateResponse(
        request=request,
        name="components/definition_create_form.html",
        context={
            "subclasses": service.list_jobsie_types(),
            "input_examples": service.get_input_examples(),
            "form_data": form_data,
        },
    )


@router.post("/create", response_class=HTMLResponse)
async def definition_create(request: Request) -> HTMLResponse:
    """Create a new jobsie definition via HTMX form submission."""
    form_data = await _extract_form_data(request)
    logger.debug(f"Received form data for definition creation: {form_data}")

    service = DefinitionService()
    try:
        definition_in = RequestJobsieDefinitionCreate(**form_data)
        service.create_definition(definition_in)
    except (KeyError, ValueError, ValidationError) as err:
        logger.error(str(err))
        subclasses = service.list_jobsie_types()
        input_examples = service.get_input_examples()
        return templates.TemplateResponse(
            request=request,
            name="components/definition_create_form.html",
            context={
                "subclasses": subclasses,
                "input_examples": input_examples,
                "errors": [f"{err!s}"],
                "form_data": form_data,
            },
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    definitions = service.list_definitions()
    status_bar = _status_bar_html(f"Definition '{definition_in.name}' created successfully")
    table_html = templates.get_template("components/definition_table.html").render(
        {"definitions": definitions},
    )
    logger.debug("Endpoint executed: POST /definition/create")
    return HTMLResponse(
        table_html + "\n" + status_bar,
        headers={"HX-Retarget": "#definitions-table", "HX-Trigger": "definition-created"},
    )


@router.patch("/{definition_id}", response_class=HTMLResponse)
@router.put("/{definition_id}", response_class=HTMLResponse)
async def definintion_update(request: Request, definition_id: int) -> HTMLResponse:
    """Update a jobsie definition via HTMX form submission."""
    service = DefinitionService()
    definition = service.get_definition(definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail=f"Definition {definition_id} not found")

    form_data = await _extract_form_data(request)
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
    return HTMLResponse(
        table_html + "\n" + status_bar,
        headers={"HX-Retarget": "#definitions-table", "HX-Trigger": "definition-updated"},
    )


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
    definition = DefinitionService().get_definition(definition_id)
    if not definition:
        msg = f"Jobsie definition with id {definition_id} not found"
        logger.error(msg)
        return HTMLResponse(_status_bar_html(msg, status_type="error"))
    if definition.status == JobsieDefinitionStatus.UNAVAILABLE:
        msg = f"Jobsie definition with id {definition_id} is unavailable"
        logger.error(msg)
        return HTMLResponse(_status_bar_html(msg, status_type="error"))

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
