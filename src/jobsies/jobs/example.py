from random import randint

from loguru import logger

from jobsies.schemas.jobs import BaseJobsieInput, ExampleJobsieOutput

from .base import BaseJobsie


class ExampleJobsie(BaseJobsie):
    """An example jobsie returns 'Hello World!' and a random integer."""

    @classmethod
    def config_schema(cls) -> None:
        """Returns None as this jobsie doesn't have any configuration."""

    @classmethod
    def output_schema(cls) -> type[ExampleJobsieOutput]:
        """Return this jobsie's output model class."""
        return ExampleJobsieOutput

    @classmethod
    def input_schema(cls) -> type[BaseJobsieInput]:
        """Return this jobsie's input model class."""
        return BaseJobsieInput

    def execute(self) -> ExampleJobsieOutput:
        """Retrieves status and content of example.com."""
        logger.debug("Example jobsie executed!")
        return self.output_schema()(content="Hello World!", number=randint(0, 9))  # noqa: S311
