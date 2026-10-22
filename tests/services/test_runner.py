import pytest
from jobsies.database import get_db_handler
from jobsies.exceptions import UnavailableJobsieError
from jobsies.jobs import ExampleJobsie, get_jobsie_registry
from jobsies.schemas.enums import JobsieDefinitionStatus
from jobsies.schemas.tables import TableJobsiesDefinition, TableJobsiesOutputs
from jobsies.services.runner import RunnerService


def test_get_jobsie_configuration_raises_for_unavailable_jobsie() -> None:
    """Reject retrieving a jobsie configuration when its status is unavailable."""
    jobsie_config = TableJobsiesDefinition(
        name="Unavailable test jobsie",
        subclass_name="ExampleJobsie",
        cron="0 * * * *",
        input_kwargs={},
        output_vars={},
        output_monitoring={},
        status=JobsieDefinitionStatus.UNAVAILABLE,
    )
    get_db_handler().store([jobsie_config])

    with pytest.raises(UnavailableJobsieError, match="is unavailable"):
        RunnerService()._get_jobsie_configuration(jobsie_config.id)


@pytest.mark.usefixtures("seeded_definition")
def test_run_dynamic_jobsie_stores_execution_duration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Store the measured jobsie execution duration in output metadata."""
    timestamps = iter((10.0, 12.5))
    monkeypatch.setattr("jobsies.services.runner.time.perf_counter", lambda: next(timestamps))

    RunnerService().run_dynamic_jobsie(1)

    output = get_db_handler().load(TableJobsiesOutputs)[0]
    assert output.execution_metadata["duration"] == 2.5


@pytest.mark.usefixtures("seeded_definition")
def test_run_dynamic_jobsie_skips_storage_when_result_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip storing output when the jobsie opts out of result persistence."""

    class IgnoreResultJobsie(ExampleJobsie):
        def __init__(self) -> None:
            """Initialize the jobsie with result persistence disabled."""
            super().__init__()
            self.ignore_result = True

    registry = get_jobsie_registry()
    monkeypatch.setitem(registry.registry, "ExampleJobsie", IgnoreResultJobsie)

    RunnerService().run_dynamic_jobsie(1)

    assert get_db_handler().load(TableJobsiesOutputs) == []
