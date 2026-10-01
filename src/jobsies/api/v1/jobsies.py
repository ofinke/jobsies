from fastapi import APIRouter, HTTPException, status
from loguru import logger

from jobsies.celery_app import wrapper_run_dynamic_jobsie
from jobsies.schemas.api.definition import ResponseJobsieExecute
from jobsies.schemas.enums import JobsieDefinitionStatus
from jobsies.services import DefinitionService

router = APIRouter(prefix="/api/v1/jobsie/execute", tags=["Jobsies Execution"])


@router.post("/{definition_id}")
@router.get("/{definition_id}")
async def api_jobsie_execute(definition_id: int) -> ResponseJobsieExecute:
    """Trigger execution of a jobsie configuration by ID."""
    definition = DefinitionService().get_definition(definition_id)
    if not definition:
        msg = f"Jobsie definition with id {definition_id} not found"
        logger.error(msg)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    if definition.status == JobsieDefinitionStatus.UNAVAILABLE:
        msg = f"Jobsie definition with id {definition_id} is unavailable"
        logger.error(msg)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)

    try:
        task = wrapper_run_dynamic_jobsie.apply_async(args=[definition_id])
        logger.info(f"Triggered jobsie id {definition_id} with task id {task.id}")
    except Exception as err:
        logger.error(f"Failed to trigger jobsie {definition_id}: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger jobsie execution for definition ID {definition_id}",
        ) from err
    return ResponseJobsieExecute(
        message=f"Jobsie execution for definition ID {definition_id} queued successfully",
        definition_id=definition_id,
        task_id=str(task.id),
    )
