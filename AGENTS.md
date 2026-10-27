`Jobsies` is a self-hosted application designed to run scheduled tasks (called jobsies). These tasks are added through a plugin system. This project is the worker and server application for scheduling and executing jobsies and serving a frontend for their management and monitoring of the results.

# Coding style

- Use good practices for the Python version defined in the `.python-version` file
- All functions must include a docstring without `Args`, `Returns`, or `Raises` sections unless otherwise specified by the user
- Write helper functions only when they are reusable
- Solve linting issues exclusively with `uv run ruff`
- After each update run tests using `make test` or `uv run pytest --cov=jobsies`

# Architecture considerations

The application consists of a FastAPI server, Celery worker, Redis, and SQLite database. The worker and server share the same codebase; only the method of running the application differs. The primary running method is through Docker, defined in the `docker-compose.yml` file.

- The server mainly handles the user interface and interaction via the REST API
- The worker handles scheduling and jobsies execution
- Redis serves as a broker for the Celery worker
- The SQLite database serves as storage for jobsie results, configurations, and execution definitions

## Project structure and glossary

- Jobsies - `src/jobsies/jobs` folder - repeatable tasks derived from the `BaseJobsie` class. On startup, the application registers all instances of the base class in the `JobsieRegistry`. Jobsies have defined input and output data models derived from the `BaseJobsieInput` and `BaseJobsieOutput` models.
- Settings - `src/jobsies/settings.py` - contains a unified interface for environment variables. These are used only for the server and worker runtime
- Schemas - `src/jobsies/schemas` folder - contains all Pydantic models and SQLModel definitions
- Services - `src/jobsies/services` folder - various reusable services that are either required by the application itself or can be used in jobsies
- Configurations - `src/jobsies/services/config_service.py` - special service for handling various configurations for the application or for jobsies. Configurations can contain secrets and are the preferred method for storing them for jobsies. Configurations are stored as named entities in the database and are validated by their specific Pydantic models derived from the `BaseConfig` class. `BaseConfig` is exposed to the plugin system.
- Lightweight documentation for some components can be found in `/docs` folder.

## Frontend

The frontend is served via HTML templates with HTMX endpoints. The page API endpoints are defined in `src/jobsies/api/web/pages.py`, and all HTMX components are served via endpoints defined in the `src/jobsies/api/web/components` folder in files corresponding to their page. HTML is located in the `src/jobsies/templates` folder, and CSS and JS are located in the `src/jobsies/static` folder.
