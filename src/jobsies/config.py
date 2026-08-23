import functools

from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


class Config(BaseModel):
    """Application configuration."""

    scheduler_lookahead: int = 18000

    templates_location: str = "src/jobsies/templates"


@functools.cache
def get_config() -> Config:
    """Retruns cached application configuration."""
    return Config()


@functools.cache
def get_templates() -> Jinja2Templates:
    return Jinja2Templates(directory=get_config().templates_location)
