# Roadmap

 The development roughly follows this path

- [X] v0.1.0 - Celery worker with sqlite storage
- [X] v0.1.1 - Simple containerization for deployment
- [X] v0.2.0 - Fastapi serving frontend with showing results from executed jobsies
  - [X] v0.2.1 - Add entrypoint.sh into docker image to determine if image should be started as app or worker
  - [X] v0.2.2 - Add TZ env variable and ensure that timestamps are correctly handled everywhere
  - [X] v0.2.3 - Testing for celery worker 
  - [X] v0.2.4 - Testing suite for the fastapi and Jobsie for scraping airpline ticket prices from google flights
  - [ ] v0.2.5 - Update Jobsies definition UI with better input_kwargs validation
  - [ ] v0.2.6 - Page for monitoring celery worker and jobsies scheduling (look at /sibson/redbeat as a celery scheduler)
- [ ] v0.3.0 - Reusable services, generic configuration template for credentials, jobsies as a plugin system, and monitoring results as charts
  - [ ] v O.3.1 - cleanup of the project and figuring out what next

# Features

Here is a list of features which I would like to include. Some will be later included in the roadmap and some will be done randomly when I feel like it. Some will be skipped when I inevitably get bored with this project.

## jobsies
-

## Small

- Move app config into database and include initialization of it when app is first started (included in 0.3.0). Include this in the entrypoint.sh script which will initialize the database first time the app is started (not worker)
- Add tasks for cleaning up database and implement the retention mechanism
- Make Redis handling better (password protection, don´t use everything with default ports and others).
- Include copy and export as json buttons to the definition page
- Figure out how to operate with jobsies and their runs after they are deleted (do I keep the run, what about the database id, does it get reused, do I show the results)
  - ID doesn't get reused from the database, don't know when I'm migrating the database for example.

## Large

- Advanced UI for showing results from jobsies, allowing show output variables as charts, or something else.
- Alerting system using whatsapp / email or maybe something else.
