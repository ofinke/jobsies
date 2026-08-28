import traceback
from uuid import uuid4

from loguru import logger
from sqlalchemy.sql import Select

from jobsies.database import get_db_handler
from jobsies.jobs import get_jobsie_class
from jobsies.schemas.runner import RunnerExecutionMetadata
from jobsies.schemas.tables import TableJobsiesDefinition, TableJobsiesOutputs


class RunnerService:
    """
    Execution layer for jobsies execution.

    Single source of truth for the execution. Method of execution can vary.
    """

    @property
    def _default_execution_metadata() -> dict:
        """Generates default execution metadata."""
        return RunnerExecutionMetadata(execution_id=str(uuid4()), execution_method="direct_call")

    def _upload_result_to_db(
        self,
        jobsie_config: dict,
        output_data: dict,
        execution_metadata: RunnerExecutionMetadata,
    ) -> None:
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

    def _get_jobsie_configuration(self, jobsie_id: int) -> TableJobsiesDefinition:
        """Retrieve jobsie configuration based on its ID."""
        db = get_db_handler()
        jobsie_configs = db.load(
            TableJobsiesDefinition,
            statement=Select(TableJobsiesDefinition).where(TableJobsiesDefinition.id == jobsie_id),
        )
        if not jobsie_configs:
            msg = f"No jobsie config found with id {jobsie_id}"
            logger.error(msg)
            raise ValueError(msg)
        return jobsie_configs[0]

    def run_dynamic_jobsie(self, jobsie_id: int, *, execution_metadata: dict | None = None) -> None:
        """Executes jobsie based on its configuration ID and stores the output into database."""
        # If the execution layer doesn't provide execution_metadata, generate default ones or validate the input.
        if not execution_metadata:
            execution_metadata = self._default_execution_metadata()
        else:
            execution_metadata = RunnerExecutionMetadata(**execution_metadata)

        # First we define empty config and output to handle cases where it fails somewhere
        jobsie_config = {}
        output = {}

        # Whole jobsie execution is done in a single Try / Except block so if anything fails, the attempt is logged
        try:
            # selects correct class to execute
            jobsie_config = self._get_jobsie_configuration(jobsie_id)
            cls = get_jobsie_class(jobsie_config.subclass_name)
            instance = cls(**jobsie_config.input_kwargs)

            # executes the jobsie
            output = instance.execute()
            logger.debug(f"Jobsie ID: '{jobsie_config.id}', name: '{jobsie_config.name}' finished succesfful")

        except Exception as err:
            logger.error(f"Jobsie execution failed with {err!s}")
            # Prepare the execution output
            execution_metadata.traceback = "".join(traceback.format_exception(err))
            raise

        finally:
            # Convert model to dict for DB storage
            output_data = output.model_dump() if not isinstance(output, dict) else output
            # Store result in database
            self._upload_result_to_db(jobsie_config, output_data, execution_metadata)
