from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from sqlalchemy.sql import Select

from jobsies.database.handler import get_db_handler
from jobsies.jobs import get_jobsie_class
from jobsies.schemas.api import RequestJobsieDefinitionCreate, RequestJobsieDefinitionUpdate
from jobsies.schemas.tables import TableJobsiesDefinition

router = APIRouter(prefix="/jobsie/definition", tags=["Jobsie Definition"])


def _get_output_schema_for_subclass(subclass_name: str) -> dict:
    """Retrieve output schema from the matching BaseJobsie subclass."""
    try:
        cls = get_jobsie_class(subclass_name)
    except KeyError:
        msg = f"Unknown jobsie subclass: '{subclass_name}'"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        ) from None
    return cls.output_schema.model_json_schema()


@router.get("")
@router.get("/", include_in_schema=False)
def list_definitions() -> list[TableJobsiesDefinition]:
    """Retrieve all jobsie definitions."""
    db = get_db_handler()
    return db.load(TableJobsiesDefinition)


@router.get("/{definition_id}")
def get_definition(definition_id: int) -> TableJobsiesDefinition:
    """Retrieve a specific jobsie definition by its ID."""
    db = get_db_handler()
    definitions = db.load(
        TableJobsiesDefinition,
        statement=Select(TableJobsiesDefinition).where(TableJobsiesDefinition.id == definition_id),
    )
    if not definitions:
        msg = f"Jobsie definition with id {definition_id} not found"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg,
        )
    return definitions[0]


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_definition(definition_in: RequestJobsieDefinitionCreate) -> TableJobsiesDefinition:
    """Create a new jobsie definition with subclass-defined output_vars."""
    output_vars = _get_output_schema_for_subclass(definition_in.subclass_name)
    definition_data = definition_in.model_dump()
    definition_data["output_vars"] = output_vars

    try:
        db_definition = TableJobsiesDefinition(**definition_data)
    except ValueError as err:
        msg = str(err)
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        ) from None

    db = get_db_handler()
    db.store([db_definition])
    logger.info(f"Created jobsie definition with ID {db_definition.id} and name '{db_definition.name}'")
    return db_definition


@router.put("/{definition_id}")
@router.patch("/{definition_id}")
def update_definition(definition_id: int, definition_in: RequestJobsieDefinitionUpdate) -> TableJobsiesDefinition:
    """Update an existing jobsie definition by ID."""
    db = get_db_handler()
    existing = db.load(
        TableJobsiesDefinition,
        statement=Select(TableJobsiesDefinition).where(TableJobsiesDefinition.id == definition_id),
    )
    if not existing:
        msg = f"Jobsie definition with id {definition_id} not found"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg,
        )

    update_data = definition_in.model_dump(exclude_unset=True)
    if not update_data:
        return existing[0]

    if "subclass_name" in update_data and update_data["subclass_name"] is not None:
        update_data["output_vars"] = _get_output_schema_for_subclass(update_data["subclass_name"])

    update_data["updated_at"] = datetime.now(UTC)

    db.update(
        TableJobsiesDefinition,
        filters={"id": definition_id},
        update_values=update_data,
    )
    updated = db.load(
        TableJobsiesDefinition,
        statement=Select(TableJobsiesDefinition).where(TableJobsiesDefinition.id == definition_id),
    )
    logger.info(f"Updated jobsie definition with ID {definition_id}")
    return updated[0]


@router.delete("/{definition_id}")
def delete_definition(definition_id: int) -> dict[str, str]:
    """Delete a jobsie definition by ID."""
    db = get_db_handler()
    existing = db.load(
        TableJobsiesDefinition,
        statement=Select(TableJobsiesDefinition).where(TableJobsiesDefinition.id == definition_id),
    )
    if not existing:
        msg = f"Jobsie definition with id {definition_id} not found"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg,
        )

    db.delete(TableJobsiesDefinition, filters={"id": definition_id})
    logger.info(f"Deleted jobsie definition with ID {definition_id}")
    return {"message": f"Jobsie definition with id {definition_id} deleted successfully"}
