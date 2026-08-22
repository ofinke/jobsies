from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from loguru import logger
from pytz import timezone as pytz_timezone

from jobsies.config import get_templates
from jobsies.schemas.api.output import JobsieOutputInterface
from jobsies.services.output import OutputService

router = APIRouter(prefix="/results", tags=["Web Components"])
templates = get_templates()


def _status_bar_html(message: str, status_type: str = "success") -> str:
    icon = "check" if status_type == "success" else "alert-circle"
    return templates.get_template("components/status_bar.html").render(
        {"message": message, "type": status_type, "icon": icon},
    )


@router.get("/latest", response_class=HTMLResponse)
async def results_get_latest() -> HTMLResponse:
    """Render the latest results widget partial for HTMX."""
    raw_data = OutputService().get_latest_results()
    results = []
    for row in raw_data:
        data = row.model_dump()
        if not data["success"]:
            traceback = data.get("execution_metadata", {}).get("traceback", "No traceback available")
            last_line = traceback.strip().split("\n")[-1] if traceback else "No traceback available"
            data["output_data"] = {"traceback": last_line}
        results.append(JobsieOutputInterface(**data))
    logger.debug("Endpoint executed: GET /results/latest")
    widget_html = templates.get_template("components/results_widget.html").render(
        {"results": results},
    )
    prague_tz = pytz_timezone("Europe/Prague")
    now = datetime.now(prague_tz).strftime("%H:%M:%S")
    status_bar = _status_bar_html(f"Results refreshed at {now}")
    return HTMLResponse(widget_html + "\n" + status_bar)
