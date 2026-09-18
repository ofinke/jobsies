🛠️ Jobsies is a self-hosted tool designed to automatically run simple jobs on the internet; scrape price of a product you are interested in, monitor websites for new events, or anything you are willing to program yourself.

Features:

# Quickstart

To run the project locally, docker installation is assumed. The project can be run fully locally without it, but you need to supply redis instance and include it in `.env` file. Project is mainly controlled via the included `Makefile`, run

```bash
make
```

to see the available commands or, if you don't have make tools installed, just read the file.

## Local development

Clone the repository, install dependencies

```bash
make init
```

To run the application, first populate database with example jobsie

```bash
make populate   # populates database with example jobsie, good before first run
```

Then, you can run run the app components separately (in different shells) by these commands

```bash
make redis-up
make run-worker
make run-app
```

These commands creates redis instance using docker and starts both the worker and app. Application is then available at [localhost:8000](http://127.0.0.1:8000). Swagger documentation is available at [/docs](http://127.0.0.1:8000/docs). 

## Containerized 

Build and start the whole stack in docker (redis + worker + app) using

```bash
make up
```

The worker container mounts the local `./data` folder, so the database persists on the host. By default, the docker exposes app at the port 8777 - [http://127.0.0.1:8777](http://127.0.0.1:8777).

Stop the whole stack by running

```bash
make down
```
# How to

TBD (general introduction, how to create new jobsie).

# Roadmap

Goal is to develop dockerized system consisting of celery worker for processing and a simple fastapi frontend to show generated information. Data are stored in an sqlite database. For larger detail, look into [docs/roadmap.md](docs/roadmap.md)

# AI Contribution

This project was co-developed with [opencode](https://opencode.ai/) using various models, mostly GPT-5.6-Luna, DeepSeek v4 Flash, and Gemini-3.7-Flash. Contribution via PRs are welcomed, however fully AI generated and automated PRs will be rejected.