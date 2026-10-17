from pydantic import Field

from .base import BaseJobsieOutput


class ExampleJobsieOutput(BaseJobsieOutput):
    """Data model for output of ExampleJobsie."""

    content: str = Field(
        description="Output content of the Jobsie",
    )
    number: int = Field(
        ge=0,
        le=9,
        description="Random integer between 0 and 9",
    )
