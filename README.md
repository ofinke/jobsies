🛠️ Jobsies is a self-hosted tool designed to automatically run simple jobs on the internet; scrape price of a product you are interested in, monitor websites for new events, or anything you are willing to program yourself.

# Quickstart

## Local development

Clone the repository and install dependencies

```bash
uv sync
```

Use make tools to run the application, follow these commands:

```bash
make populate   # populates database with example jobsie, good before first run
make run        # starts the application fully
```

This command creates redis instance using docker and starts both the worker and app in a single shell. Application is then available at [localhost:8000](http://127.0.0.1:8000). Swagger documentation is then available at [/docs](http://127.0.0.1:8000/docs). 

You can run run the app components separately by these commands

```bash
make redis
make run-worker
make run-app
```

## Containerized 

Build and start the whole stack in docker (redis + worker + app) using

```bash
docker compose up -d --build
```

The worker container mounts the local `./data` folder, so the database persists on the host. By default, the docker exposes app at the port 8777 - [http://127.0.0.1:8777](http://127.0.0.1:8777).

Stop the whole stack by running

```bash
docker stop jobsies-redis jobsies-app jobsies-worker
```
# How to

TBD (general introduction, how to create new jobsie).

# Roadmap

Goal is to develop dockerized system consisting of celery worker for processing and a simple fastapi frontend to show generated information. Data are stored in an sqlite database. For larger detail, look into [docs/roadmap.md](docs/roadmap.md)