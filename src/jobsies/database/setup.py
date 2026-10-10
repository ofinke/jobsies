import json
from pathlib import Path

from loguru import logger
from sqlalchemy import UniqueConstraint, inspect, select
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel

from jobsies.database.handler import get_db_handler
from jobsies.jobs import get_jobsie_registry
from jobsies.schemas.config import AppConfig
from jobsies.schemas.tables import TableJobsiesDefinition, TableSharedConfigurations

DEFAULT_JOBSIES_CONFIG_PATH = Path(__file__).resolve().parents[3] / "configs" / "default_jobsies_configs.json"


def setup_database() -> None:
    """Create and validate database tables, then seed default configurations and jobsies."""
    # Import every table model before creating the metadata tables.
    import jobsies.schemas.tables  # noqa: F401, PLC0415

    logger.info("Starting database setup")
    engine = get_db_handler().engine
    SQLModel.metadata.create_all(bind=engine)
    _validate_schema(engine)
    _seed_app_config(engine)
    _seed_default_jobsies(engine)
    logger.info("Database setup completed")


def _validate_schema(engine: Engine) -> None:
    """Raise an error if any database table differs from its current SQLModel definition."""
    inspector = inspect(engine)
    differences: list[str] = []

    for table in SQLModel.metadata.sorted_tables:
        table_name = table.name
        actual_columns = {column["name"]: column for column in inspector.get_columns(table_name)}
        expected_columns = {column.name: column for column in table.columns}
        if actual_columns.keys() != expected_columns.keys():
            differences.append(
                f"{table_name}: columns differ (expected {sorted(expected_columns)}, found {sorted(actual_columns)})"
            )
            continue

        for column_name, expected in expected_columns.items():
            actual = actual_columns[column_name]
            expected_type = expected.type.compile(dialect=engine.dialect)
            actual_type = actual["type"].compile(dialect=engine.dialect)
            if expected_type != actual_type:
                differences.append(f"{table_name}.{column_name}: expected type {expected_type}, found {actual_type}")
            if expected.nullable != actual["nullable"]:
                differences.append(
                    f"{table_name}.{column_name}: expected nullable={expected.nullable}, "
                    f"found nullable={actual['nullable']}"
                )

        expected_primary_key = sorted(column.name for column in table.primary_key.columns)
        actual_primary_key = sorted(inspector.get_pk_constraint(table_name)["constrained_columns"] or [])
        if expected_primary_key != actual_primary_key:
            differences.append(f"{table_name}: expected primary key {expected_primary_key}, found {actual_primary_key}")

        expected_unique_constraints = {
            tuple(sorted(constraint.columns.keys()))
            for constraint in table.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        actual_unique_constraints = {
            tuple(sorted(constraint["column_names"]))
            for constraint in inspector.get_unique_constraints(table_name)
            if constraint["column_names"]
        }
        if expected_unique_constraints != actual_unique_constraints:
            differences.append(
                f"{table_name}: expected unique constraints {sorted(expected_unique_constraints)}, "
                f"found {sorted(actual_unique_constraints)}"
            )

    if differences:
        msg = "Database schema does not match the current table definitions:\n- " + "\n- ".join(differences)
        raise RuntimeError(msg)


def _seed_app_config(engine: Engine) -> None:
    """Insert the default app configuration when it is not already stored."""
    with Session(engine) as session:
        existing = session.exec(
            select(TableSharedConfigurations).where(TableSharedConfigurations.name == "app-config")
        ).first()
        if existing is not None:
            logger.debug("Default app configuration already exists")
            return

        session.add(
            TableSharedConfigurations(
                name="app-config",
                config_model=AppConfig.__name__,
                config=AppConfig().model_dump(mode="json"),
            )
        )
        session.commit()
        logger.info("Seeded default app configuration")


def _seed_default_jobsies(engine: Engine) -> None:
    """Insert default jobsie definitions that are not already present in the database."""
    with DEFAULT_JOBSIES_CONFIG_PATH.open(encoding="utf-8") as config_file:
        definitions = json.load(config_file)

    jobsie_registry = get_jobsie_registry()
    seeded_names: list[str] = []
    with Session(engine) as session:
        for definition in definitions:
            existing = session.exec(
                select(TableJobsiesDefinition).where(
                    TableJobsiesDefinition.name == definition["name"],
                    TableJobsiesDefinition.subclass_name == definition["subclass_name"],
                )
            ).first()
            if existing is not None:
                logger.debug(f"Default jobsie '{definition['name']}' already exists")
                continue

            jobsie_class = jobsie_registry.get(definition["subclass_name"])
            definition["output_vars"] = jobsie_class.output_schema().model_json_schema()
            session.add(TableJobsiesDefinition(**definition))
            seeded_names.append(definition["name"])

        if seeded_names:
            session.commit()
            logger.info(f"Seeded default jobsies: {seeded_names}")


if __name__ == "__main__":
    setup_database()
