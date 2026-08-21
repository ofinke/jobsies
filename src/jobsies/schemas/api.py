from typing import Any

from croniter import croniter
from loguru import logger
from pydantic import BaseModel, Field, field_validator


class JobsieDefinitionBase(BaseModel):
    """
    Shared fields for jobsie definition.

    Almost same as the TableDefinitionConfig model which defines how this definition is stored in the database.
    """

    name: str = Field(
        description="Name of the jobsie",
        examples=["Zalando Camper"],
    )
    subclass_name: str = Field(
        description="Name of the class which the jobsie uses",
        examples=["ZalandoJobsie"],
    )
    cron: str = Field(
        description="Cron expression for scheduling",
        examples=["0 0 * * *"],
    )
    retention: str = Field(
        default="0",
        description="Retention configuration in format 30d, etc.",
        examples=["0"],
    )
    input_kwargs: dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of input variables for the jobsie",
    )
    output_monitoring: dict[str, Any] = Field(
        default_factory=dict,
        description="How we want to monitor results in frontend",
    )
    enabled: bool = Field(
        default=True,
        description="Is the jobsie enabled",
    )

    @field_validator("cron")
    @classmethod
    def validate_cron(cls, value: str) -> str:
        """Validates cron expression format."""
        try:
            croniter(value)
        except (KeyError, ValueError):
            msg = f"Invalid cron expression: {value}"
            logger.error(msg)
            raise ValueError(msg) from None
        return value


class RequestJobsieDefinitionCreate(JobsieDefinitionBase):
    """Schema for creating a new jobsie definition."""


class RequestJobsieDefinitionUpdate(JobsieDefinitionBase):
    """Schema for updating an existing jobsie definition."""

    name: str | None = None
    subclass_name: str | None = None
    cron: str | None = None
    retention: str | None = None
    input_kwargs: dict[str, Any] | None = None
    output_monitoring: dict[str, Any] | None = None
    enabled: bool | None = None

    @field_validator("cron")
    @classmethod
    def validate_cron_optional(cls, value: str | None) -> str | None:
        """Validates cron expression format if provided."""
        if value is not None:
            try:
                croniter(value)
            except (KeyError, ValueError):
                msg = f"Invalid cron expression: {value}"
                logger.error(msg)
                raise ValueError(msg) from None
        return value


class ResponseJobsieExecute(BaseModel):
    """Schema for response returned when a jobsie execution is triggered."""

    message: str = Field(description="Status message of the execution request")
    definition_id: int = Field(description="ID of the jobsie definition executed")
    task_id: str = Field(description="Celery task ID for the execution")
