from unittest.mock import MagicMock

import pytest
from jobsies.config import ConfigRegistry
from jobsies.schemas.config import AppConfig
from jobsies.schemas.tables import TableSharedConfigurations
from pydantic import ValidationError


@pytest.fixture
def mock_db_handler(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Provide a mocked database handler for registry tests."""
    handler = MagicMock()
    monkeypatch.setattr("jobsies.config.get_db_handler", lambda: handler)
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

    registry = ConfigRegistry()

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
        ConfigRegistry()


def test_registry_reports_missing_configuration(mock_db_handler: MagicMock) -> None:
    """Raise a clear lookup error when a configuration name is not registered."""
    mock_db_handler.load.return_value = []
    registry = ConfigRegistry()

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
    registry = ConfigRegistry()

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
