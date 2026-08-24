from collections.abc import Callable
from datetime import datetime, timedelta

from croniter import croniter
from loguru import logger
from pytz import timezone
from sqlmodel import select

from jobsies.database import get_db_handler
from jobsies.schemas.tables import TableJobsiesDefinition
from jobsies.services import RedisService
from jobsies.settings import get_settings


class SchedulingService:
    """
    Handles dynamic task discovery, cron execution calculations,
    and duplicate prevention using Redis locks.
    """

    def __init__(self, lookahead_seconds: int) -> None:
        """Initiates Redis client and how far into the future scheduler should schedule."""
        self.redis = RedisService()
        self.lookahead_seconds = lookahead_seconds
        self.settings = get_settings()

    def get_active_task_configs(self) -> list[TableJobsiesDefinition]:
        """Returns a list of active jobsies configurations."""
        db = get_db_handler()
        return db.load(
            TableJobsiesDefinition,
            statement=select(TableJobsiesDefinition).where(TableJobsiesDefinition.enabled.is_(True)),
        )

    def acquire_enqueue_lock(self, task_id: int, scheduled_time: datetime) -> bool:
        """
        Attempts to acquire a unique execution lock in Redis for a specific timestamp.
        Returns True if lock is acquired (safe to queue), False if already queued.
        """
        epoch_timestamp = int(scheduled_time.timestamp()) // 60  # timestamp truncated to minutes
        lock_key = f"lock:task_run:{task_id}:{epoch_timestamp}"
        logger.debug(f"Locking key: {lock_key}")

        # Keys expire after 1.2 multiple of the lookahead_seconds
        return bool(self.redis.set(lock_key, "enqueued", nx=True, ex=int(self.lookahead_seconds * 1.2)))

    def calculate_executions_in_window(self, cron_string: str, start_time: datetime, end_time: datetime) -> list:
        """Calculates all scheduled execution times for a cron pattern within a given window."""
        executions = []
        # croniter needs a starting point just before start_time to check boundaries cleanly
        iterator = croniter(cron_string, start_time - timedelta(seconds=1))

        next_run = iterator.get_next(datetime)
        while next_run < end_time:
            if next_run >= start_time:
                executions.append(next_run)
            next_run = iterator.get_next(datetime)

        return executions

    def process_and_schedule(self, target_task_callable: Callable) -> dict:
        """
        Core orchestration loop. Finds upcoming tasks, verifies locks,
        and triggers the Celery tasks with an ETA.
        """
        now = datetime.now(timezone(self.settings.tz_info))
        window_end = now + timedelta(seconds=self.lookahead_seconds)

        configs = self.get_active_task_configs()
        results = {"enqueued": 0, "skipped": 0}

        logger.debug(f"Starting schedule scan for window: {now} to {window_end}")

        for config in configs:
            task_id = config.id
            cron_expr = config.cron

            # Find all runs for this task in the next 30 minutes
            upcoming_runs = self.calculate_executions_in_window(cron_expr, now, window_end)

            # Scheduling task execution with locking mechanism to prevent double executions.
            for run_time in upcoming_runs:
                if self.acquire_enqueue_lock(task_id, run_time):
                    target_task_callable.apply_async(args=[task_id], eta=run_time)
                    results["enqueued"] += 1
                    logger.info(f"Enqueued jobsie ID: '{task_id}', name: '{config.name}' for ETA: {run_time}")
                else:
                    results["skipped"] += 1
                    logger.warning(f"Jobsie with ID {task_id} already scheduled for {run_time}")

        return results
