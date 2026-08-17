from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RunnerExecutionMetadata(BaseModel):
    """Metadata created during the jobsie execution included in the output table."""

    model_config = ConfigDict(validate_assignment=True)

    execution_id: str
    execution_method: Literal["direct_call", "celery"]
    traceback: str | None = Field(
        default=None,
        description="Traceback string if the execution failed, otherwise None",
    )
