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

Build and start the whole stack (redis + worker + app)

```bash
docker compose up -d --build
```

The worker container mounts the local `./data` folder, so the database persists on the host. By default, the APP is available at [http://127.0.0.1:8777](http://127.0.0.1:8000).

Stop the whole stack bu running

```bash
docker stop jobsies-redis jobsies-app jobsies-worker
```

# Roadmap

Goal is to develop dockerized system consisting of celery worker for processing and a simple fastapi frontend to show created information. Data are stored in an sqlite database. The development roughly follows this path

- [X] v0.1.0 - Celery worker with sqlite storage
- [X] v0.1.1 - Simple containerization for deployment
- [X] v0.2.0 - Fastapi serving frontend with showing results from executed jobsies
  - [X] v0.2.1 - Add entrypoint.sh into docker image to determine if image should be started as app or worker
  - [ ] v0.2.2 - Add TZ env variable and ensure that timestamps are correctly handled everywhere
  - [ ] v0.2.3 - Testing for celery worker (including plan and instructions for unification)
  - [ ] v0.2.4 - Testing suite for the fastapi (including plan and instructions for unification)
  - [ ] v0.2.5 - Update Jobsies definition UI with better input_kwargs validation
  - [ ] v0.2.6 - Page for monitoring celery worker and jobsies scheduling
  - [ ] v0.2.7 - Cleaner and unified UI styling
- [ ] v0.3.0 - Reusable services and generic configuration template for credentials and others
