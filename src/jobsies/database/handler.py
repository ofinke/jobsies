# Database handler.
import functools

from loguru import logger
from sqlalchemy import create_engine, select
from sqlalchemy import update as sql_update
from sqlalchemy.sql import Select
from sqlmodel import Session, SQLModel, delete

from jobsies.schemas.tables.base import TableDefaultModel
from jobsies.settings import get_settings

settings = get_settings()


class DatabaseHandler:
    """Database Handler for Jobsies operations."""

    def __init__(self) -> None:
        """Initializes engine to database."""
        self.engine = create_engine(settings.db_url)

        # Importing definitions of data models required to create table models.
        import jobsies.schemas.tables  # noqa: F401, PLC0415

        SQLModel.metadata.create_all(bind=self.engine)

    def store[T: TableDefaultModel](self, data: list[T]) -> None:
        """Stores data of type[BaseModel] into corresponding table in database."""
        if not data:
            logger.debug("No data to store.")
            return

        with Session(self.engine, expire_on_commit=False) as session:
            try:
                for item in data:
                    session.add(item)
                session.commit()
            except Exception:
                session.rollback()
                raise
        logger.debug(f"Stored {len(data)} into '{data[0].__tablename__}' table.")

    def load[T: TableDefaultModel](self, data_schema: type[T], *, statement: Select | None = None) -> list[T]:
        """
        Loads data from the table using a provided SQLAlchemy statement or defaults to full table.

        Handles both sqlmodel.select (returns scalars) and sqlalchemy Select (returns Row tuples).
        """
        # TODO: when writing tests, handle both cases with the Select and sqlmodel.select.
        with Session(self.engine, expire_on_commit=False) as session:
            try:
                if statement is None:
                    statement = select(data_schema)
                results = session.exec(statement)
                rows = results.all()
                if rows and hasattr(rows[0], "_mapping"):
                    rows = [row[0] for row in rows]
                return [row.datetimes_to_local_tz() for row in rows]
            except Exception:
                session.rollback()
                raise

    def update[T: TableDefaultModel](
        self,
        model: type[T],
        filters: dict[str, object],
        update_values: dict[str, object],
    ) -> int:
        """Update rows in the table that match given filters with provided values."""
        with Session(self.engine) as session:
            try:
                statement = sql_update(model).filter_by(**filters).values(**update_values)
                result = session.exec(statement)
                session.commit()
            except Exception:
                session.rollback()
                raise
            else:
                return result.rowcount if result else 0

    def delete[T: TableDefaultModel](self, model: type[T], filters: dict[str, object]) -> int:
        """Deletes rows from the table that match given filters."""
        with Session(self.engine) as session:
            try:
                statement = delete(model).filter_by(**filters)
                result = session.exec(statement)
                session.commit()
            except Exception:
                session.rollback()
                raise
            else:
                return result.rowcount if result else 0

    def clear_table[T: TableDefaultModel](self, data_schema: type[T]) -> int:
        """Deletes all rows from the table corresponding to the given data_schema."""
        with Session(self.engine) as session:
            try:
                statement = delete(data_schema)
                result = session.exec(statement)
                session.commit()
            except Exception:
                session.rollback()
                raise
            else:
                return result.rowcount if result else 0


@functools.cache
def get_db_handler() -> DatabaseHandler:
    """Return database handler."""
    return DatabaseHandler()
