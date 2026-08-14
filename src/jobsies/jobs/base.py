from abc import ABC, abstractmethod


class BaseJobsie(ABC):
    def __init__(self) -> None:
        """Does something."""
        super().__init__()

    @abstractmethod
    def execute(self) -> dict:
        """Actually does something."""


def get_jobsie_class(name: str) -> type[BaseJobsie]:
    """Returns a subclass of BaseJobsie by its class name."""
    mapping = {cls.__name__: cls for cls in BaseJobsie.__subclasses__()}
    return mapping[name]
