from datetime import datetime, timedelta

from croniter import croniter
from loguru import logger
from pytz import timezone
from sqlmodel import select

from jobsies.database import get_db_handler
from jobsies.schemas.tables import TableJobsiesDefinition
from jobsies.settings import get_settings

settings = get_settings()

class SchedulingService:
    """
    Service for handling all methods related to custom task scheduling.

    Dynamic task discovery, cron execution calculations, and duplicate prevention using Redis locks.
    """

    def __init__(self) -> None:
        """Initiates the Redis and database clients used by the scheduler."""
        # Tasks are scheduled into the broker database
        self.db = get_db_handler()

    def get_active_task_configs(self) -> list[TableJobsiesDefinition]:
        """Returns a list of active jobsies configurations."""
        return self.db.load(
            TableJobsiesDefinition,
            statement=select(TableJobsiesDefinition).where(TableJobsiesDefinition.enabled.is_(True)),
        )

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

    def define_next_jobsies(self, lookahead_seconds: int) -> dict[int, list[datetime]]:
        """Return the upcoming execution times for each active jobsie."""
        now = datetime.now(timezone(settings.tz_info))
        window_end = now + timedelta(seconds=lookahead_seconds)

        configs = self.get_active_task_configs()
        jobsies = {}

        logger.debug(f"Defining jobsies for window: {now} to {window_end}")

        for config in configs:
            executions = self.calculate_executions_in_window(config.cron, now, window_end)
            if executions:
                jobsies[config.id] = executions

        return jobsies
