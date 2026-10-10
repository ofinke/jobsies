from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RunnerExecutionMetadata(BaseModel):
    """Metadata created during the jobsie execution included in the output table."""

    model_config = ConfigDict(validate_assignment=True)

    execution_id: str = Field(
        description="UUID4 of the execution",
    )
    execution_method: Literal["direct_call", "celery"]
    duration: float = Field(
        default=0.0,
        ge=0,
        description="Jobsie execution duration in seconds",
    )
    traceback: str | None = Field(
        default=None,
        description="Traceback string if the execution failed, otherwise None",
    )
