from functools import cache

from pydantic import BaseModel


class Config(BaseModel):
    """test."""

    scheduler_lookahead: int = 180


@cache
def get_config() -> Config:
    """Retruns cached application configuration."""
    return Config()
