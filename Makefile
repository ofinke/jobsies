.PHONY: init fix test run-worker run-app help

.DEFAULT_GOAL := help

init:  ## Initialize project (sync dependencies)
	uv sync

fix:  ## Run ruff fix on the codebase
	uv run ruff check --fix

test:  ## Run pytest
	uv run pytest

run-worker:  ## Start Celery worker with beat scheduler
	uv run celery -A src.jobsies.celery_app worker --loglevel=info --beat

run-app:  ## Start FastAPI dev server via uvicorn
	uv run uvicorn jobsies.fastapi_app:app --reload

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'
