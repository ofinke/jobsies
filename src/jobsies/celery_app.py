from typing import Any

from celery import Celery
from loguru import logger

from jobsies.config import get_config_by_name
from jobsies.services import RunnerService, SchedulingService, get_redis_handler
from jobsies.settings import get_settings

settings = get_settings()
config = get_config_by_name("app-config")

# Celery worker definition
app = Celery(
    "jobsies",
    broker=settings.broker_redis_url,
    include=["jobsies.celery_app"],
)

# Celery worker configuration
# Static from env
app.conf.timezone = settings.tz_info
app.conf.redbeat_redis_url = settings.redbeat_redis_url
# hardcoded
app.conf.task_default_queue = "celery"
app.conf.worker_prefetch_multiplier = 0
app.conf.task_ignore_result = True
# configurable
app.conf.task_soft_time_limit = config.task_soft_time_limit
app.conf.task_time_limit = config.task_time_limit
app.conf.worker_concurrency = config.worker_concurrency

# Scheduler for cron jobs
app.conf.beat_schedule = {
    "schedule-upcoming-jobsies": {
        "task": "task.schedule_upcoming_jobsies",
        "schedule": config.scheduler_interval,
    },
}


def celery_app_status() -> dict[str, Any]:
    """Return the status and uptime of the Celery worker."""
    status = {"alive": False, "uptime": "Unavailable"}
    try:
        stats = app.control.inspect(timeout=0.1).stats() or {}
        if not stats:
            return status
        worker_key = next(iter(stats))
        uptime = stats[worker_key].get("uptime", "Unavailable")
    except Exception:  # noqa: BLE001
        return status

    status.update(alive=True, uptime=uptime)
    return status


# Celery worker tasks
@app.task(
    name="task.run_dynamic_jobsie",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
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
    # inti services
    config = get_config_by_name("app-config")
    scheduler = SchedulingService()
    redis = get_redis_handler(settings.broker_redis_url)

    # get which jobsies should be started
    jobsies = scheduler.define_next_jobsies(config.scheduler_lookahead)
    results = {"enqueued": 0, "skipped": 0}

    # add jobsies into redis queue
    for jobsie_id, upcoming_runs in jobsies.items():
        for run_time in upcoming_runs:
            epoch_timestamp = int(run_time.timestamp()) // 60
            lock_key = f"lock:task_run:{jobsie_id}:{epoch_timestamp}"
            logger.debug(f"Locking key: {lock_key}")

            if redis.acquire_enqueue_lock(lock_key, int(config.scheduler_lookahead * 1.2)):
                wrapper_run_dynamic_jobsie.apply_async(args=[jobsie_id], eta=run_time)
                results["enqueued"] += 1
                logger.info(f"Enqueued jobsie ID: '{jobsie_id}' for ETA: {run_time}")
            else:
                results["skipped"] += 1
                logger.warning(f"Jobsie with ID {jobsie_id} already scheduled for {run_time}")

    logger.info(f"Scheduled {results['enqueued']} jobsies (skipped {results['skipped']} duplicates)")
