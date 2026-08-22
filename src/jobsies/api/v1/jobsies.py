from fastapi import APIRouter, HTTPException, status
from loguru import logger

from jobsies.celery_app import wrapper_run_dynamic_jobsie
from jobsies.schemas.api.definition import ResponseJobsieExecute
from jobsies.services import DefinitionService

router = APIRouter(prefix="/jobsie/execute", tags=["Jobsies Execution"])


@router.post("/{definition_id}")
@router.get("/{definition_id}")
async def api_jobsie_execute(definition_id: int) -> ResponseJobsieExecute:
    """Trigger execution of a jobsie configuration by ID."""
    service = DefinitionService()
    definition = service.get_definition(definition_id)
    if not definition:
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
