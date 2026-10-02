from pydantic import BaseModel, model_validator


class BaseConfig(BaseModel):
    """Base validation model for different configurations."""

    @model_validator(mode="after")
    def validate_json_serializable(self) -> "BaseConfig":
        self.model_dump(mode="json")
        return self
