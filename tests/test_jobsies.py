from types import SimpleNamespace

import pytest
from jobsies.jobs import BaseJobsie, ExampleJobsie, JobsieRegistry
from jobsies.schemas.jobs import BaseJobsieInput, BaseJobsieOutput


def test_example_jobsie_returns_random_number() -> None:
    """Return the example content and a number within the configured range."""
    output = ExampleJobsie().execute()

    assert output.content == "Hello World!"
    assert 0 <= output.number <= 9


def test_jobsie_registry_loads_valid_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
    """Register valid jobsie plugins and allow jobsies without a config schema."""

    class PluginInput(BaseJobsieInput):
        """Input schema for the test plugin."""

    class PluginOutput(BaseJobsieOutput):
        """Output schema for the test plugin."""

    class PluginJobsie(BaseJobsie):
        """Valid plugin jobsie."""

        input_model = PluginInput
        output_model = PluginOutput

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

        input_model = BaseJobsieOutput
        output_model = BaseJobsieOutput

        def execute(self) -> BaseJobsieOutput:
            """Return an empty output."""
            return BaseJobsieOutput()

    class InvalidOutputJobsie(InvalidInputJobsie):
        """Jobsie with an invalid output schema."""

        input_model = BaseJobsieInput
        output_model = BaseJobsieInput

    class InvalidConfigJobsie(InvalidInputJobsie):
        """Jobsie with an invalid config schema."""

        input_model = BaseJobsieInput
        config_model = BaseJobsieInput

    class MissingInputJobsie(BaseJobsie):
        """Jobsie without a required input model."""

        output_model = BaseJobsieOutput

        def execute(self) -> BaseJobsieOutput:
            """Return an empty output."""
            return BaseJobsieOutput()

    invalid_value = object()
    plugins = {
        "invalid-value": invalid_value,
        "invalid-input": InvalidInputJobsie,
        "invalid-output": InvalidOutputJobsie,
        "invalid-config": InvalidConfigJobsie,
        "missing-input": MissingInputJobsie,
    }
    entry_points = [SimpleNamespace(name=name, load=lambda value=value: value) for name, value in plugins.items()]
    monkeypatch.setattr("jobsies.jobs.registry.entry_points", lambda **_: entry_points)

    registry = JobsieRegistry()

    assert registry.failed_load == plugins
