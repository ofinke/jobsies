from datetime import datetime

from pydantic import BaseModel, Field


class JobsieOutputBase(BaseModel):
    """Pydantic model for a jobsie output entry, mirroring TableJobsiesOutputs."""

    id: int = Field(
        description="Primary key of the output record",
    )
    jobsie_name: str = Field(
        description="Name of the jobsie that produced this output",
    )
    jobsie_id: int = Field(
        description="ID of the jobsie which produced the output",
    )
    execution_id: str = Field(
        description="Unique identifier of the execution run",
    )
    retention: datetime | None = Field(
        default=None,
        description="Retention date; None means keep indefinitely",
    )
    success: bool = Field(
        description="Whether the execution succeeded",
    )
    output_data: dict = Field(
        description="Output data produced by the jobsie execution",
    )
    execution_metadata: dict = Field(
        description="Metadata about the execution",
    )
