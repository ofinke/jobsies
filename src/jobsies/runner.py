# runs the end to end logic of executing a task
# run the execute method, store the output in the databse
from loguru import logger

from jobsies.jobs import ZalandoJobsie


def execute_save_jobsie(jobsie_id: int = 1) -> dict:
    """Executes jobsie based on its configuration ID and stores the output into database."""
    return
