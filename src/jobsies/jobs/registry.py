import functools

from loguru import logger

from jobsies.exceptions import DuplicateJobsieError

from .base import BaseJobsie
from .example import ExampleJobsie
from .flights import FlightPriceJobsie
from .zalando import ZalandoJobsie


class JobsieRegistry:
    """
    Creates mapping registry of all available jobsies.

    Source for the registry is locally available jobsies and jobsies installed via
    the plugin system.
    """

    def __init__(self) -> None:
        """Creates and fills the registry."""
        self.registry: dict[str, type[BaseJobsie]] = {}
        self._local_load()
        self._external_load()

    def _local_load(self) -> None:
        """Loads all local jobsie classes."""
        jobsie_classes = (ExampleJobsie, FlightPriceJobsie, ZalandoJobsie)
        for jobsie_class in jobsie_classes:
            name = jobsie_class.__name__
            if name in self.registry:
                msg = f"A jobsie named '{name}' is already registered"
                raise DuplicateJobsieError(msg)
            self.registry[name] = jobsie_class

        logger.debug(f"Loaded local jobsie classes: {list(self.registry)}")

    def _external_load(self) -> None:
        """Load and validate external jobsie classes when plugin support is implemented."""

    def get(self, name: str) -> type[BaseJobsie]:
        """Retrieve jobsie class by its name."""
        return self.registry[name]


@functools.cache
def get_jobsie_registry() -> JobsieRegistry:
    """Returns singleton instance of the jobsie registry."""
    return JobsieRegistry()
