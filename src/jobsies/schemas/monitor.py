from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MonitoringWindow(BaseModel):
    """Define which executions are included in a monitoring chart."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["last_executions"] = Field(
        description="Select a fixed number of the latest executions.",
    )
    count: int = Field(
        gt=0,
        description="Number of latest executions to include.",
    )


class OutputMonitor(BaseModel):
    """Define one chart for a field in a Jobsie output."""

    model_config = ConfigDict(extra="forbid")

    # id: str = Field(
    #     min_length=1,
    #     description="Stable identifier for this monitor within its definition.",
    # )
    title: str = Field(
        min_length=1,
        description="Human-readable chart title.",
    )
    field: str = Field(
        min_length=1,
        pattern=r"^(?:/(?:[^~/]|~[01])*)+$",
        description="JSON Pointer to the output field being monitored.",
        examples=["/price_czk"],
    )
    visualization: Literal["line"] = Field(
        description="Chart visualization to use for the selected output field.",
    )
    window: MonitoringWindow = Field(
        description="Executions to include when building the chart.",
    )
    unit: str | None = Field(
        default=None,
        description="Optional unit displayed with the values.",
    )


class OutputMonitoringDefinition(BaseModel):
    """Versioned monitoring configuration for a Jobsie definition."""

    model_config = ConfigDict(extra="forbid")

    version: Literal[1] = Field(
        description="Version of this monitoring configuration format.",
    )
    monitors: list[OutputMonitor] = Field(
        default_factory=list,
        description="Charts to render for this Jobsie definition.",
    )
