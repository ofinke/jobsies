from celery import Celery
from loguru import logger

from jobsies.config import get_config
from jobsies.services import RunnerService, SchedulingService
from jobsies.settings import get_settings

settings = get_settings()
config = get_config()

# Celery worker definition
app = Celery(
    "jobsies",
    broker=settings.redis_url,
    include=["jobsies.celery_app"],
)

# Celery worker configuration
app.conf.timezone = settings.tz_info
app.conf.task_soft_time_limit = 300
app.conf.task_time_limit = 360
app.conf.task_ignore_result = True
app.conf.worker_concurrency = 2

# Scheduler for cron jobs
app.conf.beat_schedule = {
    "schedule-upcoming-jobsies": {
        "task": "task.schedule_upcoming_jobsies",
        "schedule": config.scheduler_lookahead,
    },
}


# Celery worker tasks
@app.task(
    name="task.run_dynamic_jobsie",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True
)
def wrapper_run_dynamic_jobsie(self, jobsie_id: int) -> None:  # noqa: ANN001
    """Execution layer for the RunnerService as a celery task."""
    execution_metadata = {"execution_id": self.request.id, "execution_method": "celery"}
    RunnerService().run_dynamic_jobsie(jobsie_id, execution_metadata=execution_metadata)


@app.task(
    name="task.schedule_upcoming_jobsies",
)
def schedule_upcoming_jobsies() -> None:
    """Schedules upcoming jobsies based on configuration using SchedulingService."""
    service = SchedulingService(lookahead_seconds=config.scheduler_lookahead)
    results = service.process_and_schedule(wrapper_run_dynamic_jobsie)
    logger.info(f"Scheduled {results['enqueued']} jobsies (skipped {results['skipped']} duplicates)")
