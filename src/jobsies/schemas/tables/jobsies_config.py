from croniter import croniter
from loguru import logger
from pydantic import field_validator
from sqlalchemy import Column, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlmodel import Field

from .base import TableDefaultModel


class TableJobsiesConfig(TableDefaultModel, table=True):
    __tablename__ = "config_jobsies"

    name: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Name of the jobsie",
    )
    subclass_name: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Name of the class which the jobsie uses",
    )
    cron: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Cron tab",
    )
    input_kwargs: dict = Field(
        sa_column=Column(JSON, nullable=False),
        description="Dictionary of input variables for the jobsie",
    )
    output_vars: dict = Field(
        sa_column=Column(JSON, nullable=False),
        description="Names and description of output variables, defined by class.",
    )
    output_monitoring: dict = Field(
        sa_column=Column(JSON, nullable=False),
        description="How we want to monitor results in frontend",
    )
    enabled: bool = Field(
        default=True,
        description="Is the jobsie enabled",
    )

    @field_validator("cron")
    @classmethod
    def validate_cron(cls, value: str) -> str:
        try:
            croniter(value)
        except (KeyError, ValueError):
            msg = f"Invalid cron expression: {value}"
            logger.error(msg)
            raise ValueError(msg) from None
        return value
