class DuplicateJobsieError(Exception):
    """Raised when jobsie class with duplicate name is registered."""


class UnavailableJobsieError(Exception):
    """Raised when execution of unavailable jobsie is triggered."""
