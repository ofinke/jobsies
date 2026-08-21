from collections.abc import Generator

import pytest
from jobsies.database.handler import get_db_handler
from jobsies.jobs import ExampleJobsie, ZalandoJobsie
from jobsies.schemas.api import RequestJobsieDefinitionCreate, RequestJobsieDefinitionUpdate
from jobsies.schemas.tables import TableJobsiesDefinition
from jobsies.services import DefinitionService
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture(autouse=True)
def test_db() -> Generator[None]:
    """Sets up an in-memory database for testing and overrides the database handler engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(bind=engine)

    handler = get_db_handler()
    original_engine = handler.engine
    handler.engine = engine

    with Session(engine) as session:
        definition = TableJobsiesDefinition(
            name="Initial Test Config",
            subclass_name="ExampleJobsie",
            cron="0 * * * *",
            retention="0",
            input_kwargs={},
            output_vars=ExampleJobsie.output_schema.model_json_schema(),
            output_monitoring={},
            enabled=True,
        )
        session.add(definition)
        session.commit()

    yield

    handler.engine = original_engine


def test_service_list_definitions() -> None:
    """Tests DefinitionService.list_definitions returns list of definitions."""
    service = DefinitionService()
    definitions = service.list_definitions()
    assert len(definitions) == 1
    assert definitions[0].name == "Initial Test Config"


def test_service_get_definition_found() -> None:
    """Tests DefinitionService.get_definition with existing ID returns definition."""
    service = DefinitionService()
    definition = service.get_definition(1)
    assert definition is not None
    assert definition.name == "Initial Test Config"


def test_service_get_definition_not_found() -> None:
    """Tests DefinitionService.get_definition with invalid ID returns None."""
    service = DefinitionService()
    definition = service.get_definition(999)
    assert definition is None


def test_service_create_definition() -> None:
    """Tests DefinitionService.create_definition creates a definition in the database."""
    service = DefinitionService()
    definition_in = RequestJobsieDefinitionCreate(
        name="Created via Service",
        subclass_name="ZalandoJobsie",
        cron="*/5 * * * *",
        retention="14d",
        input_kwargs={"url": "https://zalando.cz"},
        output_monitoring={},
        enabled=True,
    )
    result = service.create_definition(definition_in)
    assert result.id is not None
    assert result.name == "Created via Service"
    assert result.output_vars == ZalandoJobsie.output_schema.model_json_schema()


def test_service_update_definition() -> None:
    """Tests DefinitionService.update_definition modifies an existing definition."""
    service = DefinitionService()
    update_in = RequestJobsieDefinitionUpdate(
        name="Updated Name via Service",
        subclass_name="ZalandoJobsie",
    )
    updated = service.update_definition(1, update_in)
    assert updated is not None
    assert updated.name == "Updated Name via Service"
    assert updated.subclass_name == "ZalandoJobsie"
    assert updated.output_vars == ZalandoJobsie.output_schema.model_json_schema()


def test_service_update_definition_not_found() -> None:
    """Tests DefinitionService.update_definition on non-existent ID returns None."""
    service = DefinitionService()
    update_in = RequestJobsieDefinitionUpdate(name="Non-existent")
    updated = service.update_definition(999, update_in)
    assert updated is None


def test_service_delete_definition() -> None:
    """Tests DefinitionService.delete_definition removes definition from database."""
    service = DefinitionService()
    success = service.delete_definition(1)
    assert success is True
    assert service.get_definition(1) is None


def test_service_delete_definition_not_found() -> None:
    """Tests DefinitionService.delete_definition on non-existent ID returns False."""
    service = DefinitionService()
    success = service.delete_definition(999)
    assert success is False
