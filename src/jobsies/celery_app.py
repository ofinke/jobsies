from celery import Celery

from jobsies.runner import execute_save_jobsie

app = Celery(
    "jobsies",
    broker="redis://localhost:6379/0",
    include=["jobsies.celery_app"],
)


@app.task()
def task_wrapper_jobsie_execute(jid: int = 1) -> dict:
    """Wrap execute_save_jobsie as a Celery task."""
    return execute_save_jobsie(jid)
