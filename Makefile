.PHONY: install init fix test populate redis redis-run redis-stop run run-worker run-app stop help
.ONESHELL:

REDIS_CONTAINER := jobsies-redis-dev

.DEFAULT_GOAL := help

install:  ## Install all project dependency groups
	uv sync --all-groups

init:  ## Install dependencies and populate the database
	$(MAKE) install
	$(MAKE) populate

fix:  ## Run ruff fix on the codebase
	uv run ruff check --fix

test:  ## Run pytest
	uv run pytest --cov=jobsies

populate: ## Populate database with default values
	uv run python -m jobsies.database.setup

redis-run: ## Run redis in docker
	set -e
	docker rm -f $(REDIS_CONTAINER) >/dev/null 2>&1 || true
	docker run -d --name $(REDIS_CONTAINER) --memory=128m -p 6379:6379 redis:alpine >/dev/null

redis-stop: ## Stop the locally managed Redis container
	docker stop $(REDIS_CONTAINER) 2>/dev/null || true

run-worker:  ## Start Celery worker with beat scheduler
	uv run celery -A src.jobsies.celery_app worker --loglevel=info --beat --scheduler redbeat.RedBeatScheduler

run-app:  ## Start FastAPI dev server via uvicorn
	uv run uvicorn jobsies.fastapi_app:app --reload

up:		## Starts the whole application using docker
	docker compose up --build -d

down:	## Stops the stack
	docker compose down

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'
