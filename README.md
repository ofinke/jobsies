🛠️ Jobsies is a self-hosted tool designed to automatically run simple jobs on the internet; scrape price of a product you are interested in, or anything you are willing to program yourself.

# How to run

## Locally

Clone the repository and install dependencies

```bash
uv sync
```

Populate database with example jobsie config

```bash
uv run populate-db
```

To run the application, redis running on a localhost (default port) is required. There is a predefined redis in the docker-compose.yaml, simply run

```bash
docker compose up -d redis
```

Then the Jobsie worker can be run by running


```bash
uv run celery -A src.jobsies.celery_app worker --loglevel=info --beat
```

The FastAPI web server can be started by running

```bash
uv run uvicorn jobsies.fastapi_app:app --reload
```

Interactive Swagger documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Containerized 

Before running for the first time, build the database into `./data`

```bash
uv run populate-db
```

Build and start the whole stack (redis + jobsies worker)

```bash
docker compose up -d --build
```

The worker container mounts the local `./data` folder, so the sqlite database persists on the host and can be shared with a locally running instance.

# Roadmap

Goal is to develop dockerized system consisting of celery worker for processing and a simple fastapi frontend to show created information. Data are stored in an sqlite database. The development roughly follows this path

- [X] v0.1.0 - Celery worker with sqlite storage
- [X] v0.1.1 - Simple containerization for deployment
- [ ] v0.2.0 - Fastapi serving frontend with showing results from executed jobsies
  - [ ] v0.2.1 - Expansion of docker image with entrypoint.sh if container is executed as app / image
  - [ ] v0.2.2 - Jobsies input models and modal for configuration endpoints
  - [ ] v0.2.3 - Testing for celery worker (including plan and instructions for unification)
  - [ ] v0.2.4 - Testing suite for the fastapi (including plan and instructions for unification)
  - [ ] v0.2.5 - Page for monitoring celery worker and jobsies scheduling
- [ ] v0.3.0 - Reusable services and generic configuration template for credentials and others