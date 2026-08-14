import json
from pathlib import Path

from jobsies.database.handler import get_db_handler
from jobsies.schemas.tables import TableJobsiesConfig

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "default_jobsies_configs.json"


def main() -> None:
    """Populate the database with default jobsies configs."""
    with Path.open(DATA_PATH) as f:
        config_raw = json.load(f)

    configs = [TableJobsiesConfig(**config) for config in config_raw]

    db = get_db_handler()
    db.store(configs)


if __name__ == "__main__":
    main()
