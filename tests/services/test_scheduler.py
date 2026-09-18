from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from freezegun import freeze_time
from jobsies.schemas.tables import TableJobsiesDefinition
from jobsies.services import SchedulingService
from pytz import timezone


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> SchedulingService:
    """Create a scheduler backed by the isolated test database."""
    monkeypatch.setattr("jobsies.services.scheduler.settings.tz_info", "UTC")
    return SchedulingService()


@pytest.fixture
def definition_factory(service: SchedulingService) -> Callable[..., TableJobsiesDefinition]:
    """Create and persist jobsie definitions with only relevant values configurable."""

    def create_definition(**overrides: Any) -> TableJobsiesDefinition:
        """Create and persist one jobsie definition."""
        values: dict[str, Any] = {
            "name": "Test Jobsie",
            "subclass_name": "ExampleJobsie",
            "cron": "0 * * * *",
            "retention": "0",
            "input_kwargs": {},
            "output_vars": {},
            "output_monitoring": {},
            "enabled": True,
        }
        values.update(overrides)
        definition = TableJobsiesDefinition(**values)
        service.db.store([definition])
        return definition

    return create_definition


def test_calculate_executions_in_window_includes_start_and_excludes_end(service: SchedulingService) -> None:
    """Test that execution windows include their start and exclude their end."""
    start = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    end = start + timedelta(minutes=10)

    executions = service.calculate_executions_in_window("*/5 * * * *", start, end)

    assert executions == [start, start + timedelta(minutes=5)]


def test_calculate_executions_in_window_returns_empty_when_no_run_is_due(service: SchedulingService) -> None:
    """Test that a valid cron expression can have no executions in a window."""
    start = datetime(2026, 1, 1, 12, 1, tzinfo=UTC)
    end = start + timedelta(minutes=3)

    assert service.calculate_executions_in_window("0 * * * *", start, end) == []


def test_get_active_task_configs_excludes_disabled_jobsies(
    service: SchedulingService,
    definition_factory: Callable[..., TableJobsiesDefinition],
) -> None:
    """Test that only enabled definitions are returned as active configurations."""
    enabled = definition_factory(name="Enabled")
    definition_factory(name="Disabled", enabled=False)

    active_configs = service.get_active_task_configs()

    assert [config.id for config in active_configs] == [enabled.id]


def test_define_next_jobsies_does_not_schedule_disabled_jobsie(
    service: SchedulingService,
    definition_factory: Callable[..., TableJobsiesDefinition],
) -> None:
    """Test that a disabled jobsie is absent from the scheduled jobsies."""
    enabled = definition_factory(name="Enabled", cron="0 * * * *")
    disabled = definition_factory(name="Disabled", cron="0 * * * *", enabled=False)

    with freeze_time("2026-01-01 11:59:00", tz_offset=0):
        scheduled = service.define_next_jobsies(120)

    assert scheduled.keys() == {enabled.id}
    assert disabled.id not in scheduled


def test_define_next_jobsies_schedules_all_runs_in_lookahead_window(
    service: SchedulingService,
    definition_factory: Callable[..., TableJobsiesDefinition],
) -> None:
    """Test that recurring jobsies are scheduled once for every due run in the window."""
    definition = definition_factory(cron="*/5 * * * *")

    with freeze_time("2026-01-01 12:00:00", tz_offset=0):
        scheduled = service.define_next_jobsies(11 * 60)

    assert scheduled[definition.id] == [
        datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        datetime(2026, 1, 1, 12, 5, tzinfo=UTC),
        datetime(2026, 1, 1, 12, 10, tzinfo=UTC),
    ]


def test_define_next_jobsies_omits_active_jobsie_without_run_in_window(
    service: SchedulingService,
    definition_factory: Callable[..., TableJobsiesDefinition],
) -> None:
    """Test that active jobsies without an upcoming run are omitted from the result."""
    definition = definition_factory(cron="0 * * * *")

    with freeze_time("2026-01-01 12:01:00", tz_offset=0):
        scheduled = service.define_next_jobsies(30)

    assert scheduled == {}
    assert definition.id not in scheduled


def test_define_next_jobsies_returns_runs_for_each_jobsie_separately(
    service: SchedulingService,
    definition_factory: Callable[..., TableJobsiesDefinition],
) -> None:
    """Test that schedules for multiple jobsies retain each definition's own cron pattern."""
    every_five_minutes = definition_factory(name="Frequent", cron="*/5 * * * *")
    hourly = definition_factory(name="Hourly", cron="0 * * * *")

    with freeze_time("2026-01-01 12:00:00", tz_offset=0):
        scheduled = service.define_next_jobsies(16 * 60)

    assert scheduled[every_five_minutes.id] == [
        datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        datetime(2026, 1, 1, 12, 5, tzinfo=UTC),
        datetime(2026, 1, 1, 12, 10, tzinfo=UTC),
        datetime(2026, 1, 1, 12, 15, tzinfo=UTC),
    ]
    assert scheduled[hourly.id] == [datetime(2026, 1, 1, 12, 0, tzinfo=UTC)]


def test_define_next_jobsies_uses_configured_timezone(
    monkeypatch: pytest.MonkeyPatch,
    service: SchedulingService,
    definition_factory: Callable[..., TableJobsiesDefinition],
) -> None:
    """Test that scheduler execution timestamps use the configured application timezone."""
    definition_factory(cron="0 * * * *")
    monkeypatch.setattr("jobsies.services.scheduler.settings.tz_info", "Europe/Prague")

    with freeze_time("2026-01-01 11:30:00", tz_offset=0):
        scheduled = service.define_next_jobsies(31 * 60)

    expected = datetime(2026, 1, 1, 12, 0, tzinfo=UTC).astimezone(timezone("Europe/Prague"))
    assert len(scheduled) == 1
    assert next(iter(scheduled.values())) == [expected]
