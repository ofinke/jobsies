🛠️ `Jobsies` is a self-hosted tool designed to automatically run simple jobs on the internet. This about page focuses on description on what jobsies are, how to set them up, and how to implement new ones.

# Jobsies

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