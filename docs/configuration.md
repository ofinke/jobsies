In `Jobsies`, configurations are implemented as entities stored in the database. Configurations store credentials and other parameters that don't need to be updated very often, like credentials for services.

In current version, configurations are stored in database without any encryption.

# Architecture

Configurations are defined as pydantic models derived from the `BaseConfig` class and multiple configurations from the same model can be stored in the `TableSharedConfigurations` table under unique name and ID. Name is then used in the application to retrieve the configuration using the `get_config_by_name` function, which returns configuration as instance of its pydantic model. Application loads and caches all configurations on startup and it only reloads them when configuration is updated through the application interface. However, some updates require application restart to take full efect (configurations changing application worker behavior for example)

Reserved name for application configuration is `app-config`.

# In jobsies

Jobsies can have configurations and the schema of the configuration is retrievable using the `config_schema` classmethod. On startup, application checks if any configuration of that schema exist in the database, if not, jobsie is considered unavailable. However, it is up to the user to specify which named configuration to use and also specify when and how it is loaded during jobsie execution.