from typing import Any

from pydantic import BaseModel, SecretStr, model_validator


class BaseConfig(BaseModel):
    """Base validation model for different configurations."""

    def dump_for_storage(self) -> dict[str, Any]:
        """Return JSON-compatible configuration data with secrets revealed for persistence."""
        json_dump = self.model_dump(mode="json")
        python_dump = self.model_dump(mode="python")
        return self._replace_secrets(json_dump, python_dump)

    @staticmethod
    def _replace_secrets(json_value: Any, python_value: Any) -> Any:
        """Replace JSON-masked secrets using their values from the Python-mode dump."""
        if isinstance(python_value, SecretStr):
            return python_value.get_secret_value()

        if isinstance(json_value, dict) and isinstance(python_value, dict):
            return {
                key: BaseConfig._replace_secrets(value, python_value[key]) if key in python_value else value
                for key, value in json_value.items()
            }

        if isinstance(json_value, list) and isinstance(python_value, (list, tuple)):
            return [
                BaseConfig._replace_secrets(value, python_value[index]) if index < len(python_value) else value
                for index, value in enumerate(json_value)
            ]

        return json_value

    @model_validator(mode="after")
    def validate_json_serializable(self) -> "BaseConfig":
        self.model_dump(mode="json")
        return self
