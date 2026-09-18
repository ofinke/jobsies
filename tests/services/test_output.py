from datetime import UTC, datetime, timedelta

import pytest
from jobsies.database import get_db_handler
from jobsies.schemas.tables import TableJobsiesOutputs
from jobsies.services import OutputService
from sqlmodel import Session


@pytest.fixture
def seeded_outputs() -> None:
    """Seeds three output rows from two jobsies into the test database."""
    create_output_rows()


def create_output_rows() -> None:
    """Creates three output rows from two jobsies in the test database."""
    with Session(get_db_handler().engine) as session:
        session.add(
            TableJobsiesOutputs(
                jobsie_name="ExampleJobsie",
                jobsie_id=1,
                execution_id="exec-1",
                output_data={"price": 10},
                execution_metadata={},
            )
        )
        session.add(
            TableJobsiesOutputs(
                jobsie_name="ExampleJobsie",
                jobsie_id=1,
                execution_id="exec-2",
                output_data={"price": 12},
                execution_metadata={},
            )
        )
        session.add(
            TableJobsiesOutputs(
                jobsie_name="ZalandoJobsie",
                jobsie_id=2,
                execution_id="exec-3",
                output_data={"price": 99},
                execution_metadata={},
            )
        )
        session.commit()


@pytest.mark.usefixtures("seeded_outputs")
def test_get_latest_results_with_multiple_rows() -> None:
    """Tests OutputService.get_latest_results returns only latest output of each jobsie."""
    service = OutputService()
    results = service.get_latest_results()
    assert len(results) == 2
    assert [result.jobsie_id for result in results] == [1, 2]
    assert [result.execution_id for result in results] == ["exec-2", "exec-3"]


def test_get_latest_results_empty_database() -> None:
    """Tests OutputService.get_latest_results returns empty list when no outputs exist."""
    service = OutputService()
    assert service.get_latest_results() == []


def test_get_exception_counts_only_returns_recent_failed_outputs() -> None:
    """Tests exception counts exclude successful and older output rows."""
    now = datetime.now(UTC)
    with Session(get_db_handler().engine) as session:
        session.add_all(
            [
                TableJobsiesOutputs(
                    jobsie_name="ExampleJobsie",
                    jobsie_id=1,
                    execution_id="failed-1",
                    created_at=now,
                    output_data={},
                    execution_metadata={},
                    success=False,
                ),
                TableJobsiesOutputs(
                    jobsie_name="ExampleJobsie",
                    jobsie_id=1,
                    execution_id="failed-2",
                    created_at=now - timedelta(hours=1),
                    output_data={},
                    execution_metadata={},
                    success=False,
                ),
                TableJobsiesOutputs(
                    jobsie_name="OtherJobsie",
                    jobsie_id=2,
                    execution_id="success-1",
                    created_at=now,
                    output_data={},
                    execution_metadata={},
                    success=True,
                ),
                TableJobsiesOutputs(
                    jobsie_name="OtherJobsie",
                    jobsie_id=2,
                    execution_id="failed-old",
                    created_at=now - timedelta(hours=25),
                    output_data={},
                    execution_metadata={},
                    success=False,
                ),
            ]
        )
        session.commit()

    assert OutputService().get_exception_counts() == [{"id": 1, "name": "ExampleJobsie", "exceptions": 2}]
