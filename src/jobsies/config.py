import functools

from jobsies.database import get_db_handler
from jobsies.schemas.config import BaseConfig
from jobsies.schemas.tables import TableSharedConfigurations


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
            config_model = next(
                subclass for subclass in BaseConfig.__subclasses__() if subclass.__name__ == configuration.config_model
            )

            self.registry[configuration.name] = config_model.model_validate(configuration.config)

    def get(self, name: str) -> BaseConfig:
        """Retrieve configuration by its name."""
        try:
            return self.registry[name]
        except KeyError:
            msg = f"Configuration not found: {name}"
            raise KeyError(msg) from None


@functools.cache
def get_config_registry() -> ConfigRegistry:
    """Singleton of the configuration registy."""
    return ConfigRegistry()


def get_config_by_name(name: str) -> BaseConfig:
    """Function for retrieving named configuration."""
    return get_config_registry().get(name)
