from collections.abc import Generator

import pytest
from jobsies.database import get_db_handler
from jobsies.jobs import ExampleJobsie
from jobsies.schemas.tables import TableJobsiesDefinition
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture(autouse=True)
def test_db() -> Generator[Engine]:
    """Sets up an isolated in-memory database and restores the application engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(bind=engine)

    handler = get_db_handler()
    original_engine = handler.engine
    handler.engine = engine
    try:
        yield engine
    finally:
        handler.engine = original_engine
        engine.dispose()


def create_initial_definition(engine: Engine) -> None:
    """Creates the initial definition used by API and web tests."""
    with Session(engine) as session:
        session.add(
            TableJobsiesDefinition(
                name="Initial Test Config",
                subclass_name="ExampleJobsie",
                cron="0 * * * *",
                retention="0",
                input_kwargs={},
                output_vars=ExampleJobsie.output_schema.model_json_schema(),
                output_monitoring={},
                enabled=True,
            )
        )
        session.commit()


@pytest.fixture
def seeded_definition(test_db: Engine) -> None:
    """Seeds the initial definition used by API and web tests."""
    create_initial_definition(test_db)
