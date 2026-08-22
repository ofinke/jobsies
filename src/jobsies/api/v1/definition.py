from fastapi import APIRouter, HTTPException, status
from loguru import logger

from jobsies.schemas.api.definition import RequestJobsieDefinitionCreate, RequestJobsieDefinitionUpdate
from jobsies.schemas.tables import TableJobsiesDefinition
from jobsies.services import DefinitionService

router = APIRouter(prefix="/jobsie/definition", tags=["Jobsie Definition"])


@router.get("")
async def api_list_definitions() -> list[TableJobsiesDefinition]:
    """Retrieve all jobsie definitions."""
    service = DefinitionService()
    return service.list_definitions()


@router.get("/{definition_id}")
async def api_get_definition(definition_id: int) -> TableJobsiesDefinition:
    """Retrieve a specific jobsie definition by its ID."""
    service = DefinitionService()
    definition = service.get_definition(definition_id)
    if not definition:
        msg = f"Jobsie definition with id {definition_id} not found"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg,
        )
    return definition


@router.post("", status_code=status.HTTP_201_CREATED)
async def api_create_definition(definition_in: RequestJobsieDefinitionCreate) -> TableJobsiesDefinition:
    """Create a new jobsie definition with subclass-defined output_vars."""
    service = DefinitionService()
    try:
        return service.create_definition(definition_in)
    except KeyError:
        msg = f"Unknown jobsie subclass: '{definition_in.subclass_name}'"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        ) from None
    except ValueError as err:
        msg = str(err)
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        ) from None


@router.put("/{definition_id}")
@router.patch("/{definition_id}")
async def api_update_definition(
    definition_id: int, definition_in: RequestJobsieDefinitionUpdate
) -> TableJobsiesDefinition:
    """Update an existing jobsie definition by ID."""
    service = DefinitionService()
    try:
        updated = service.update_definition(definition_id, definition_in)
    except KeyError:
        msg = f"Unknown jobsie subclass: '{definition_in.subclass_name}'"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        ) from None

    if not updated:
        msg = f"Jobsie definition with id {definition_id} not found"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg,
        )
    return updated


@router.delete("/{definition_id}")
async def api_delete_definition(definition_id: int) -> dict[str, str]:
    """Delete a jobsie definition by ID."""
    service = DefinitionService()
    deleted = service.delete_definition(definition_id)
    if not deleted:
        msg = f"Jobsie definition with id {definition_id} not found"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg,
        )
    return {"message": f"Jobsie definition with id {definition_id} deleted successfully"}
