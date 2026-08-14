from celery import Celery

from jobsies.runner import run_jobsie

app = Celery(
    "jobsies",
    broker="redis://localhost:6379/0",
    include=["jobsies.celery_app"],
)


@app.task()
def task_wrapper_run_jobsie(jid: int = 1) -> dict:
    """Wrap execute_save_jobsie as a Celery task."""
    return run_jobsie(jid)
