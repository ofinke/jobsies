import pytest
from jobsies.schemas.tables import TableSharedConfigurations
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session


def test_configuration_name_is_unique_in_sqlite(test_db: Engine) -> None:
    """The database rejects shared configurations with duplicate names."""
    configuration = TableSharedConfigurations(
        name="test-config",
        config_model="AppConfig",
        config={},
    )
    with Session(test_db) as session:
        session.add(configuration)
        session.commit()
        session.add(
            TableSharedConfigurations(
                name="test-config",
                config_model="AppConfig",
                config={},
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_configuration_model_can_be_loaded_by_class_name() -> None:
    """The built-in application configuration can be referenced by class name."""
    configuration = TableSharedConfigurations.model_validate(
        {
            "name": "app-config",
            "config_model": "AppConfig",
            "config": {},
        }
    )

    assert configuration.config_model == "AppConfig"


def test_configuration_model_must_exist() -> None:
    """An unknown configuration class name is rejected."""
    with pytest.raises(TypeError, match="BaseConfig subclass"):
        TableSharedConfigurations.model_validate(
            {
                "name": "test-config",
                "config_model": "MissingConfig",
                "config": {},
            }
        )
