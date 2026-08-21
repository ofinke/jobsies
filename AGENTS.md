Jobsies is a self-hosted tool designed to automatically run simple jobs on the internet or locally. Like scraping product prices or others.

# Coding style
- Use good practices for python version defined in `.python-version` file
- All functions have to include docstring without args, returns, and raises if not specified differently by the user
- Write helper functions only when they are reusable
- Solve linting issues exclusively with `uv run ruff`

# Architecture considerations

## Worker

Celery worker is responsible for executing all jobsies. Jobsie is derived from `BaseJobsie` class and output of the `execute` method is a json seriazible object based on a `BaseJobsieOutput` model.

## Frontend

Frontend combines fastapi application with jinja templates and HTMX.


