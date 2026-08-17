Jobsies is a self-hosted tool designed to run automatically simple jobs on the internet, scrape price of a product you are interested in, or anything you are willing to program yourself.

# Installation

Clone the repository and run

```bash
uv sync
```

# Running Celery worker

```bash
uv run celery -A src.jobsies.celery_app worker --loglevel=info --beat
```