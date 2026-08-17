import json
from pathlib import Path

import click

from jobsies.database.handler import get_db_handler
from jobsies.jobs.base import BaseJobsie
from jobsies.schemas.tables import TableJobsiesConfig

DEFAULT_DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "default_jobsies_configs.json"
DATA_DIR = DEFAULT_DATA_PATH.parent


def _get_output_schema_for_subclass(subclass_name: str) -> dict:
    """Retrieve output schema from the matching BaseJobsie subclass."""
    cls = BaseJobsie.__subclasses__()
    mapping = {c.__name__: c for c in cls}
    return mapping[subclass_name].output_schema.model_json_schema()


@click.command()
@click.option(
    "--file",
    "-f",
    default="default_jobsies_configs",
    help="Name of the JSON file in the data directory (without .json extension).",
)
def main(file: str) -> None:
    """Populate the database with jobsies configs from a JSON file."""
    data_path = DATA_DIR / f"{file}.json"

    if not data_path.exists():
        msg = f"Config file not found: {data_path}"
        raise FileNotFoundError(msg)

    with Path.open(data_path) as f:
        config_raw = json.load(f)

    for config in config_raw:
        config["output_vars"] = _get_output_schema_for_subclass(config["subclass_name"])

    configs = [TableJobsiesConfig(**config) for config in config_raw]

    db = get_db_handler()
    db.store(configs)


if __name__ == "__main__":
    main()
