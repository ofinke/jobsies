import functools
from importlib.metadata import version

from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Application configuration."""

    app_version: str = Field(
        default=version("jobsies"),
        description="Application version extracted from the pyproject",
    )
    scheduler_lookahead: int = Field(
        default=900,
        description="How often the worker schedules tasks ahead",
    )
    scheduler_interval: int = Field(
            default=450,
            description="How often the scheduler runs",
        )
    task_queue_name: str = Field(
        default="celery",
        description="Redis queue used by Celery tasks",
    )
    templates_location: str = Field(
        default="src/jobsies/templates",
        description="Location of Jinja templates",
    )


@functools.cache
def get_config() -> Config:
    """Retruns cached application configuration."""
    return Config()


@functools.cache
def get_templates() -> Jinja2Templates:
    templates = Jinja2Templates(directory=get_config().templates_location)
    templates.env.globals["app_version"] = get_config().app_version
    return templates
