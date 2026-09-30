import functools
from importlib.metadata import entry_points

from loguru import logger

from jobsies.database import get_db_handler
from jobsies.schemas.config import BaseConfig
from jobsies.schemas.tables import TableSharedConfigurations


class ConfigClassRegistry:
    """Registry of available configuration classes."""

    def __init__(self) -> None:
        """Create and populate the registry with built-in and plugin classes."""
        self.registry: dict[str, type[BaseConfig]] = {}
        self.failed_load: dict[str, object] = {}
        self._local_load()
        self._external_load()

    def _register(self, config_class: type[BaseConfig]) -> None:
        """Register a configuration class by its class name."""
        name = config_class.__name__
        if name in self.registry:
            if self.registry[name] is config_class:
                return
            msg = f"A configuration class named '{name}' is already registered"
            logger.error(msg)
            raise ValueError(msg)
        self.registry[name] = config_class

    def _local_load(self) -> None:
        """Load local configuration classes derived from BaseConfig."""
        for config_class in BaseConfig.__subclasses__():
            self._register(config_class)
        logger.debug(f"Loaded local configuration classes: {list(self.registry)}")

    def _external_load(self) -> None:
        """Load plugin classes and track values that are not BaseConfig subclasses."""
        for entry_point in entry_points(group="jobsies.config"):
            loaded = entry_point.load()
            if not isinstance(loaded, type) or not issubclass(loaded, BaseConfig) or loaded is BaseConfig:
                self.failed_load[entry_point.name] = loaded
                logger.warning(
                    f"Failed to load configuration plugin '{entry_point.name}': "
                    f"expected a BaseConfig subclass, got {loaded!r}"
                )
                continue
            self._register(loaded)

    def get(self, name: str) -> type[BaseConfig]:
        """Retrieve a configuration class by its name."""
        try:
            return self.registry[name]
        except KeyError:
            msg = f"Configuration class not found: {name}"
            logger.error(msg)
            raise KeyError(msg) from None


@functools.cache
def get_config_class_registry() -> ConfigClassRegistry:
    """Return the cached singleton configuration class registry."""
    return ConfigClassRegistry()


class ConfigRegistry:
    """Registry of reusable configurations used accross the application."""

    def __init__(self) -> None:
        """On initialization, loads all available configurations from database and stores them in internal registry."""
        self.store_and_validate()

    def store_and_validate(self) -> None:
        """Loads configuration from database, validates it with appropriate models and stores it in the registry."""
        # Clear existing registry
        self.registry: dict[str, BaseConfig] = {}

        for stored_configuration in get_db_handler().load(TableSharedConfigurations):
            configuration = TableSharedConfigurations.model_validate(stored_configuration)
            # NOTE: here we have to handle case where we uninstall plugin which contains configuration definition
            config_model = get_config_class_registry().get(configuration.config_model)

            self.registry[configuration.name] = config_model.model_validate(configuration.config)

    def get(self, name: str) -> BaseConfig:
        """Retrieve configuration by its name."""
        try:
            return self.registry[name]
        except KeyError:
            msg = f"Configuration not found: {name}"
            logger.error(msg)
            raise KeyError(msg) from None


@functools.cache
def get_config_registry() -> ConfigRegistry:
    """Singleton of the configuration registy."""
    return ConfigRegistry()


def get_config_by_name(name: str) -> BaseConfig:
    """Function for retrieving named configuration."""
    return get_config_registry().get(name)
