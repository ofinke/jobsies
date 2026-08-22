from fastapi import APIRouter, HTTPException, status
from loguru import logger

from jobsies.celery_app import wrapper_run_dynamic_jobsie
from jobsies.schemas.api.definition import ResponseJobsieExecute

router = APIRouter(prefix="/jobsie/execute", tags=["Jobsies Execution"])


@router.post("/{definition_id}")
@router.get("/{definition_id}")
async def api_jobsie_execute(definition_id: int) -> ResponseJobsieExecute:
    """Trigger execution of a jobsie configuration by ID."""
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
