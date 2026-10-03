from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from jobsies.schemas.config import AppConfig, BaseConfig
from jobsies.schemas.tables import TableSharedConfigurations
from jobsies.services.config_classes import ConfigClassRegistry
from jobsies.services.config_service import ConfigService
from pydantic import SecretStr, ValidationError
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlmodel import Session, select


@pytest.fixture
def mock_db_handler(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Provide a mocked database handler for registry tests."""
    handler = MagicMock()
    monkeypatch.setattr("jobsies.services.config_service.get_db_handler", lambda: handler)
    return handler


def test_registry_loads_and_validates_config(mock_db_handler: MagicMock) -> None:
    """Load stored values as an instance of the configuration model."""
    mock_db_handler.load.return_value = [
        TableSharedConfigurations(
            name="app-config",
            config_model="AppConfig",
            config={"worker_concurrency": 4},
        )
    ]

    registry = ConfigService()

    config = registry.get("app-config")

    assert isinstance(config, AppConfig)
    assert config.worker_concurrency == 4


def test_registry_rejects_invalid_config_values(mock_db_handler: MagicMock) -> None:
    """Reject stored values that do not validate against their configuration model."""
    mock_db_handler.load.return_value = [
        TableSharedConfigurations(
            name="app-config",
            config_model="AppConfig",
            config={"worker_concurrency": "not-an-integer"},
        )
    ]

    with pytest.raises(ValidationError):
        ConfigService()


def test_registry_reports_missing_configuration(mock_db_handler: MagicMock) -> None:
    """Raise a clear lookup error when a configuration name is not registered."""
    mock_db_handler.load.return_value = []
    registry = ConfigService()

    with pytest.raises(KeyError, match="Configuration not found: missing"):
        registry.get("missing")


def test_registry_reload_replaces_stored_configurations(mock_db_handler: MagicMock) -> None:
    """Replace cached entries when configurations are loaded again."""
    mock_db_handler.load.return_value = [
        TableSharedConfigurations(
            name="old-config",
            config_model="AppConfig",
            config={},
        )
    ]
    registry = ConfigService()

    mock_db_handler.load.return_value = [
        TableSharedConfigurations(
            name="new-config",
            config_model="AppConfig",
            config={"worker_concurrency": 3},
        )
    ]
    registry.store_and_validate()

    with pytest.raises(KeyError, match="Configuration not found: old-config"):
        registry.get("old-config")
    assert registry.get("new-config").worker_concurrency == 3


def test_registry_tracks_configurations_with_missing_models(
    mock_db_handler: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep configurations whose plugin model is no longer registered in failed_load."""
    configuration = TableSharedConfigurations(
        name="plugin-config",
        config_model="AppConfig",
        config={"setting": "value"},
    )
    configuration.config_model = "RemovedPluginConfig"
    mock_db_handler.load.return_value = [configuration]

    class MissingConfigRegistry:
        """Simulate a config class registry without the removed plugin model."""

        def get(self, _name: str) -> type[BaseConfig]:
            """Raise when the removed model is requested."""
            msg = "Configuration class not found: RemovedPluginConfig"
            raise KeyError(msg)

    monkeypatch.setattr(
        "jobsies.services.config_service.get_config_class_registry",
        MissingConfigRegistry,
    )

    registry = ConfigService()

    assert registry.registry == {}
    assert registry.failed_load == {"plugin-config": configuration}


def test_configuration_rejects_unknown_model() -> None:
    """Reject configuration rows that name an unregistered model."""
    with pytest.raises(TypeError, match="BaseConfig subclass"):
        TableSharedConfigurations.model_validate(
            {
                "name": "test-config",
                "config_model": "MissingConfig",
                "config": {},
            }
        )


def test_configuration_is_stored_as_json_text(
    monkeypatch: pytest.MonkeyPatch,
    test_db: Engine,
) -> None:
    """Store configuration dictionaries as JSON strings and load them as dictionaries."""
    monkeypatch.setattr(
        "jobsies.schemas.tables.config.get_settings",
        lambda: SimpleNamespace(encryption_key=None),
    )
    configuration = {"worker_concurrency": 4}

    with Session(test_db) as session:
        session.add(TableSharedConfigurations(name="json-config", config_model="AppConfig", config=configuration))
        session.commit()

        stored_value = session.execute(
            text("SELECT config FROM shared_configurations WHERE name = :name"),
            {"name": "json-config"},
        ).scalar_one()
        loaded_configuration = session.exec(
            select(TableSharedConfigurations).where(TableSharedConfigurations.name == "json-config")
        ).one()

    assert stored_value == '{"worker_concurrency": 4}'
    assert loaded_configuration.config == configuration


def test_configuration_is_encrypted_in_database(
    monkeypatch: pytest.MonkeyPatch,
    test_db: Engine,
) -> None:
    """Encrypt configuration JSON in storage and decrypt it when loading the row."""
    monkeypatch.setattr(
        "jobsies.schemas.tables.config.get_settings",
        lambda: SimpleNamespace(encryption_key=SecretStr("test-encryption-key")),
    )
    configuration = {"secret": "private-value"}

    with Session(test_db) as session:
        session.add(TableSharedConfigurations(name="encrypted-config", config_model="AppConfig", config=configuration))
        session.commit()

        stored_value = session.execute(
            text("SELECT config FROM shared_configurations WHERE name = :name"),
            {"name": "encrypted-config"},
        ).scalar_one()
        loaded_configuration = session.exec(
            select(TableSharedConfigurations).where(TableSharedConfigurations.name == "encrypted-config")
        ).one()

    assert "private-value" not in stored_value
    assert loaded_configuration.config == configuration


def test_config_class_registry_loads_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
    """Load configuration classes exposed by the plugin entry-point group."""

    class PluginConfig(BaseConfig):
        """Configuration class supplied by a plugin."""

    entry_point = SimpleNamespace(name="plugin-config", load=lambda: PluginConfig)
    monkeypatch.setattr("jobsies.services.config_classes.entry_points", lambda **_: [entry_point])

    registry = ConfigClassRegistry()

    assert registry.get("PluginConfig") is PluginConfig


def test_config_class_registry_loads_local_subclasses(monkeypatch: pytest.MonkeyPatch) -> None:
    """Automatically register local configuration subclasses."""

    class LocalConfig(BaseConfig):
        """Configuration class defined within the application."""

    monkeypatch.setattr("jobsies.services.config_classes.entry_points", lambda **_: [])

    registry = ConfigClassRegistry()

    assert registry.get("LocalConfig") is LocalConfig


def test_config_class_registry_tracks_invalid_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep plugin entry-point values that are not BaseConfig subclasses in failed_load."""
    entry_point = SimpleNamespace(name="invalid-config", load=lambda: object)
    monkeypatch.setattr("jobsies.services.config_classes.entry_points", lambda **_: [entry_point])

    registry = ConfigClassRegistry()

    assert registry.failed_load == {"invalid-config": object}
