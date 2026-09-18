from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ResponseHealthLiveness(BaseModel):
    """Schema for the response of the liveness check."""

    status: str = Field(
        description="Liveness status of the application",
        examples=["UP"],
    )
    timestamp: str = Field(
        description="Timestamp of the request",
        examples=[datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S%z")],
    )


class ResponseHealthReadiness(BaseModel):
    """Schema for the response of the readiness check."""

    status: str = Field(
        description="Overall readiness status of the application dependencies",
        examples=["UP", "DOWN"],
    )
    timestamp: str = Field(
        description="Timestamp of the request",
        examples=[datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S%z")],
    )
    components: dict[str, str] = Field(
        description="Readiness status of each application dependency",
        examples=[{"database": "UP", "redis": "DOWN"}],
    )
