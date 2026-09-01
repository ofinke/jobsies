from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import pytz
from freezegun import freeze_time
from jobsies.database import get_db_handler
from jobsies.jobs import ExampleJobsie, ZalandoJobsie
from jobsies.schemas.api.definition import RequestJobsieDefinitionCreate, RequestJobsieDefinitionUpdate
from jobsies.schemas.tables import TableJobsiesDefinition
from jobsies.schemas.tables.base import settings as base_settings
from jobsies.services import DefinitionService
from sqlmodel import Session


@pytest.fixture
def definition() -> TableJobsiesDefinition:
    """Creates an ExampleJobsie definition through the service and returns it."""
    return DefinitionService().create_definition(definition_request())


def definition_request(**overrides: Any) -> RequestJobsieDefinitionCreate:
    """Builds a definition create request for ExampleJobsie with optional field overrides."""
    data: dict[str, Any] = {
        "name": "Test Jobsie",
        "subclass_name": "ExampleJobsie",
        "cron": "0 0 * * *",
        "retention": "0",
        "input_kwargs": {},
        "output_monitoring": {},
        "enabled": True,
    }
    data.update(overrides)
    return RequestJobsieDefinitionCreate(**data)


def to_utc(naive_local: datetime, tz_name: str) -> datetime:
    """Converts a naive datetime expressed in the given timezone into an aware UTC datetime."""
    return pytz.timezone(tz_name).localize(naive_local).astimezone(UTC)


def test_list_definitions_empty_database() -> None:
    """Tests DefinitionService.list_definitions returns empty list when no definitions exist."""
    service = DefinitionService()
    assert service.list_definitions() == []


def test_list_definitions_returns_definitions() -> None:
    """Tests DefinitionService.list_definitions returns stored rows as definitions."""
    service = DefinitionService()
    created = service.create_definition(definition_request())

    definitions = service.list_definitions()
    assert len(definitions) == 1
    first_definition = definitions[0]
    assert isinstance(first_definition, TableJobsiesDefinition)
    assert first_definition.id == created.id
    assert first_definition.name == "Test Jobsie"
    assert first_definition.subclass_name == "ExampleJobsie"
    assert first_definition.cron == "0 0 * * *"
    assert first_definition.enabled is True
    assert first_definition.created_at is not None
    assert first_definition.updated_at is not None
    assert "content" in first_definition.output_vars["properties"]


def test_get_definition_returns_correct_definition() -> None:
    """Tests DefinitionService.get_definition returns the definition matching the given ID."""
    service = DefinitionService()
    first = service.create_definition(definition_request(name="First Jobsie"))
    second = service.create_definition(definition_request(name="Second Jobsie", subclass_name="ZalandoJobsie"))

    fetched_first = service.get_definition(first.id)
    assert fetched_first is not None
    assert fetched_first.name == "First Jobsie"
    assert fetched_first.subclass_name == "ExampleJobsie"

    fetched_second = service.get_definition(second.id)
    assert fetched_second is not None
    assert fetched_second.name == "Second Jobsie"
    assert fetched_second.subclass_name == "ZalandoJobsie"


def test_get_definition_returns_none_for_missing_id() -> None:
    """Tests DefinitionService.get_definition returns None for a non-existent ID."""
    service = DefinitionService()
    assert service.get_definition(999) is None


def test_create_definition_stores_and_retrieves_definition() -> None:
    """Tests DefinitionService.create_definition persists the definition with service-derived output_vars."""
    service = DefinitionService()
    created = service.create_definition(
        definition_request(retention="7d", input_kwargs={"url": "https://example.com"})
    )
    assert created.id is not None

    fetched = service.get_definition(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "Test Jobsie"
    assert fetched.subclass_name == "ExampleJobsie"
    assert fetched.cron == "0 0 * * *"
    assert fetched.retention == "7d"
    assert fetched.input_kwargs == {"url": "https://example.com"}
    assert fetched.output_monitoring == {}
    assert fetched.enabled is True
    assert fetched.output_vars == ExampleJobsie.output_schema.model_json_schema()

    listed = service.list_definitions()
    assert len(listed) == 1
    assert listed[0].id == created.id


def test_update_definition_updates_fields() -> None:
    """Tests DefinitionService.update_definition changes provided fields and refreshes output_vars."""
    service = DefinitionService()
    created = service.create_definition(definition_request())
    before = service.get_definition(created.id)
    assert before is not None

    update_in = RequestJobsieDefinitionUpdate(
        name="Updated Jobsie",
        subclass_name="ZalandoJobsie",
        cron="*/10 * * * *",
        retention="14d",
        input_kwargs={"url": "https://zalando.cz"},
        output_monitoring={"price_czk": True},
    )
    updated = service.update_definition(created.id, update_in)

    assert updated is not None
    assert updated.id == created.id
    assert updated.name == "Updated Jobsie"
    assert updated.subclass_name == "ZalandoJobsie"
    assert updated.cron == "*/10 * * * *"
    assert updated.retention == "14d"
    assert updated.input_kwargs == {"url": "https://zalando.cz"}
    assert updated.output_monitoring == {"price_czk": True}
    assert updated.enabled is True
    assert updated.output_vars == ZalandoJobsie.output_schema.model_json_schema()
    assert updated.created_at == before.created_at
    assert len(service.list_definitions()) == 1


def test_update_definition_returns_none_for_missing_id() -> None:
    """Tests DefinitionService.update_definition returns None for a non-existent ID."""
    service = DefinitionService()
    assert service.update_definition(999, RequestJobsieDefinitionUpdate(name="Ghost Jobsie")) is None


def test_update_definition_updated_at_in_utc_and_returned_in_app_timezone(
    monkeypatch: pytest.MonkeyPatch,
    definition: TableJobsiesDefinition,
) -> None:
    """Tests update_definition stores updated_at in UTC and returns it converted to the app timezone."""
    monkeypatch.setattr(base_settings, "tz_info", "Asia/Tokyo")
    service = DefinitionService()

    before = service.get_definition(definition.id)
    assert before is not None
    assert before.updated_at is not None
    assert before.updated_at.tzinfo is None

    expected_utc = datetime.now(UTC).replace(microsecond=0) + timedelta(days=1)
    with freeze_time(expected_utc):
        updated = service.update_definition(definition.id, RequestJobsieDefinitionUpdate(name="Tokyo Updated"))

    assert updated is not None
    assert updated.name == "Tokyo Updated"
    assert updated.created_at == before.created_at
    assert updated.updated_at is not None
    # Returned timestamps are naive wall-clock values expressed in the app timezone.
    assert updated.updated_at.tzinfo is None
    assert updated.updated_at > before.updated_at
    expected_app_time = pytz.utc.localize(expected_utc.replace(tzinfo=None)).astimezone(pytz.timezone("Asia/Tokyo"))
    assert updated.updated_at == expected_app_time.replace(tzinfo=None)
    assert to_utc(before.updated_at, "Asia/Tokyo") < expected_utc

    # Raw database value stays naive UTC.
    with Session(get_db_handler().engine) as session:
        raw = session.get(TableJobsiesDefinition, definition.id)
    assert raw is not None
    assert raw.updated_at is not None
    assert raw.updated_at.tzinfo is None
    assert raw.updated_at.replace(tzinfo=UTC) == expected_utc


def test_delete_definition_removes_existing_definition() -> None:
    """Tests DefinitionService.delete_definition removes an existing definition and returns True."""
    service = DefinitionService()
    created = service.create_definition(definition_request())

    assert service.delete_definition(created.id) is True
    assert service.get_definition(created.id) is None
    assert service.list_definitions() == []


def test_delete_definition_returns_false_for_missing_id() -> None:
    """Tests DefinitionService.delete_definition returns False for a non-existent ID."""
    service = DefinitionService()
    assert service.delete_definition(999) is False
