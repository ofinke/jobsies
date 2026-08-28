.PHONY: init fix test populate redis run run-worker run-app stop help
.ONESHELL:

REDIS_CONTAINER := jobsies-redis-dev

.DEFAULT_GOAL := help

init:  ## Initialize project (sync dependencies)
	uv sync

fix:  ## Run ruff fix on the codebase
	uv run ruff check --fix

test:  ## Run pytest
	uv run pytest

populate: ## Populate database with default values
	docker compose up -d redis

redis: ## Run redis in docker
	set -e
	docker rm -f $(REDIS_CONTAINER) >/dev/null 2>&1 || true
	docker run -d --name $(REDIS_CONTAINER) --memory=128m -p 6379:6379 redis:alpine >/dev/null

run-worker:  ## Start Celery worker with beat scheduler
	uv run celery -A src.jobsies.celery_app worker --loglevel=info --beat

run-app:  ## Start FastAPI dev server via uvicorn
	uv run uvicorn jobsies.fastapi_app:app --reload

run: ## Start Redis, the Celery worker, and the FastAPI app locally
	set -e
	docker rm -f $(REDIS_CONTAINER) >/dev/null 2>&1 || true
	docker run -d --name $(REDIS_CONTAINER) --memory=128m -p 6379:6379 redis:alpine >/dev/null
	trap 'kill $$worker 2>/dev/null || true; docker stop $(REDIS_CONTAINER) >/dev/null 2>&1 || true' EXIT INT TERM
	until docker exec $(REDIS_CONTAINER) redis-cli ping >/dev/null 2>&1; do sleep 1; done
	uv run celery -A src.jobsies.celery_app worker --loglevel=info --beat &
	worker=$$!
	uv run uvicorn jobsies.fastapi_app:app --reload

stop: ## Stop the locally managed Redis container
	docker stop $(REDIS_CONTAINER) 2>/dev/null || true

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'
