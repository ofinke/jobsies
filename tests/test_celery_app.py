from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from jobsies.celery_app import (
    app,
    # celery_app_status,
    config,
    schedule_upcoming_jobsies,
    settings,
    wrapper_run_dynamic_jobsie,
)


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


# @patch("jobsies.celery_app.app")
# def test_celery_status_returns_worker_metrics(mock_app: MagicMock) -> None:
#     """Test Celery status normalizes worker metrics without task payloads."""
#     inspector = mock_app.control.inspect.return_value
#     inspector.stats.return_value = {
#         "celery@worker": {"pid": 42, "uptime": 600, "pool": {"max-concurrency": 2}},
#     }

#     status = celery_app_status()

#     assert status == {
#         "alive": True,
#         "worker_count": 1,
#         "workers": [
#             {
#                 "hostname": "celery@worker",
#                 "alive": True,
#                 "concurrency": 2,
#                 "active_tasks": "Unavailable",
#                 "reserved_tasks": "Unavailable",
#                 "scheduled_tasks": "Unavailable",
#                 "uptime": 600,
#                 "pid": 42,
#             },
#         ],
#     }
#     mock_app.control.inspect.assert_called_once_with(timeout=0.1)
#     inspector.stats.assert_called_once_with()


# @patch("jobsies.celery_app.app")
# def test_celery_status_reports_unavailable_when_inspection_fails(mock_app: MagicMock) -> None:
#     """Test failed Celery inspection produces a safe unavailable status."""
#     mock_app.control.inspect.side_effect = RuntimeError("worker unavailable")

#     status = celery_app_status()

#     assert status == {"alive": False, "worker_count": 0, "workers": []}


@patch("jobsies.celery_app.SchedulingService")
def test_schedule_upcoming_jobsies_delegates_to_scheduler(
    mock_scheduler_service: MagicMock,
) -> None:
    """Tests that upcoming jobsies are passed to SchedulingService."""
    scheduler = mock_scheduler_service.return_value
    scheduler.define_next_jobsies.return_value = {}

    schedule_upcoming_jobsies()

    mock_scheduler_service.assert_called_once_with()
    scheduler.define_next_jobsies.assert_called_once_with(config.scheduler_lookahead)


@patch("jobsies.celery_app.wrapper_run_dynamic_jobsie")
@patch("jobsies.celery_app.get_redis_handler")
@patch("jobsies.celery_app.SchedulingService")
def test_schedule_upcoming_jobsies_enqueues_defined_runs(
    mock_scheduler_service: MagicMock,
    mock_get_redis_handler: MagicMock,
    mock_task: MagicMock,
) -> None:
    """Tests that defined runs are locked and passed to Celery with their ETA."""
    run_time = datetime(2026, 9, 14, 13, 0, tzinfo=UTC)
    scheduler = mock_scheduler_service.return_value
    scheduler.define_next_jobsies.return_value = {42: [run_time]}
    redis_handler = mock_get_redis_handler.return_value
    redis_handler.acquire_enqueue_lock.return_value = True

    schedule_upcoming_jobsies()

    mock_get_redis_handler.assert_called_once_with(settings.broker_redis_url)
    redis_handler.acquire_enqueue_lock.assert_called_once_with(
        "lock:task_run:42:29823180",
        int(config.scheduler_lookahead * 1.2),
    )
    mock_task.apply_async.assert_called_once_with(args=[42], eta=run_time)


@patch("jobsies.celery_app.RunnerService")
def test_wrapper_run_dynamic_jobsie_propagates_runner_error(
    mock_runner_service: MagicMock,
) -> None:
    """Tests that RunnerService errors are not swallowed by the task."""
    mock_runner_service.return_value.run_dynamic_jobsie.side_effect = RuntimeError("failed")

    with pytest.raises(RuntimeError, match="failed"):
        wrapper_run_dynamic_jobsie.run(42)
