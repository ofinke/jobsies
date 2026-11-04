from abc import ABC, abstractmethod
from typing import ClassVar

from jobsies.schemas.config.base import BaseConfig
from jobsies.schemas.jobs.base import BaseJobsieInput, BaseJobsieOutput


class BaseJobsie(ABC):
    """Base abstract class for Jobsies, all jobsies are children of this class."""

    # Required model attributes are validated when external Jobsies are registered.
    input_model: ClassVar[type[BaseJobsieInput]]
    output_model: ClassVar[type[BaseJobsieOutput]]
    config_model: ClassVar[type[BaseConfig] | None] = None

    def __init__(self) -> None:
        """
        Initializes jobsie with default behaviour.

        By default behaviour, jobsie result is stored in the database.
        """
        # False = store result in database, True = skip result
        self.ignore_result: bool = False

    @abstractmethod
    def execute(self) -> BaseJobsieOutput:
        """
        Contains jobsie execution logic.

        Returns instance of data validated by corresponding output_model
        """
