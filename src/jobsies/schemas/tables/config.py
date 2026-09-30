from importlib import import_module

from pydantic import field_validator
from sqlalchemy import Column, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlmodel import Field

from .base import TableDefaultModel


class TableSharedConfigurations(TableDefaultModel, table=True):
    """Table for storing configurations."""

    __tablename__ = "shared_configurations"

    name: str = Field(
        sa_column=Column(Text, nullable=False, unique=True),
        description="Unique name of the configuration.",
    )
    config_model: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Fully qualified name of the BaseConfig subclass validating configuration values.",
    )
    config: dict = Field(
        sa_column=Column(JSON, nullable=False),
        description="Stored configuration values",
    )

    @field_validator("config_model")
    @classmethod
    def validate_config_model(cls, value: str) -> str:
        """Ensure the configured model resolves to a BaseConfig subclass."""
        try:
            import_module("jobsies.config").get_config_class_registry().get(value)
        except KeyError:
            msg = f"Configuration model must be a BaseConfig subclass: {value}"
            raise TypeError(msg) from None

        return value
