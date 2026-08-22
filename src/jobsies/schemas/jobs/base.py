from pydantic import BaseModel, model_validator


class BaseJobsieOutput(BaseModel):
    """Base model class for all Jobsies outputs."""

    @model_validator(mode="after")
    def validate_json_serializable(self) -> "BaseJobsieOutput":
        self.model_dump(mode="json")
        return self


class BaseJobsieInput(BaseModel):
    """Base model for all Jobsies inputs."""
