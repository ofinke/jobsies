from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlmodel import select

from jobsies.database import DatabaseHandler, get_db_handler
from jobsies.schemas.tables import TableJobsiesOutputs


class OutputService:
    """Service for handling all outputs from jobsie executions."""

    def __init__(self, db_handler: DatabaseHandler | None = None) -> None:
        """Initialize definition service."""
        self.db = db_handler or get_db_handler()

    def get_latest_results(self) -> list[TableJobsiesOutputs]:
        """Returns list with latest execution of all jobsies ordered by Jobsie ID."""
        subq = (
            select(
                TableJobsiesOutputs.jobsie_id,
                func.max(TableJobsiesOutputs.id).label("max_id"),
            )
            .group_by(TableJobsiesOutputs.jobsie_id)
            .subquery()
        )
        stmt = (
            select(TableJobsiesOutputs)
            .join(subq, TableJobsiesOutputs.id == subq.c.max_id)
            .order_by(TableJobsiesOutputs.jobsie_id)
        )
        return self.db.load(TableJobsiesOutputs, statement=stmt)

    def get_exception_counts(self) -> list[dict[str, int | str]]:
        """Return the number of failed executions for each jobsie in the last 24 hours."""
        since = datetime.now(UTC) - timedelta(hours=24)
        stmt = select(TableJobsiesOutputs).where(
            TableJobsiesOutputs.success.is_(False),
            TableJobsiesOutputs.created_at >= since,
        )
        outputs = self.db.load(TableJobsiesOutputs, statement=stmt)
        counts: dict[int, dict[str, int | str]] = {}
        for output in outputs:
            if output.jobsie_id not in counts:
                counts[output.jobsie_id] = {
                    "id": output.jobsie_id,
                    "name": output.jobsie_name,
                    "exceptions": 0,
                }
            counts[output.jobsie_id]["exceptions"] = int(counts[output.jobsie_id]["exceptions"]) + 1
        return sorted(counts.values(), key=lambda row: int(row["id"]))
