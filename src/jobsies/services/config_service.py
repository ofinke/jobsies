import functools
from datetime import UTC, datetime

from loguru import logger
from sqlalchemy.sql import Select

from jobsies.database import DatabaseHandler, get_db_handler
from jobsies.exceptions import UnavailableConfigError
from jobsies.schemas.config import BaseConfig
from jobsies.schemas.tables import TableSharedConfigurations

from .config_classes import get_config_class_registry


class ConfigService:
    """
    Service for retrieving and managing configurations.

    It is accessed as a singleton entity through get_config_service function. Named configurations are then
    retrieved by get_config_by_name function.
    """

    def __init__(self, db_handler: DatabaseHandler | None = None) -> None:
        """Initialize the service and record configurations with unavailable models."""
        self.db = db_handler or get_db_handler()

        self._detect_failed_loads()

    def _detect_failed_loads(self) -> None:
        """Record configurations whose model is no longer registered."""
        failed_load: dict[str, TableSharedConfigurations] = {}

        for configuration in self.db.load(TableSharedConfigurations):
            try:
                get_config_class_registry().get(configuration.config_model)
            except KeyError:
                failed_load[configuration.name] = configuration
                logger.warning(
                    f"Failed to load configuration '{configuration.name}': "
                    f"configuration model '{configuration.config_model}' is not registered"
                )
                continue

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
        """Validate and persist a configuration."""
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
        """Validate and update a stored configuration, then refresh failed-load detection."""
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
        self._detect_failed_loads()
        logger.info(f"Updated configuration with ID {config_id}")
        return self.get_configuration(config_id)

    def delete_configuration(self, config_id: int) -> bool:
        """Delete a stored configuration and refresh failed-load detection."""
        existing = self.get_configuration(config_id)
        if existing is None:
            return False

        self.db.delete(TableSharedConfigurations, filters={"id": config_id})
        self._detect_failed_loads()
        logger.info(f"Deleted configuration with ID {config_id} and name '{existing.name}'")
        return True

    @staticmethod
    def _validate_config(config_model: str, config: dict) -> dict:
        """Validate configuration values against their registered model and return JSON data."""
        config_class = get_config_class_registry().get(config_model)
        return config_class.model_validate(config).model_dump(mode="json")

    def get(self, name: str) -> BaseConfig:
        """Retrieve configuration by its name."""
        configurations = self.db.load(
            TableSharedConfigurations,
            statement=Select(TableSharedConfigurations).where(TableSharedConfigurations.name == name),
        )
        if not configurations:
            msg = f"Configuration not found: {name}"
            logger.error(msg)
            raise KeyError(msg) from None

        configuration = configurations[0]
        try:
            config_class = get_config_class_registry().get(configuration.config_model)
        except KeyError:
            msg = f"Configuration '{name}' uses unavailable model: {configuration.config_model}"
            logger.error(msg)
            raise UnavailableConfigError(msg) from None

        return config_class.model_validate(configuration.config)


@functools.cache
def get_config_service() -> ConfigService:
    """Singleton of the configuration registy."""
    return ConfigService()


def get_config_by_name(name: str) -> BaseConfig:
    """Function for retrieving named configuration."""
    return get_config_service().get(name)
