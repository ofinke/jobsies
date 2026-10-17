from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from jobsies.database import get_db_handler
from jobsies.schemas.tables import TableJobsiesDefinition, TableJobsiesOutputs
from jobsies.services import TrendsService


@pytest.fixture
def definition_factory() -> Callable[..., int]:
    """Create and persist ExampleJobsie definitions for trend tests."""

    def create_definition(output_monitoring: dict[str, Any] | None = None) -> int:
        """Persist a definition with the supplied output monitoring configuration."""
        definition = TableJobsiesDefinition(
            name="Trend test",
            subclass_name="ExampleJobsie",
            cron="0 * * * *",
            retention="0",
            input_kwargs={},
            output_vars={},
            output_monitoring=output_monitoring or {},
            status="enabled",
        )
        get_db_handler().store([definition])
        assert definition.id is not None
        return definition.id

    return create_definition


@pytest.fixture
def output_factory() -> Callable[..., None]:
    """Create and persist ExampleJobsie execution outputs for trend tests."""

    def create_output(
        jobsie_id: int,
        execution_id: str,
        created_at: datetime,
        output_data: dict[str, Any],
        *,
        success: bool = True,
    ) -> None:
        """Persist one ExampleJobsie execution output."""
        get_db_handler().store(
            [
                TableJobsiesOutputs(
                    jobsie_name="ExampleJobsie",
                    jobsie_id=jobsie_id,
                    execution_id=execution_id,
                    created_at=created_at,
                    output_data=output_data,
                    execution_metadata={},
                    success=success,
                ),
            ],
        )

    return create_output


def test_get_output_trend_returns_latest_successful_values_in_time_order(
    definition_factory: Callable[..., int],
    output_factory: Callable[..., None],
) -> None:
    """Return the latest configured successful outputs ordered chronologically."""
    jobsie_id = definition_factory(
        {
            "version": 1,
            "monitors": [
                {
                    "title": "Number history",
                    "field": "/number",
                    "visualization": "line",
                    "window": {"type": "last_executions", "count": 2},
                },
            ],
        },
    )
    now = datetime.now(UTC)
    output_factory(jobsie_id, "old", now - timedelta(minutes=3), {"content": "Hello World!", "number": 9})
    output_factory(jobsie_id, "middle", now - timedelta(minutes=2), {"content": "Hello World!", "number": 8})
    output_factory(jobsie_id, "failed", now - timedelta(minutes=1), {}, success=False)
    output_factory(jobsie_id, "latest", now, {"content": "Hello World!", "number": 6})

    trend = TrendsService().get_output_trend(jobsie_id)

    assert trend is not None
    assert trend["version"] == 1
    assert trend["monitors"][0]["title"] == "Number history"
    assert trend["monitors"][0]["data"]["value"] == [8, 6]
    assert trend["monitors"][0]["data"]["timestamp"] == [
        (now - timedelta(minutes=2)).isoformat(),
        now.isoformat(),
    ]


def test_get_output_trend_handles_nested_pointers_and_non_numeric_values(
    definition_factory: Callable[..., int],
    output_factory: Callable[..., None],
) -> None:
    """Resolve escaped JSON Pointer tokens and represent non-numeric values as gaps."""
    jobsie_id = definition_factory(
        {
            "version": 1,
            "monitors": [
                {
                    "title": "Nested value",
                    "field": "/stats/number~1value",
                    "visualization": "line",
                    "window": {"type": "last_executions", "count": 2},
                },
            ],
        },
    )
    now = datetime.now(UTC)
    output_factory(jobsie_id, "numeric", now - timedelta(minutes=1), {"stats": {"number/value": 12.5}})
    output_factory(jobsie_id, "string", now, {"stats": {"number/value": "unknown"}})

    trend = TrendsService().get_output_trend(jobsie_id)

    assert trend is not None
    assert trend["monitors"][0]["data"]["value"] == [12.5, None]


def test_get_output_trend_returns_empty_monitor_data_without_outputs(
    definition_factory: Callable[..., int],
) -> None:
    """Return configured monitors with empty data when there are no execution outputs."""
    jobsie_id = definition_factory(
        {
            "version": 1,
            "monitors": [
                {
                    "title": "Number history",
                    "field": "/number",
                    "visualization": "line",
                    "window": {"type": "last_executions", "count": 30},
                },
            ],
        },
    )

    trend = TrendsService().get_output_trend(jobsie_id)

    assert trend is not None
    assert trend["monitors"][0]["data"] == {"timestamp": [], "value": []}


def test_get_output_trend_returns_none_for_missing_definition() -> None:
    """Return None when no definition matches the requested Jobsie ID."""
    assert TrendsService().get_output_trend(999) is None


def test_get_output_trend_treats_empty_monitoring_as_no_monitors(definition_factory: Callable[..., int]) -> None:
    """Return an empty versioned trend result for definitions without monitoring configured."""
    jobsie_id = definition_factory()

    assert TrendsService().get_output_trend(jobsie_id) == {"version": 1, "monitors": []}
