🛠️ `Jobsies` is a self-hosted application designed to run scheduled tasks (called jobsies) on your server. These tasks can be anything you are willing to program yourself, scrape price of a product you are interested in, or create reports on data from various sources. Here, you can find documentation of the project which focuses on high-level description of the functionality, explaining core concepts, and helping you to get started.

# Glossary
- `Jobsie` refers to the whole project
- Jobsie refers to the task which is executed
- Definition refers to definition of jobsie, when it is suppose to be executed, with what input parameters, etc...

# Features
- Cron scheduler and execution layer for your jobsies
- Local sqlite database for storing definitions, configurations, and jobsies outputs
- Plugin system so you can create and install only jobsies you will be using
- Reusable services to help you with jobsies executions
- API interface to control system programatically 
- Simple HTMX powered frontend

# How to

## Installing Jobsies

Jobsies includes the built-in `ExampleJobsie`. Other jobsies are installed as Python plugin packages. For the Docker Compose setup, add each package's install spec to the `PLUGINS` variable in `.env.container` (you can use `.env.example` as a template). For example:

```dotenv
PLUGINS="my-jobsie-plugin another-jobsie-plugin"
```

The value is a whitespace-separated list of package specs, such as package names available from a package index or Git URLs accepted by `uv pip install`. See Plugins for plugin package requirements.

After changing `PLUGINS`, run `docker compose up -d` to recreate the containers. The startup script installs the listed packages in the app, worker, and setup containers, and the app and worker load the jobsies when they start.

## Defining jobsies

In the `Definitions` page, select "Create" and fill out the form:

- Named your jobsie, this can be anything as it is for your orientation.
- Select type of the jobsie from installed plugins.
- Define schedule when this jobsie is suppose to run by [Cron Expression](https://en.wikipedia.org/wiki/Cron).
- Select retention, for how long the results from runs should be stored in application database. Defaults to 0, meaning, that the results are stored indefinetely (currently placeholder).
- Define input variables as a JSON. Input variables depends on the selected Jobsie type and can vary wildly.
