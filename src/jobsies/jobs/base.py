from abc import ABC, abstractmethod

from jobsies.schemas.config.base import BaseConfig
from jobsies.schemas.jobs.base import BaseJobsieInput, BaseJobsieOutput


class BaseJobsie(ABC):
    """Base abstract class for Jobsies, all jobsies are children of this class."""

    def __init__(self) -> None:
        """Does something."""
        super().__init__()

    @classmethod
    @abstractmethod
    def config_schema(cls) -> type[BaseConfig] | None:
        """Return schema of jobsie configuration if it exists, or None if it doesnt."""

    @classmethod
    @abstractmethod
    def output_schema(cls) -> type[BaseJobsieOutput]:
        """Return the output model class for this Jobsie."""

    @classmethod
    @abstractmethod
    def input_schema(cls) -> type[BaseJobsieInput]:
        """Return the input model class for this Jobsie."""

    @abstractmethod
    def execute(self) -> BaseJobsieOutput:
        """Actually does something."""
