from functools import cache

from pydantic import BaseModel


class Config(BaseModel):
    """test."""


@cache
def get_config() -> Config:
    """Retruns cached application configuration."""
    return Config()
