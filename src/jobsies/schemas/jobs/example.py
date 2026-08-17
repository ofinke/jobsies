from pydantic import Field

from .base import BaseJobsieOutput


class ExampleJobsieOutput(BaseJobsieOutput):
    """Data model for output of ExampleJobsie."""

    content: str = Field(
        description="Output content of the Jobsie",
    )
