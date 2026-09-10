from datetime import UTC, datetime
from types import UnionType
from typing import Any, Union, get_args, get_origin

from loguru import logger
from pydantic import BaseModel
from sqlalchemy.sql import Select

from jobsies.database import DatabaseHandler, get_db_handler
from jobsies.jobs import BaseJobsie, get_jobsie_class
from jobsies.schemas.api.definition import RequestJobsieDefinitionCreate, RequestJobsieDefinitionUpdate
from jobsies.schemas.tables import TableJobsiesDefinition


def _unwrap_optional(annotation: Any) -> Any:
    """Return the non-None member of an Optional annotation, otherwise the annotation itself."""
    if get_origin(annotation) in (Union, UnionType):
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation


def _build_example(model: type[BaseModel]) -> dict:
    """Build an example input dict from Field examples, recursing into nested input models."""
    example: dict = {}
    for name, field in model.model_fields.items():
        if field.examples:
            example[name] = field.examples[0]
            continue
        annotation = _unwrap_optional(field.annotation)
        is_list = get_origin(annotation) is list
        if is_list:
            annotation = get_args(annotation)[0]
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            nested = _build_example(annotation)
            example[name] = [nested] if is_list else nested
    return example


class DefinitionService:
    """Service layer for interaction with database related to jobsie definition."""

    def __init__(self, db_handler: DatabaseHandler | None = None) -> None:
        """Initialize definition service."""
        self.db = db_handler or get_db_handler()

    def list_jobsie_types(self) -> list[str]:
        """Retrieve names of all BaseJobsie subclasses."""
        return [cls.__name__ for cls in BaseJobsie.__subclasses__()]

    def get_output_schema(self, subclass_name: str) -> dict:
        """Retrieve output schema from the matching BaseJobsie subclass."""
        cls = get_jobsie_class(subclass_name)
        return cls.output_schema.model_json_schema()

    def get_input_examples(self) -> dict[str, dict]:
        """Retrieve example input values for all Jobsie subclasses."""
        return {cls.__name__: _build_example(cls.input_schema) for cls in BaseJobsie.__subclasses__()}

    def list_definitions(self) -> list[TableJobsiesDefinition]:
        """Retrieve all jobsie definitions."""
        return self.db.load(TableJobsiesDefinition)

    def get_definition(self, definition_id: int) -> TableJobsiesDefinition | None:
        """Retrieve a specific jobsie definition by its ID."""
        definitions = self.db.load(
            TableJobsiesDefinition,
            statement=Select(TableJobsiesDefinition).where(TableJobsiesDefinition.id == definition_id),
        )
        return definitions[0] if definitions else None

    def create_definition(self, definition_in: RequestJobsieDefinitionCreate) -> TableJobsiesDefinition:
        """Create a new jobsie definition with subclass-defined output_vars."""
        output_vars = self.get_output_schema(definition_in.subclass_name)
        definition_data = definition_in.model_dump()
        definition_data["output_vars"] = output_vars

        db_definition = TableJobsiesDefinition(**definition_data)
        self.db.store([db_definition])
        logger.info(f"Created jobsie definition with ID {db_definition.id} and name '{db_definition.name}'")
        return db_definition

    def update_definition(
        self,
        definition_id: int,
        definition_in: RequestJobsieDefinitionUpdate,
    ) -> TableJobsiesDefinition | None:
        """Update an existing jobsie definition by ID."""
        existing = self.get_definition(definition_id)
        if not existing:
            return None

        update_data = definition_in.model_dump(exclude_unset=True)
        if not update_data:
            return existing

        if "subclass_name" in update_data and update_data["subclass_name"] is not None:
            update_data["output_vars"] = self.get_output_schema(update_data["subclass_name"])

        # datetime values are stored in UTC in the database, therefore we use UTC here
        update_data["updated_at"] = datetime.now(UTC)
        self.db.update(
            TableJobsiesDefinition,
            filters={"id": definition_id},
            update_values=update_data,
        )
        logger.info(f"Updated jobsie definition with ID {definition_id}")
        return self.get_definition(definition_id)

    def delete_definition(self, definition_id: int) -> bool:
        """Delete a jobsie definition by ID."""
        existing = self.get_definition(definition_id)
        if not existing:
            return False

        self.db.delete(TableJobsiesDefinition, filters={"id": definition_id})
        logger.info(f"Deleted jobsie definition with ID {definition_id}")
        return True
