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

To run the application, redis running on a default localhost is required. There is a predefined redis in the docker-compose.yaml, simply run

```bash
docker compose up -d
```

Then the Jobsie worker can be run by running


```bash
uv run celery -A src.jobsies.celery_app worker --loglevel=info --beat
```
## Containerized 

TBD

# Roadmap

Goal is to develop dockerized system consisting of celery worker for processing jobsies and simple fastapi frontend to show scraped information. Information is stored in an sqlite database. The development roughly follows this path

- [X] v0.1.0 - Celery worker with sqlite storage
- [ ] v0.1.1 - Simple containerization for deployment
- [ ] v0.2.0 - Fastapi serving frontend with showing results from executed jobsies
- [ ] v0.3.0 - Reusable services and generic configuration template for credentials and other