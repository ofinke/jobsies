# unified table for jobsies output
# ideas for columns - name, json output, retention (days, 0 infinite)

from .base import TableDefaultModel


class TableJobsiesOutputs(TableDefaultModel):
    """Data structure for storing results from Jobsies executions."""

    __tablename__ = "data_outputs"
