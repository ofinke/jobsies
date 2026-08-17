from loguru import logger

from jobsies.schemas.jobs import ExampleJobsieOutput

from .base import BaseJobsie


class ExampleJobsie(BaseJobsie):
    """An example jobsie returns string 'Hello World!'."""

    output_schema = ExampleJobsieOutput

    def execute(self) -> ExampleJobsieOutput:
        """Retrieves status and content of example.com."""
        logger.debug("Example jobsie executed!")
        return self.output_schema(content="Hello World!")
