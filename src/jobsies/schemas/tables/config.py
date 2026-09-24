from pydantic import field_validator
from sqlalchemy import Column, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlmodel import Field

from jobsies.schemas.config import BaseConfig

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
        config_model = next(
            (subclass for subclass in BaseConfig.__subclasses__() if subclass.__name__ == value),
            None,
        )

        if not isinstance(config_model, type) or not issubclass(config_model, BaseConfig):
            msg = f"Configuration model must be a BaseConfig subclass: {value}"
            raise TypeError(msg)

        return value
