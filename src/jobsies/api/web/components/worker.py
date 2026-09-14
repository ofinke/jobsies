from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from humanize import naturaltime
from pytz import timezone

from jobsies.config import get_templates
from jobsies.services import SchedulingService, get_redis_handler
from jobsies.settings import get_settings

router = APIRouter(prefix="/worker", tags=["Web Components"])
templates = get_templates()
settings = get_settings()


def _status_bar_html(message: str) -> str:
    """Render a successful status bar message for an HTMX response."""
    return templates.get_template("components/status_bar.html").render(
        {"message": message, "type": "success", "icon": "check"},
    )


@router.get("/next_task", response_class=HTMLResponse)
async def worker_get_next_tasks() -> HTMLResponse:
    """Render the next scheduled jobsies for the following 24 hours."""
    service = SchedulingService()
    definitions = {definition.id: definition for definition in service.get_active_task_configs()}
    scheduled_jobsies = service.define_next_jobsies(24 * 60 * 60)
    tasks = sorted(
        (
            {"id": definition_id, "name": definitions[definition_id].name, "scheduled_at": scheduled_at}
            for definition_id, executions in scheduled_jobsies.items()
            if definition_id in definitions
            for scheduled_at in executions
        ),
        key=lambda task: task["scheduled_at"],
    )[:14]

    now = datetime.now(timezone(settings.tz_info))
    for task in tasks:
        task["scheduled_at"] = naturaltime(task["scheduled_at"], when=now)

    table_html = templates.get_template("components/worker_next_tasks.html").render({"tasks": tasks})
    now = datetime.now(timezone(settings.tz_info)).strftime("%H:%M:%S")
    status_bar = _status_bar_html(f"Worker data refreshed at {now}")
    return HTMLResponse(table_html + "\n" + status_bar)


@router.get("/redis_status", response_class=HTMLResponse)
async def worker_get_redis_status() -> HTMLResponse:
    """Render the Redis broker status table for the worker page."""
    status = get_redis_handler(settings.broker_redis_url).client_status()
    table_html = templates.get_template("components/worker_redis_status.html").render({"status": status})
    return HTMLResponse(table_html)
