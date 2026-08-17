from functools import cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """test."""

    db_url: str = "sqlite:///jobsies.sqlite"
    redis_url: str = "redis://localhost:6379/0"


@cache
def get_settings() -> Settings:
    """Retruns cached application settings."""
    return Settings()
