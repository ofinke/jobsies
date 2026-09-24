# Overview

In Jobsies, different configurations are implemented as a database stored entities. In configs, we store credentials, and other parameters which doesn't need to update very often. Each service, jobsie or other components requirung configuration has it defined as pydantic model. Set values are then stored in the `shared_configurations` table. Configurations are stored under unique names.

## Architecture

- Each configuration is stored as row in the `TableSharedConfigurations` table under a unique name and ID
    - values of the configuration are stored as a JSON
- In the application, all configurations are accessible through singleton instance of `ConfigRegistry`
    - Configurations are loaded and cached at the start of the application
    - Cache is cleared when any update, through application interface, is done to any configurations
    - Some configuration changes require application restart
- 



Mutable / unmutable configuration
- Idea is, that this is configuration for some app part, celery, fastapi, or something similar. Something which would require application restart to work and has some default values defined in the application. Should be user able to modify this? Or should ve define it with different flag? Is the flag even necessary?