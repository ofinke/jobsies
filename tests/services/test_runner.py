import pytest
from jobsies.database import get_db_handler
from jobsies.exceptions import UnavailableJobsieError
from jobsies.schemas.enums import JobsieDefinitionStatus
from jobsies.schemas.tables import TableJobsiesDefinition
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
