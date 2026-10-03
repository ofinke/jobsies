import json
from datetime import UTC, datetime
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from loguru import logger
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import Select

from jobsies.config import get_config_class_registry, get_config_registry
from jobsies.database import get_db_handler
from jobsies.schemas.tables import TableSharedConfigurations
from jobsies.settings import get_templates

router = APIRouter(prefix="/configs", tags=["Web Components"])
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
        return {key: value[0] if len(value) == 1 else value for key, value in parsed.items()}


def _get_configuration_models() -> dict[str, dict]:
    """Return registered configuration schemas for the form's type selector."""
    return {
        name: config_class.model_json_schema() for name, config_class in get_config_class_registry().registry.items()
    }


def _get_config_datatypes(schema: dict) -> dict[str, str]:
    """Return a JSON-ready mapping of configuration fields to their data types."""
    definitions = schema.get("$defs", {})

    def get_data_type(field_schema: dict, seen_refs: frozenset[str] = frozenset()) -> str:
        reference = field_schema.get("$ref")
        if reference:
            definition_name = reference.rsplit("/", 1)[-1]
            if definition_name in seen_refs:
                return "object"
            return get_data_type(definitions.get(definition_name, {}), seen_refs | {definition_name})

        union = field_schema.get("anyOf") or field_schema.get("oneOf")
        if union:
            return " | ".join(dict.fromkeys(get_data_type(option, seen_refs) for option in union))

        field_type = field_schema.get("type", "object")
        if isinstance(field_type, list):
            return " | ".join(dict.fromkeys(field_type))
        return field_type

    return {
        field: get_data_type(field_schema)
        for field, field_schema in schema.get("properties", {}).items()
    }


def _parse_config_values(config_model: str, config_json: str) -> dict:
    """Parse JSON configuration values and validate them with their registered model."""
    config_class = get_config_class_registry().get(config_model)
    config = config_class.model_validate(json.loads(config_json or "{}"))
    return config.model_dump(mode="json")


def _validate_config_name(name: str) -> str:
    """Require a non-empty configuration name."""
    if not name:
        msg = "Configuration name cannot be empty"
        raise ValueError(msg)
    return name


def _reload_config_registry() -> None:
    """Reload validated configuration values after a configuration change."""
    get_config_registry().store_and_validate()


def _get_configurations() -> list[TableSharedConfigurations]:
    """Load all persisted configurations for the table partial."""
    return get_db_handler().load(TableSharedConfigurations)


def _render_config_table() -> str:
    """Render the configurations table partial."""
    return templates.get_template("components/config_table.html").render(
        {"configurations": _get_configurations()},
    )


def _form_context(form_data: dict | None = None, errors: list[str] | None = None) -> dict:
    """Build common context for configuration create and update forms."""
    form_data = form_data or {}
    config_models = _get_configuration_models()
    selected_model = form_data.get("config_model")
    if selected_model not in config_models:
        selected_model = next(iter(config_models), None)

    return {
        "config_models": config_models,
        "config_datatypes": _get_config_datatypes(config_models.get(selected_model, {})),
        "form_data": form_data,
        "errors": errors or [],
    }


@router.get("/table", response_class=HTMLResponse)
async def configs_get_table() -> HTMLResponse:
    """Render the configurations HTMX partial table."""
    now = datetime.now(UTC).strftime("%H:%M:%S")
    table_html = _render_config_table()
    status_bar = _status_bar_html(f"Configurations refreshed at {now}")
    logger.debug("Endpoint executed: GET /configs/table")
    return HTMLResponse(table_html + "\n" + status_bar)


@router.get("/create", response_class=HTMLResponse)
async def configs_get_create_form(request: Request) -> HTMLResponse:
    """Render the configuration creation dialog."""
    logger.debug("Endpoint executed: GET /configs/create")
    return templates.TemplateResponse(
        request=request,
        name="components/config_form.html",
        context={"form_action": "/configs/create", **_form_context()},
    )


@router.get("/{config_id}/update", response_class=HTMLResponse)
async def configs_get_update_form(request: Request, config_id: int) -> HTMLResponse:
    """Render the configuration update dialog with its current values."""
    configurations = get_db_handler().load(
        TableSharedConfigurations,
        statement=Select(TableSharedConfigurations).where(TableSharedConfigurations.id == config_id),
    )
    if not configurations:
        raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")

    configuration = configurations[0]
    form_data = {
        "name": configuration.name,
        "config_model": configuration.config_model,
        "description": configuration.description or "",
        "config": json.dumps(configuration.config, indent=2),
    }
    logger.debug(f"Endpoint executed: GET /configs/{config_id}/update")
    return templates.TemplateResponse(
        request=request,
        name="components/config_form.html",
        context={
            "form_action": f"/configs/{config_id}",
            "config_id": config_id,
            **_form_context(form_data),
        },
    )


@router.get("/{config_id}/copy", response_class=HTMLResponse)
async def configs_get_copy_form(request: Request, config_id: int) -> HTMLResponse:
    """Render a prefilled creation dialog copied from an existing configuration."""
    configurations = get_db_handler().load(
        TableSharedConfigurations,
        statement=Select(TableSharedConfigurations).where(TableSharedConfigurations.id == config_id),
    )
    if not configurations:
        raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")

    configuration = configurations[0]
    form_data = {
        "name": f"{configuration.name} (copy)",
        "config_model": configuration.config_model,
        "description": configuration.description or "",
        "config": json.dumps(configuration.config, indent=2),
    }
    logger.debug(f"Endpoint executed: GET /configs/{config_id}/copy")
    return templates.TemplateResponse(
        request=request,
        name="components/config_form.html",
        context={"form_action": "/configs/create", **_form_context(form_data)},
    )


@router.post("/create", response_class=HTMLResponse)
async def configs_create(request: Request) -> HTMLResponse:
    """Create a reusable configuration via HTMX form submission."""
    form_data = await _extract_form_data(request)
    try:
        name = _validate_config_name(form_data.get("name", "").strip())
        config_values = _parse_config_values(form_data.get("config_model", ""), form_data.get("config", "{}"))
        configuration = TableSharedConfigurations(
            name=name,
            config_model=form_data.get("config_model", ""),
            description=(form_data.get("description", "") or "").strip() or None,
            config=config_values,
        )
        get_db_handler().store([configuration])
    except (KeyError, ValueError, ValidationError, IntegrityError) as err:
        logger.error(str(err))
        return templates.TemplateResponse(
            request=request,
            name="components/config_form.html",
            context={
                "form_action": "/configs/create",
                **_form_context(form_data, [str(err)]),
            },
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    _reload_config_registry()
    status_bar = _status_bar_html(f"Configuration '{configuration.name}' created successfully")
    logger.debug("Endpoint executed: POST /configs/create")
    return HTMLResponse(
        _render_config_table() + "\n" + status_bar,
        headers={"HX-Retarget": "#configs-table", "HX-Trigger": "config-created"},
    )


@router.patch("/{config_id}", response_class=HTMLResponse)
@router.put("/{config_id}", response_class=HTMLResponse)
async def configs_update(request: Request, config_id: int) -> HTMLResponse:
    """Update a reusable configuration via HTMX form submission."""
    db = get_db_handler()
    configurations = db.load(
        TableSharedConfigurations,
        statement=Select(TableSharedConfigurations).where(TableSharedConfigurations.id == config_id),
    )
    if not configurations:
        raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")

    configuration = configurations[0]
    form_data = await _extract_form_data(request)
    try:
        config_model = form_data.get("config_model", configuration.config_model)
        config_values = _parse_config_values(config_model, form_data.get("config", "{}"))
        name = _validate_config_name(form_data.get("name", configuration.name).strip())
        description = (form_data.get("description", configuration.description) or "").strip() or None
        db.update(
            TableSharedConfigurations,
            filters={"id": config_id},
            update_values={
                "name": name,
                "config_model": config_model,
                "description": description,
                "config": config_values,
                "updated_at": datetime.now(UTC),
            },
        )
    except (KeyError, ValueError, ValidationError, IntegrityError) as err:
        logger.error(str(err))
        return templates.TemplateResponse(
            request=request,
            name="components/config_form.html",
            context={
                "form_action": f"/configs/{config_id}",
                "config_id": config_id,
                **_form_context(form_data, [str(err)]),
            },
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    _reload_config_registry()
    status_bar = _status_bar_html(f"Configuration '{name}' updated successfully")
    logger.debug(f"Endpoint executed: PATCH|PUT /configs/{config_id}")
    return HTMLResponse(
        _render_config_table() + "\n" + status_bar,
        headers={"HX-Retarget": "#configs-table", "HX-Trigger": "config-updated"},
    )


@router.delete("/{config_id}", response_class=HTMLResponse)
async def configs_delete(config_id: int) -> HTMLResponse:
    """Delete a reusable configuration via HTMX and re-render the table."""
    db = get_db_handler()
    configurations = db.load(
        TableSharedConfigurations,
        statement=Select(TableSharedConfigurations).where(TableSharedConfigurations.id == config_id),
    )
    if not configurations:
        raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")

    configuration_name = configurations[0].name
    db.delete(TableSharedConfigurations, filters={"id": config_id})
    _reload_config_registry()
    status_bar = _status_bar_html(f"Configuration '{configuration_name}' deleted successfully")
    logger.debug(f"Endpoint executed: DELETE /configs/{config_id}")
    return HTMLResponse(
        _render_config_table() + "\n" + status_bar,
        headers={"HX-Retarget": "#configs-table"},
    )
