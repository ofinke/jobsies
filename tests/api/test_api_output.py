from fastapi.testclient import TestClient
from jobsies.database import get_db_handler
from jobsies.schemas.tables import TableJobsiesOutputs
from sqlmodel import Session


def seed_outputs() -> None:
    """Creates multiple output rows for the output API tests."""
    with Session(get_db_handler().engine) as session:
        session.add(
            TableJobsiesOutputs(
                jobsie_name="ExampleJobsie",
                jobsie_id=1,
                execution_id="exec-1",
                output_data={"price": 10},
                execution_metadata={"duration": 1},
            )
        )
        session.add(
            TableJobsiesOutputs(
                jobsie_name="ExampleJobsie",
                jobsie_id=1,
                execution_id="exec-2",
                success=False,
                output_data={"price": 12},
                execution_metadata={"duration": 2},
            )
        )
        session.add(
            TableJobsiesOutputs(
                jobsie_name="ZalandoJobsie",
                jobsie_id=2,
                execution_id="exec-3",
                output_data={"price": 99},
                execution_metadata={"duration": 3},
            )
        )
        session.commit()


def test_get_latest_outputs_empty(client: TestClient) -> None:
    """Tests GET /api/v1/output/latest returns an empty list without outputs."""
    response = client.get("/api/v1/output/latest")

    assert response.status_code == 200
    assert response.json() == []


def test_get_latest_outputs(client: TestClient) -> None:
    """Tests GET /api/v1/output/latest returns the latest output for every jobsie."""
    seed_outputs()

    response = client.get("/api/v1/output/latest")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 2,
            "jobsie_name": "ExampleJobsie",
            "jobsie_id": 1,
            "execution_id": "exec-2",
            "retention": None,
            "success": False,
            "output_data": {"price": 12},
            "execution_metadata": {"duration": 2},
        },
        {
            "id": 3,
            "jobsie_name": "ZalandoJobsie",
            "jobsie_id": 2,
            "execution_id": "exec-3",
            "retention": None,
            "success": True,
            "output_data": {"price": 99},
            "execution_metadata": {"duration": 3},
        },
    ]
