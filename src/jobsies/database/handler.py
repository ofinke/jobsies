# Database handler.
import functools

from loguru import logger
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy import update as sql_update
from sqlalchemy.sql import Select
from sqlmodel import Session, SQLModel, delete

from jobsies.settings import get_settings


class DatabaseHandler:
    """Database Handler for Jobsies operations."""

    def __init__(self) -> None:
        """Initializes engine to database."""
        self.engine = create_engine(get_settings().db_url)

        # Importing definitions of data models required to create table models.
        import jobsies.schemas.tables  # noqa: F401, PLC0415

        SQLModel.metadata.create_all(bind=self.engine)

    def store[T: BaseModel](self, data: list[T]) -> None:
        """Stores data of type[BaseModel] into corresponding table in database."""
        if not data:
            logger.debug("No data to store.")
            return

        with Session(self.engine) as session:
            try:
                for item in data:
                    session.add(item)
                session.commit()
            except Exception:
                session.rollback()
                raise
        logger.debug(f"Stored {len(data)} into '{data[0].__tablename__}' table.")

    def load[T: BaseModel](self, data_schema: type[T], *, statement: Select | None = None) -> list[T]:
        """Loads data from the table using a provided SQLAlchemy statement or defaults to full table."""
        with Session(self.engine) as session:
            try:
                if statement is None:
                    statement = Select(data_schema)
                results = session.exec(statement)
                return list(results.all())
            except Exception:
                session.rollback()
                raise

    def update[T: BaseModel](self, model: type[T], filters: dict[str, object], update_values: dict[str, object]) -> int:
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

    # def execute(self, statement: Select) -> None:
    #     """Executes a raw SQL statement."""
    #     with Session(self.engine) as session:
    #         try:
    #             session.execute(statement)
    #             session.commit()
    #         except Exception:
    #             session.rollback()
    #             raise

    def clear_table[T: BaseModel](self, data_schema: type[T]) -> int:
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
