import base64
import hashlib
import json
from importlib import import_module

from cryptography.fernet import Fernet
from pydantic import field_validator
from sqlalchemy import Column, Text
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator
from sqlmodel import Field

from jobsies.settings import get_settings

from .base import TableDefaultModel


class EncryptedJSON(TypeDecorator[dict]):
    """Serialize dictionaries as JSON text and encrypt them when configured."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: dict | None, _dialect: Dialect) -> str | None:
        """Convert a dictionary to its database representation."""
        if value is None:
            return None

        serialized_value = json.dumps(value)
        encryption_key = get_settings().encryption_key
        if encryption_key is None:
            return serialized_value

        key = hashlib.sha256(encryption_key.get_secret_value().encode()).digest()
        fernet = Fernet(base64.urlsafe_b64encode(key))
        return fernet.encrypt(serialized_value.encode()).decode()

    def process_result_value(self, value: str | None, _dialect: Dialect) -> dict | None:
        """Convert database JSON text back to its original dictionary."""
        if value is None:
            return None

        encryption_key = get_settings().encryption_key
        if encryption_key is not None:
            key = hashlib.sha256(encryption_key.get_secret_value().encode()).digest()
            fernet = Fernet(base64.urlsafe_b64encode(key))
            value = fernet.decrypt(value.encode()).decode()

        return json.loads(value)


class TableSharedConfigurations(TableDefaultModel, table=True):
    """Table for storing configurations."""

    __tablename__ = "shared_configurations"

    name: str = Field(
        sa_column=Column(Text, nullable=False, unique=True),
        description="Unique name of the configuration.",
    )
    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="Description of the configuration.",
    )
    config_model: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Fully qualified name of the BaseConfig subclass validating configuration values.",
    )
    config: dict = Field(
        sa_column=Column(EncryptedJSON, nullable=False),
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
