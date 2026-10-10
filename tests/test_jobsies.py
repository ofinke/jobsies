from types import SimpleNamespace

import pytest
from jobsies.jobs import BaseJobsie, JobsieRegistry
from jobsies.schemas.config import BaseConfig
from jobsies.schemas.jobs import BaseJobsieInput, BaseJobsieOutput


def test_jobsie_registry_loads_valid_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
    """Register valid jobsie plugins and allow jobsies without a config schema."""

    class PluginInput(BaseJobsieInput):
        """Input schema for the test plugin."""

    class PluginOutput(BaseJobsieOutput):
        """Output schema for the test plugin."""

    class PluginJobsie(BaseJobsie):
        """Valid plugin jobsie."""

        @classmethod
        def input_schema(cls) -> type[PluginInput]:
            """Return the plugin input schema."""
            return PluginInput

        @classmethod
        def output_schema(cls) -> type[PluginOutput]:
            """Return the plugin output schema."""
            return PluginOutput

        @classmethod
        def config_schema(cls) -> None:
            """Declare that the plugin does not need configuration."""

        def execute(self) -> PluginOutput:
            """Return an empty output."""
            return PluginOutput()

    entry_point = SimpleNamespace(name="valid-plugin", load=lambda: PluginJobsie)
    monkeypatch.setattr("jobsies.jobs.registry.entry_points", lambda **_: [entry_point])

    registry = JobsieRegistry()

    assert registry.get("PluginJobsie") is PluginJobsie
    assert registry.failed_load == {}


def test_jobsie_registry_tracks_invalid_plugins(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep invalid entry-point values and schema definitions in failed_load."""

    class InvalidInputJobsie(BaseJobsie):
        """Jobsie with an invalid input schema."""

        @classmethod
        def input_schema(cls) -> type[BaseJobsieOutput]:
            """Return the wrong schema base class."""
            return BaseJobsieOutput

        @classmethod
        def output_schema(cls) -> type[BaseJobsieOutput]:
            """Return a valid output schema."""
            return BaseJobsieOutput

        @classmethod
        def config_schema(cls) -> None:
            """Declare that the jobsie does not need configuration."""

        def execute(self) -> BaseJobsieOutput:
            """Return an empty output."""
            return BaseJobsieOutput()

    class InvalidOutputJobsie(InvalidInputJobsie):
        """Jobsie with an invalid output schema."""

        @classmethod
        def input_schema(cls) -> type[BaseJobsieInput]:
            """Return a valid input schema."""
            return BaseJobsieInput

        @classmethod
        def output_schema(cls) -> type[BaseJobsieInput]:
            """Return the wrong schema base class."""
            return BaseJobsieInput

    class InvalidConfigJobsie(InvalidInputJobsie):
        """Jobsie with an invalid config schema."""

        @classmethod
        def input_schema(cls) -> type[BaseJobsieInput]:
            """Return a valid input schema."""
            return BaseJobsieInput

        @classmethod
        def config_schema(cls) -> type[BaseConfig]:
            """Return a schema that is not a configuration model."""
            return BaseJobsieInput

    invalid_value = object()
    plugins = {
        "invalid-value": invalid_value,
        "invalid-input": InvalidInputJobsie,
        "invalid-output": InvalidOutputJobsie,
        "invalid-config": InvalidConfigJobsie,
    }
    entry_points = [SimpleNamespace(name=name, load=lambda value=value: value) for name, value in plugins.items()]
    monkeypatch.setattr("jobsies.jobs.registry.entry_points", lambda **_: entry_points)

    registry = JobsieRegistry()

    assert registry.failed_load == plugins
