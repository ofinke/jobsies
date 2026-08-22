from fastapi import APIRouter

from jobsies.schemas.api.output import JobsieOutputBase
from jobsies.services.output import OutputService

router = APIRouter(prefix="/output", tags=["Jobsies Outputs"])


@router.get("/latest")
def get_latest_results() -> list[JobsieOutputBase]:
    """Return the latest output for every jobsie."""
    raw_data = OutputService().get_latest_results()
    return [JobsieOutputBase(**row.model_dump()) for row in raw_data]
