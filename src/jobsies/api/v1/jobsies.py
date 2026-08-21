from fastapi import APIRouter, HTTPException, status
from loguru import logger
from sqlalchemy.sql import Select

from jobsies.celery_app import wrapper_run_dynamic_jobsie
from jobsies.database.handler import get_db_handler
from jobsies.schemas.api import ResponseJobsieExecute
from jobsies.schemas.tables import TableJobsiesDefinition

router = APIRouter(prefix="/jobsie", tags=["Jobsies Execution"])


@router.post("/execute/{definition_id}")
@router.get("/execute/{definition_id}")
def execute_jobsie(definition_id: int) -> ResponseJobsieExecute:
    """Trigger execution of a jobsie configuration by ID."""
    db = get_db_handler()
    definitions = db.load(
        TableJobsiesDefinition,
        statement=Select(TableJobsiesDefinition).where(TableJobsiesDefinition.id == definition_id),
    )
    if not definitions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jobsie definition with id {definition_id} not found",
        )

    task = wrapper_run_dynamic_jobsie.apply_async(args=[definition_id])
    logger.info(f"Triggered jobsie id {definition_id} with task id {task.id}")
    return ResponseJobsieExecute(
        message=f"Jobsie execution for definition ID {definition_id} queued successfully",
        definition_id=definition_id,
        task_id=str(task.id),
    )
