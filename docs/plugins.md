Jobsies are included through plugins. Following page describes how you can create your own jubsies and include them in the application.

# Available plugins



# Build a jobsie

Simplest approach to build a jobsie is to fork the [jobsie-template](https://github.com/ofinke/jobsies-template) repository and start there. This repository is shipped with agent skill to simplify implementing jobsies even more. For jobsie to work, it needs to be derived from the `BaseJobsie` class and its input / output and config models from corresponding classes.


# Include it in your instance

To include jobsie in your running instance, you will have to modify docker compose file. Specifically, modify following ...

