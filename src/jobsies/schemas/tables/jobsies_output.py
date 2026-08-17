# unified table for jobsies output
# ideas for columns - name, json output, retention (days, 0 infinite)

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlmodel import Field

from .base import TableDefaultModel


class TableJobsiesOutputs(TableDefaultModel, table=True):
    """Data structure for storing results from Jobsies executions."""

    __tablename__ = "data_outputs"

    # Information about jobsie executed
    jobsie_name: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Name of the jobsie that produced this output",
    )
    jobsie_id: int = Field(
        sa_column=Column(Integer, nullable=False),
        description="ID of the jobsie which produced the output",
    )
    execution_id: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Unique identifier of the execution run",
    )
    retention: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True),
        description="Retention date; None means keep indefinitely",
    )
    success: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False),
        description="Whether the execution succeeded",
    )

    # execution data
    output_data: dict = Field(
        sa_column=Column(JSON, nullable=False),
        description="Output data produced by the jobsie execution",
    )
    execution_metadata: dict = Field(
        sa_column=Column(JSON, nullable=False),
        description="Metadata about the execution",
    )
