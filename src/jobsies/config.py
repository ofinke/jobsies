import functools
from importlib.metadata import version

from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


class Config(BaseModel):
    """Application configuration."""

    app_version: str = version("jobsies")

    scheduler_lookahead: int = 1800

    templates_location: str = "src/jobsies/templates"


@functools.cache
def get_config() -> Config:
    """Retruns cached application configuration."""
    return Config()


@functools.cache
def get_templates() -> Jinja2Templates:
    templates = Jinja2Templates(directory=get_config().templates_location)
    templates.env.globals["app_version"] = get_config().app_version
    return templates
