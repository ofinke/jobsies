# runs the end to end logic of executing a task
# run the execute method, store the output in the databse
from loguru import logger
from sqlalchemy.sql import Select

from jobsies.database.handler import get_db_handler
from jobsies.jobs import get_jobsie_class
from jobsies.schemas.tables import TableJobsiesConfig


def run_jobsie(jobsie_id: int = 1) -> dict:
    """Executes jobsie based on its configuration ID and stores the output into database."""
    # finds jobsie definition in database
    db = get_db_handler()
    configs = db.load(
        TableJobsiesConfig,
        statement=Select(TableJobsiesConfig).where(TableJobsiesConfig.id == jobsie_id),
    )
    if not configs:
        logger.error(f"No jobsie config found with id {jobsie_id}")
        return {}

    # selects correct class to execute
    config = configs[0][0]
    logger.debug(f"Jobsie {config=}")
    cls = get_jobsie_class(config.subclass_name)
    instance = cls(**config.input_kwargs)

    # executes the jobsie
    output = instance.execute()
    logger.debug(output)
    return output
