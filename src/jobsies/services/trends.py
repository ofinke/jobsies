from datetime import UTC, datetime
from math import isfinite

import pytz
from sqlmodel import select

from jobsies.database import DatabaseHandler, get_db_handler
from jobsies.schemas.monitor import OutputMonitoringDefinition
from jobsies.schemas.tables import TableJobsiesDefinition, TableJobsiesOutputs
from jobsies.settings import get_settings


class TrendsService:
    """Provides data for monitoring trends from jobsies outputs."""

    def __init__(self, db_handler: DatabaseHandler | None = None) -> None:
        """Initialize the trends service."""
        self.db = db_handler or get_db_handler()

    @staticmethod
    def _get_output_value(output_data: dict, pointer: str) -> object | None:
        """Resolve a JSON Pointer against one output, returning None when it does not resolve."""
        value: object = output_data
        for encoded_token in pointer[1:].split("/"):
            token = encoded_token.replace("~1", "/").replace("~0", "~")
            if isinstance(value, dict):
                value = value.get(token)
            elif isinstance(value, list) and token.isascii() and token.isdigit():
                if str(int(token)) != token:
                    return None
                index = int(token)
                value = value[index] if index < len(value) else None
            else:
                return None

            if value is None:
                return None

        return value

    @staticmethod
    def _format_timestamp(timestamp: datetime | None) -> str | None:
        """Format an output timestamp as an ISO 8601 string with a timezone offset."""
        if timestamp is None:
            return None
        if timestamp.tzinfo is None:
            timestamp = pytz.timezone(get_settings().tz_info).localize(timestamp)
        return timestamp.astimezone(UTC).isoformat()

    @staticmethod
    def _numeric_value(value: object | None) -> int | float | None:
        """Return finite numeric values for line charts, excluding booleans and other types."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        if isinstance(value, float) and not isfinite(value):
            return None
        return value

    def get_output_trend(self, jobsie_id: int) -> dict[str, object] | None:
        """Build chart data for a Jobsie definition from its configured output monitors."""
        definitions = self.db.load(
            TableJobsiesDefinition,
            statement=select(TableJobsiesDefinition).where(TableJobsiesDefinition.id == jobsie_id),
        )
        if not definitions:
            return None

        raw_monitoring = definitions[0].output_monitoring
        monitoring = OutputMonitoringDefinition.model_validate(raw_monitoring or {"version": 1, "monitors": []})
        result: dict[str, object] = {"version": monitoring.version, "monitors": []}
        if not monitoring.monitors:
            return result

        max_count = max(monitor.window.count for monitor in monitoring.monitors)
        outputs = self.db.load(
            TableJobsiesOutputs,
            statement=(
                select(TableJobsiesOutputs)
                .where(
                    TableJobsiesOutputs.jobsie_id == jobsie_id,
                    TableJobsiesOutputs.success.is_(True),
                )
                .order_by(TableJobsiesOutputs.created_at.desc(), TableJobsiesOutputs.id.desc())
                .limit(max_count)
            ),
        )

        for monitor in monitoring.monitors:
            monitor_data = monitor.model_dump(mode="json")
            selected_outputs = list(reversed(outputs[: monitor.window.count]))
            monitor_data["data"] = {
                "timestamp": [self._format_timestamp(output.created_at) for output in selected_outputs],
                "value": [
                    self._numeric_value(self._get_output_value(output.output_data, monitor.field))
                    for output in selected_outputs
                ],
            }
            result["monitors"].append(monitor_data)

        return result
