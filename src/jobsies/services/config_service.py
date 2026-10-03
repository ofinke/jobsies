import functools
from datetime import UTC, datetime

from loguru import logger
from sqlalchemy.sql import Select

from jobsies.database import DatabaseHandler, get_db_handler
from jobsies.schemas.config import BaseConfig
from jobsies.schemas.tables import TableSharedConfigurations

from .config_classes import get_config_class_registry


class ConfigService:
    """
    Service for retrieving and managing configurations.

    It is accessed as a singleton entity through get_config_service function
    """

    def __init__(self, db_handler: DatabaseHandler | None = None) -> None:
        """On initialization, loads all available configurations from database and stores them in internal registry."""
        self.db = db_handler or get_db_handler()

        self.store_and_validate()

    def store_and_validate(self) -> None:
        """Loads configuration from database, validates it with appropriate models and stores it in the registry."""
        registry: dict[str, BaseConfig] = {}
        failed_load: dict[str, TableSharedConfigurations] = {}

        for configuration in self.db.load(TableSharedConfigurations):
            try:
                config_model = get_config_class_registry().get(configuration.config_model)
            except KeyError:
                failed_load[configuration.name] = configuration
                logger.warning(
                    f"Failed to load configuration '{configuration.name}': "
                    f"configuration model '{configuration.config_model}' is not registered"
                )
                continue

            registry[configuration.name] = config_model.model_validate(configuration.config)

        self.registry = registry
        self.failed_load = failed_load

    def list_configurations(self) -> list[TableSharedConfigurations]:
        """Retrieve all stored configurations."""
        return self.db.load(TableSharedConfigurations)

    def get_configuration(self, config_id: int) -> TableSharedConfigurations | None:
        """Retrieve a stored configuration by its ID."""
        configurations = self.db.load(
            TableSharedConfigurations,
            statement=Select(TableSharedConfigurations).where(TableSharedConfigurations.id == config_id),
        )
        return configurations[0] if configurations else None

    def create_configuration(
        self,
        name: str,
        config_model: str,
        config: dict,
        description: str | None = None,
    ) -> TableSharedConfigurations:
        """Validate and persist a configuration, then refresh the cached registry."""
        name = name.strip()
        if not name:
            msg = "Configuration name cannot be empty"
            raise ValueError(msg)

        configuration = TableSharedConfigurations(
            name=name,
            config_model=config_model,
            description=description.strip() or None if description else None,
            config=self._validate_config(config_model, config),
        )
        self.db.store([configuration])
        self.store_and_validate()
        logger.info(f"Created configuration with ID {configuration.id} and name '{configuration.name}'")
        return configuration

    def update_configuration(
        self,
        config_id: int,
        *,
        name: str,
        config_model: str,
        config: dict,
        description: str | None = None,
    ) -> TableSharedConfigurations | None:
        """Validate and update a stored configuration, then refresh the cached registry."""
        existing = self.get_configuration(config_id)
        if existing is None:
            return None

        name = name.strip()
        if not name:
            msg = "Configuration name cannot be empty"
            raise ValueError(msg)

        self.db.update(
            TableSharedConfigurations,
            filters={"id": config_id},
            update_values={
                "name": name,
                "config_model": config_model,
                "description": description.strip() or None if description else None,
                "config": self._validate_config(config_model, config),
                "updated_at": datetime.now(UTC),
            },
        )
        self.store_and_validate()
        logger.info(f"Updated configuration with ID {config_id}")
        return self.get_configuration(config_id)

    def delete_configuration(self, config_id: int) -> bool:
        """Delete a stored configuration and refresh the cached registry."""
        existing = self.get_configuration(config_id)
        if existing is None:
            return False

        self.db.delete(TableSharedConfigurations, filters={"id": config_id})
        self.store_and_validate()
        logger.info(f"Deleted configuration with ID {config_id} and name '{existing.name}'")
        return True

    @staticmethod
    def _validate_config(config_model: str, config: dict) -> dict:
        """Validate configuration values against their registered model and return JSON data."""
        config_class = get_config_class_registry().get(config_model)
        return config_class.model_validate(config).model_dump(mode="json")

    def get(self, name: str) -> BaseConfig:
        """Retrieve configuration by its name."""
        try:
            return self.registry[name]
        except KeyError:
            msg = f"Configuration not found: {name}"
            logger.error(msg)
            raise KeyError(msg) from None


@functools.cache
def get_config_service() -> ConfigService:
    """Singleton of the configuration registy."""
    return ConfigService()


def get_config_by_name(name: str) -> BaseConfig:
    """Function for retrieving named configuration."""
    return get_config_service().get(name)
