from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from humanize import naturaltime
from loguru import logger
from pytz import timezone

from jobsies.schemas.api.output import JobsieOutputInterface
from jobsies.services.output import OutputService
from jobsies.settings import get_settings, get_templates

router = APIRouter(prefix="/results", tags=["Web Components"])
templates = get_templates()
settings = get_settings()


def _status_bar_html(message: str, status_type: str = "success") -> str:
    icon = "check" if status_type == "success" else "alert-circle"
    return templates.get_template("components/status_bar.html").render(
        {"message": message, "type": status_type, "icon": icon},
    )


@router.get("/latest", response_class=HTMLResponse)
async def results_get_latest() -> HTMLResponse:
    """Render the latest results widget partial for HTMX."""
    raw_data = OutputService().get_latest_results()
    now_local = datetime.now(timezone(settings.tz_info)).replace(tzinfo=None)
    results = []
    for row in raw_data:
        data = row.model_dump()
        created_at = data["created_at"]
        data["created_at"] = f"{naturaltime(created_at, when=now_local)} ({created_at.strftime('%Y-%m-%d %H:%M:%S')})"
        if not data["success"]:
            traceback = data.get("execution_metadata", {}).get("traceback", "No traceback available")
            traceback_text = traceback.strip() if traceback else "No traceback available"
            data["output_data"] = {"traceback": traceback_text}
        results.append(JobsieOutputInterface(**data))
    logger.debug("Endpoint executed: GET /results/latest")
    widget_html = templates.get_template("components/results_widget.html").render(
        {"results": results},
    )
    now = now_local.strftime("%H:%M:%S")
    status_bar = _status_bar_html(f"Results refreshed at {now}")
    return HTMLResponse(widget_html + "\n" + status_bar)
