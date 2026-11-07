from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from loguru import logger
from pytz import timezone

from jobsies.services import DefinitionService, TrendsService
from jobsies.settings import get_settings, get_templates

router = APIRouter(prefix="/trends", tags=["Web Components"])
templates = get_templates()
settings = get_settings()


def _status_bar_html(message: str, status_type: str = "success") -> str:
    """Render the status bar as an HTMX out-of-band partial."""
    icon = "check" if status_type == "success" else "alert-circle"
    return templates.get_template("components/status_bar.html").render(
        {"message": message, "type": status_type, "icon": icon},
    )


@router.get("/latest", response_class=HTMLResponse)
async def trends_get_latest() -> HTMLResponse:
    """Render trend widgets for all Jobsie definitions with configured monitors."""
    definitions = DefinitionService().list_definitions()
    trends_service = TrendsService()
    trends = []
    for definition in definitions:
        if not definition.output_monitoring or definition.id is None:
            continue

        output_trend = trends_service.get_output_trend(definition.id)
        if output_trend is not None and output_trend["monitors"]:
            trends.append({"jobsie_id": definition.id, "name": definition.name, "data": output_trend})

    widget_html = templates.get_template("components/trends_widget.html").render(
        {"trends": trends, "timezone": settings.tz_info},
    )
    now = datetime.now(timezone(settings.tz_info)).strftime("%H:%M:%S")
    status_bar = _status_bar_html(f"Trends refreshed at {now}")
    logger.debug("Endpoint executed: GET /trends/latest")
    return HTMLResponse(widget_html + "\n" + status_bar)
