from celery import Celery
from loguru import logger

from jobsies.config import get_config
from jobsies.runner import run_dynamic_jobsie
from jobsies.services import SchedulingService
from jobsies.settings import get_settings

settings = get_settings()
config = get_config()

app = Celery(
    "jobsies",
    broker=settings.redis_url,
    include=["jobsies.celery_app"],
)

app.conf.timezone = "Europe/Prague"

app.conf.beat_schedule = {
    "schedule-upcoming-jobsies": {
        "task": "task.schedule_upcoming_jobsies",
        "schedule": config.scheduler_lookahead,
    },
}


@app.task(
    name="task.run_dynamic_jobsie",
    bind=True,
)
def wrapper_run_dynamic_jobsie(self, jobsie_id: int) -> dict:  # noqa: ANN001
    """Wrap execute_save_jobsie as a Celery task."""
    execution_metadata = {"execution_id": self.request.id, "execution_method": "celery"}
    return run_dynamic_jobsie(jobsie_id, execution_metadata=execution_metadata)


@app.task(
    name="task.schedule_upcoming_jobsies",
)
def schedule_upcoming_jobsies() -> None:
    """Schedules upcoming jobsies based on configuration using SchedulingService."""
    service = SchedulingService(lookahead_seconds=config.scheduler_lookahead)
    results = service.process_and_schedule(wrapper_run_dynamic_jobsie)
    logger.info(f"Scheduled {results['enqueued']} jobsies (skipped {results['skipped']} duplicates)")
