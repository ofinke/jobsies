from pydantic import Field

from .base import BaseConfig


class AppConfig(BaseConfig):
    """Application configuration."""

    # Configuration related to celery worker
    scheduler_lookahead: int = Field(
        default=900,
        description="How often the worker schedules tasks ahead",
    )
    scheduler_interval: int = Field(
        default=450,
        description="How often the scheduler runs, should be less then lookahead",
    )
    task_soft_time_limit: int = Field(
        default=300,
        description="Soft limit for task execution",
    )
    task_time_limit: int = Field(
        default=360,
        description="Hard stop limit for task execution",
    )
    worker_concurrency: int = Field(
        default=2,
        description="Number of parallel workers",
    )
