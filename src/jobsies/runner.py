# runs the end to end logic of executing a task
# run the execute method, store the output in the databse
import traceback
from uuid import uuid4

from loguru import logger
from sqlalchemy.sql import Select

from jobsies.database.handler import get_db_handler
from jobsies.jobs import get_jobsie_class
from jobsies.schemas.runner import RunnerExecutionMetadata
from jobsies.schemas.tables import TableJobsiesConfig, TableJobsiesOutputs


def _upload_result_to_db(jobsie_config: dict, output_data: dict, execution_metadata: RunnerExecutionMetadata) -> None:
    """Helper funtion for uploading data into database."""
    data = TableJobsiesOutputs(
        jobsie_name=jobsie_config.get("name", "UNKNOWN") if isinstance(jobsie_config, dict) else jobsie_config.name,
        jobsie_id=jobsie_config.get("id", 0) if isinstance(jobsie_config, dict) else jobsie_config.id,
        execution_id=execution_metadata.execution_id,
        retention=None,
        output_data=output_data,
        execution_metadata=execution_metadata.model_dump(exclude=["execution_id"]),
        success=execution_metadata.traceback is None,
    )

    db = get_db_handler()
    db.store([data])


def _get_default_execution_metadata() -> dict:
    """Generates default execution metadata."""
    return RunnerExecutionMetadata(execution_id=str(uuid4()), execution_method="direct_call")


def _get_jobsie_configuration(jobsie_id: int) -> TableJobsiesConfig:
    """
    Wrapper for retrieving jobsie configuration.

    Done in a wrapper function to avoid "raise-within-try" linting rule in the main function.
    """
    db = get_db_handler()
    jobsie_configs = db.load(
        TableJobsiesConfig,
        statement=Select(TableJobsiesConfig).where(TableJobsiesConfig.id == jobsie_id),
    )
    if not jobsie_configs:
        msg = f"No jobsie config found with id {jobsie_id}"
        logger.error(msg)
        raise ValueError(msg)
    return jobsie_configs[0]


def run_dynamic_jobsie(jobsie_id: int, *, execution_metadata: dict | None = None) -> None:
    """Executes jobsie based on its configuration ID and stores the output into database."""
    # If the execution layer doesn't provide execution_metadata, generate default ones or validate the input.
    if not execution_metadata:
        execution_metadata = _get_default_execution_metadata()
    else:
        execution_metadata = RunnerExecutionMetadata(**execution_metadata)

    # First we define empty config and output to handle cases where it fails somewhere
    jobsie_config = {}
    output = {}

    # Whole jobsie execution is done in a single Try / Except block so if anything fails, the attempt is logged
    try:
        # selects correct class to execute
        jobsie_config = _get_jobsie_configuration(jobsie_id)
        logger.debug(f"Jobsie {jobsie_config=}")
        cls = get_jobsie_class(jobsie_config.subclass_name)
        instance = cls(**jobsie_config.input_kwargs)

        # executes the jobsie
        output = instance.execute()
        logger.debug(f"Jobsie finished with output: {output=}")

    except Exception as err:
        logger.error(f"Jobsie execution failed with {err!s}")
        # Prepare the execution output
        execution_metadata.traceback = "".join(traceback.format_exception(err))
        raise

    finally:
        # Store result in database
        _upload_result_to_db(jobsie_config, output, execution_metadata)
