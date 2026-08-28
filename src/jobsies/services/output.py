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
