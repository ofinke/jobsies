from typing import Any

import pytest
from jobsies.schemas.monitor import OutputMonitoringDefinition
from pydantic import ValidationError


@pytest.fixture
def example_jobsie_monitor() -> dict[str, Any]:
    """Provide a valid monitor for ExampleJobsie's numeric output field."""
    return {
        "title": "Number history",
        "field": "/number",
        "visualization": "line",
        "window": {"type": "last_executions", "count": 30},
    }


@pytest.fixture
def example_jobsie_monitoring(example_jobsie_monitor: dict[str, Any]) -> dict[str, Any]:
    """Provide a valid versioned monitor configuration for ExampleJobsie."""
    return {"version": 1, "monitors": [example_jobsie_monitor]}


def test_output_monitoring_definition_accepts_example_jobsie_monitor(
    example_jobsie_monitoring: dict[str, Any],
) -> None:
    """Validate a versioned monitor for ExampleJobsie's numeric output."""
    monitoring = OutputMonitoringDefinition.model_validate(example_jobsie_monitoring)

    assert monitoring.monitors[0].field == "/number"
    assert monitoring.monitors[0].window.count == 30


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("version", 2),
        ("field", "number"),
        ("field", "/price~2czk"),
        ("visualization", "bar"),
        ("window", {"type": "last_executions", "count": 0}),
    ],
)
def test_output_monitoring_definition_rejects_invalid_values(
    field: str,
    value: object,
    example_jobsie_monitor: dict[str, Any],
) -> None:
    """Reject unsupported versions and invalid monitor options."""
    monitor = example_jobsie_monitor.copy()
    if field == "version":
        data = {"version": value, "monitors": [monitor]}
    else:
        monitor[field] = value
        data = {"version": 1, "monitors": [monitor]}

    with pytest.raises(ValidationError):
        OutputMonitoringDefinition.model_validate(data)


def test_output_monitoring_definition_rejects_unknown_fields() -> None:
    """Reject misspelled monitoring configuration fields."""
    with pytest.raises(ValidationError):
        OutputMonitoringDefinition.model_validate({"version": 1, "monitors": [], "extra": True})
