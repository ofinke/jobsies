from unittest.mock import MagicMock, patch

import pytest
from jobsies.celery_app import config, schedule_upcoming_jobsies, wrapper_run_dynamic_jobsie


@patch("jobsies.celery_app.RunnerService")
def test_wrapper_run_dynamic_jobsie_delegates_to_runner(
    mock_runner_service: MagicMock,
) -> None:
    """Tests that the Celery task delegates execution to RunnerService."""
    runner = mock_runner_service.return_value

    wrapper_run_dynamic_jobsie.run(42)

    runner.run_dynamic_jobsie.assert_called_once()
    args, kwargs = runner.run_dynamic_jobsie.call_args

    assert args == (42,)
    assert kwargs["execution_metadata"]["execution_method"] == "celery"
    assert "execution_id" in kwargs["execution_metadata"]


@patch("jobsies.celery_app.wrapper_run_dynamic_jobsie")
@patch("jobsies.celery_app.SchedulingService")
def test_schedule_upcoming_jobsies_delegates_to_scheduler(
    mock_scheduler_service: MagicMock,
    mock_task: MagicMock,
) -> None:
    """Tests that upcoming jobsies are passed to SchedulingService."""
    scheduler = mock_scheduler_service.return_value
    scheduler.process_and_schedule.return_value = {
        "enqueued": 2,
        "skipped": 1,
    }

    schedule_upcoming_jobsies()

    mock_scheduler_service.assert_called_once_with(lookahead_seconds=config.scheduler_lookahead)
    scheduler.process_and_schedule.assert_called_once_with(mock_task)


@patch("jobsies.celery_app.RunnerService")
def test_wrapper_run_dynamic_jobsie_propagates_runner_error(
    mock_runner_service: MagicMock,
) -> None:
    """Tests that RunnerService errors are not swallowed by the task."""
    mock_runner_service.return_value.run_dynamic_jobsie.side_effect = RuntimeError("failed")

    with pytest.raises(RuntimeError, match="failed"):
        wrapper_run_dynamic_jobsie.run(42)
