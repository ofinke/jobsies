🛠️ `Jobsies` is a self-hosted application designed to run scheduled tasks (called jobsies) on your home server. These tasks can be anything you are willing to program yourself, scrape price of a product you are interested in, or create reports on data from various sources. Here, you can find documentation of the project which focuses on high-level description of the program, explaining core concepts, and helping you to get started.

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

Jobsie is a single job which has a simple output and you want to run it repeatedly, the current implementations contains these jobsies:

- `ExampleJobsie` for showing functionality, it only returns "Hello World!" string.
- `ZalandoJobsie` for scraping product prices from the website zalando.cz. Input for this task is URL to scrape and the size of the product exactly as it is listed on the page.
- `FlightPriceJobsie` for scraping flight prices from google flights. It supports only looking up flights in specific dates between specific airports.

## Defining jobsies

In the `Definitions` page, select "Create" and fill out the form:

- Named your jobsie, this can be anything as it is for your orientation.
- Select type of the jobsie (see implemented jobsies above).
- Select schedule when this jobsie is suppose to run by [Cron Expression](https://en.wikipedia.org/wiki/Cron).
- Select retention, for how long the results from runs should be stored in application database. Defaults to 0, meaning, that the results are stored indefinetely.
- Define input variables as a JSON. Input variables depends on the selected Jobsie type and can vary wildly.

## Monitoring jobsies

The `Results` page shows latest results for each defined jobsie.

## Building jobsies

Like the whole applications, Jobsies are written in Python and all are derived from a `BaseJobsie` class.
