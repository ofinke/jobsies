from enum import StrEnum


class JobsieDefinitionStatus(StrEnum):
    """
    Options for jobsie definition status.

    - enabled = jobsie will be executed based on schedule
    - disabled = jobsie will not be executed
    - unavailable = jobsie cannot be executed (missing plugin, config, or other.)
    """

    ENABLED = "enabled"
    DISABLED = "disabled"
    UNAVAILABLE = "unavailable"
