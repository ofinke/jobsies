from abc import ABC, abstractmethod


class BaseJobsie(ABC):
    def __init__(self) -> None:
        """Does something."""
        super().__init__()

    @abstractmethod
    def execute(self) -> dict:
        """Actually does something."""
