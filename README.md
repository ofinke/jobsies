🛠️ `Jobsies` is a self-hosted application designed to run scheduled tasks (called jobsies) on your server. These tasks can be anything you are willing to develop yourself, scrape price of a product you are interested in, or create reports on data from various sources. Here, you can find documentation of the project which focuses on high-level description of the functionality, explaining core concepts, and helping you to get started.

**Features:**
  - Simple HTMX based fronted to monitor results and plan your jobsies execution via cron based scheduler
  - Plugin system for jobsies. Develop and install only jobsies you want to have
    - You want to implement your own jobsie? look at the [jobsies-template](https://github.com/ofinke/jobsies-template) repository for guide how to do that

# Quickstart

The application is designed to run in docker with several components: application, worker, and redis. This definition is declared in the `docker-compose.yml` file. To start the application, please first pull the repository

```bash
git clone
```

open `docker-compose.yml` and replace the `TZ_INFO` with your local timezone and map location of the `data` folder (change value of volumes) for database persistant storage. Then run

```bash
make up
# or 
docker compose up --build -d
```

Application will start and will be available by defaulf on port 8777: [http://127.0.0.1:8777](http://127.0.0.1:8777). Stop the whole stack by running

```bash
make down
# or
docker compose down
```
## Run the project locally

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


# How to

TBD (general introduction, how to create new jobsie).

# Roadmap

Goal is to develop dockerized system consisting of celery worker for processing and a simple fastapi frontend to show generated information. Data are stored in an sqlite database. For larger detail, look into [docs/roadmap.md](docs/roadmap.md)

# AI Contribution

This project was co-developed with [opencode](https://opencode.ai/) using various models, mostly GPT-6-Luna, GPT-5.6-Luna, DeepSeek v4 Flash, and Gemini-3.7-Flash.