In `Jobsies`, configurations are implemented as entities stored in the database. Configurations store credentials and other parameters that don't need to be updated very often, like credentials for services.

In current version, configurations are stored in database without any encryption.

# Architecture

Configurations are defined as pydantic models derived from the `BaseConfig` class and multiple configurations from the same model can be stored in the `TableSharedConfigurations` table under unique name and ID. Name is then used in the application to retrieve the configuration using the `get_config_by_name` function, which returns configuration as instance of its pydantic model. Some updates require application restart to take full efect (configurations changing application worker behavior for example)

Reserved name for application configuration is `app-config`.

Originally the configurations were cached in memory and this cache was reloaded only on changes. However we would have needed to track the changes through redis (so worker and app stays synchronized), so this feature was removed as we don't access the database that often anyway and it is just simpler.

# In jobsies

Jobsies can have configurations by setting the `config_model` class attribute to a `BaseConfig` subclass. If omitted, the Jobsie has no configuration model. On startup, the application checks whether any configuration of that model exists in the database; if not, the Jobsie is considered unavailable. However, it is up to the user to specify which named configuration to use and also specify when and how it is loaded during Jobsie execution.
