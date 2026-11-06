🛠️ `Jobsies` is a self-hosted application designed to run scheduled tasks (called jobsies) on your home server. These tasks can be anything you are willing to develop yourself, scrape price of a product you are interested in, or create reports on data from various sources.

**Features:**
- Simple HTMX based fronted to monitor results and plan your jobsies execution via cron based scheduler
- Plugin system for jobsies. Develop and install only jobsies you want to have
  - You want to implement your own jobsie? look at the [jobsies-template](https://github.com/ofinke/jobsies-template) repository for guide how to do that

# Quickstart

The application is designed to run in docker with several components: application, worker, and redis. This definition is declared in the `docker-compose.yml` file. To start the application, please first pull the repository, open it and prepare environmental variables

```bash
git clone https://github.com/ofinke/jobsies.git
```

```bash
cd jobsies
cp .env.example .env.container
```
And fill out the missing environmental variables in newly created `.env.container` file. Then start the application using

```bash
docker compose up --build -d
```
Application will start and will be available by defaulf on port 8777: [http://127.0.0.1:8777](http://127.0.0.1:8777). Stop the whole stack by running

```bash
docker compose down
```

# How to

TBD

# Roadmap

Goal is to develop dockerized system consisting of celery worker for processing and a simple fastapi frontend to show generated information. Data are stored in an sqlite database. For larger detail, look into [docs/roadmap.md](docs/roadmap.md)

# AI Contribution

This project was co-developed with [opencode](https://opencode.ai/) using various models, mostly GPT-6-Luna, GPT-5.6-Luna, DeepSeek v4 Flash, and Gemini-3.7-Flash.