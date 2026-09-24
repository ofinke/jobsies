from datetime import datetime
from typing import Any

import redis
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from humanize import naturaltime, precisedelta
from loguru import logger
from pytz import timezone

from jobsies.celery_app import celery_app_status
from jobsies.services import OutputService, SchedulingService, get_redis_handler
from jobsies.settings import get_settings, get_templates

router = APIRouter(prefix="/worker", tags=["Web Components"])
templates = get_templates()
settings = get_settings()


def _status_bar_html(message: str) -> str:
    """Render a successful status bar message for an HTMX response."""
    return templates.get_template("components/status_bar.html").render(
        {"message": message, "type": "success", "icon": "check"},
    )


def _humanize_uptime(uptime: float | str) -> str:
    """Return a detailed human-readable uptime, preserving unavailable values."""
    if uptime == "Unavailable":
        return uptime
    return precisedelta(uptime, minimum_unit="seconds")


def _get_next_tasks() -> list[dict[str, Any]]:
    """Return the next scheduled jobsies for the following 24 hours."""
    task_limit = 15
    service = SchedulingService()
    definitions = {definition.id: definition for definition in service.get_active_task_configs()}
    defined_jobsies = service.define_next_jobsies(24 * 60 * 60)
    try:
        redis_handler = get_redis_handler(settings.broker_redis_url)
        scheduled_jobsies = redis_handler.get_scheduled_tasks(limit=task_limit)
    except redis.exceptions.ConnectionError:
        logger.warning("Redis is unavailable! Cannot retrieve scheduled tasks.")
        scheduled_jobsies = {}

    task_rows = {
        (definition_id, scheduled_at): {
            "id": definition_id,
            "name": definitions[definition_id].name,
            "scheduled_at": scheduled_at,
            "status": "Defined",
        }
        for definition_id, executions in defined_jobsies.items()
        if definition_id in definitions
        for scheduled_at in executions
    }
    for definition_id, executions in scheduled_jobsies.items():
        if definition_id not in definitions:
            continue
        for scheduled_at in executions:
            task_rows[(definition_id, scheduled_at)] = {
                "id": definition_id,
                "name": definitions[definition_id].name,
                "scheduled_at": scheduled_at,
                "status": "Acknowledged",
            }

    tasks = sorted(
        task_rows.values(),
        key=lambda task: task["scheduled_at"],
    )[:task_limit]

    now = datetime.now(timezone(settings.tz_info))
    for task in tasks:
        task["scheduled_at"] = naturaltime(task["scheduled_at"], when=now)

    return tasks


def _get_exceptions() -> list[dict[str, int | str]]:
    """Return jobsie execution exception counts from the last 24 hours."""
    return OutputService().get_exception_counts()


def _get_app_status() -> tuple[dict[str, Any], dict[str, Any]]:
    """Return Redis and Celery worker status data."""
    # First retrieve status of redis client
    redis_handler = get_redis_handler(settings.broker_redis_url)
    redis_status = redis_handler.client_status()

    # if redis is alive, look at status of the celery worker
    worker_status = celery_app_status() if redis_status.get("alive", False) else {}
    redis_status["uptime"] = _humanize_uptime(redis_status["uptime"])
    worker_status["uptime"] = _humanize_uptime(worker_status.get("uptime", "Unavailable"))

    return redis_status, worker_status


@router.get("/status", response_class=HTMLResponse)
async def worker_get_status() -> HTMLResponse:
    """Render all worker page components in one HTMX response."""
    tasks = _get_next_tasks()
    redis_status, worker_status = _get_app_status()
    exceptions = _get_exceptions()
    now = datetime.now(timezone(settings.tz_info)).strftime("%H:%M:%S")

    response = "\n".join(
        [
            templates.get_template("components/worker_next_tasks.html").render(
                {"tasks": tasks},
            ),
            templates.get_template("components/worker_redis_status.html").render(
                {"redis": redis_status, "celery": worker_status},
            ),
            templates.get_template("components/worker_exceptions.html").render(
                {"exceptions": exceptions},
            ),
            _status_bar_html(f"Worker data refreshed at {now}"),
        ]
    )
    return HTMLResponse(response)
