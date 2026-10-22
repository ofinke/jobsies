from random import randint

from loguru import logger

from jobsies.schemas.jobs import BaseJobsieInput, ExampleJobsieOutput

from .base import BaseJobsie


class ExampleJobsie(BaseJobsie):
    """An example jobsie returns 'Hello World!' and a random integer."""

    input_model = BaseJobsieInput
    output_model = ExampleJobsieOutput

    def execute(self) -> ExampleJobsieOutput:
        """Retrieves status and content of example.com."""
        logger.debug("Example jobsie executed!")
        return self.output_model(content="Hello World!", number=randint(0, 9))  # noqa: S311
