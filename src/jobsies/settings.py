from functools import cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """test."""


@cache
def get_settings() -> Settings:
    """Retruns cached application settings."""
    return Settings()
