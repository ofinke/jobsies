Jobsies are included through plugins. Following page describes how you can create your own jubsies and include them in the application.

# Plugin package requirements

Plugin packages must expose their jobsie classes through the `jobsies.jobs` Python entry-point group. If a plugin provides configuration models, expose them through the `jobsies.config` entry-point group.

# Build a jobsie

Simplest approach to build a jobsie is to fork the [jobsie-template](https://github.com/ofinke/jobsies-template) repository and start there. This repository is shipped with agent skill to simplify implementing jobsies even more. For jobsie to work, it needs to be derived from the `BaseJobsie` class and its input / output and config models from corresponding classes.

