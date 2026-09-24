# Overview

In Jobsies, configurations are implemented as entities stored in the database. Configurations store credentials and other parameters that don't need to be updated very often.

## Architecture

- Configs are defined as pydantic models derived from `BaseConfig` class
- Each configuration is stored as a row in the `TableSharedConfigurations` table under a unique name and ID
    - Configuration values are stored as JSON in the `config` column.
- In the application, all configurations are accessible through a singleton instance of `ConfigRegistry` and retrieved by the `get_config_by_name` function
    - Configurations are loaded and cached at the start of the application
    - The cache is cleared whenever a configuration is updated through the application interface
    - Some configuration changes require an application restart
    - Retrieved configurations are validated by their models and returned as instances of those models
    - The main application configuration is stored under the name `app-config`
