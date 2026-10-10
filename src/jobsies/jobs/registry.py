import functools
from importlib.metadata import entry_points

from loguru import logger

from jobsies.exceptions import DuplicateJobsieError
from jobsies.schemas.config import BaseConfig
from jobsies.schemas.jobs import BaseJobsieInput, BaseJobsieOutput

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
        self.failed_load: dict[str, object] = {}
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
        """Load and validate external jobsie classes from plugin entry points."""
        for entry_point in entry_points(group="jobsies.jobs"):
            try:
                loaded = entry_point.load()
            except Exception as error:  # noqa: BLE001
                self.failed_load[entry_point.name] = error
                logger.warning(f"Failed to load jobsie plugin '{entry_point.name}': {error}")
                continue

            validation_error = self._validate_external_jobsie(loaded)
            if validation_error is not None:
                self.failed_load[entry_point.name] = loaded
                logger.warning(f"Failed to load jobsie plugin '{entry_point.name}': {validation_error}")
                continue

            name = loaded.__name__
            if name in self.registry:
                msg = f"A jobsie named '{name}' is already registered"
                raise DuplicateJobsieError(msg)
            self.registry[name] = loaded

        logger.debug(f"Loaded external jobsie classes: {list(self.registry)}")

    @staticmethod
    def _validate_external_jobsie(loaded: object) -> str | None:
        """Return a validation error for an external jobsie, if one exists."""
        if not isinstance(loaded, type) or not issubclass(loaded, BaseJobsie) or loaded is BaseJobsie:
            return f"expected a BaseJobsie subclass, got {loaded!r}"

        schema_types = (
            ("input_schema", BaseJobsieInput, False),
            ("output_schema", BaseJobsieOutput, False),
            ("config_schema", BaseConfig, True),
        )
        for method_name, schema_base, optional in schema_types:
            try:
                schema = getattr(loaded, method_name)()
            except Exception as error:  # noqa: BLE001
                return f"{method_name}() raised {error!r}"
            if optional and schema is None:
                continue
            if not isinstance(schema, type) or not issubclass(schema, schema_base):
                return f"{method_name}() must return a {schema_base.__name__} subclass"

        return None

    def get(self, name: str) -> type[BaseJobsie]:
        """Retrieve jobsie class by its name."""
        return self.registry[name]


@functools.cache
def get_jobsie_registry() -> JobsieRegistry:
    """Returns singleton instance of the jobsie registry."""
    return JobsieRegistry()
