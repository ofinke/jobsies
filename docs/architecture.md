Bellow you can find important architecture diagrams and high level ideas on how `jobsies` are implemented. 

## Manifest

Jobsie is


## Overall


## Executing jobsies

Jobsies are always executed by the `RunnerService` as a sole interface for the execution. The execution follow this scheme:

```mermaid
sequenceDiagram
    autonumber
    participant Trigger@{ "type": "boundary" }
    participant Runner as RunnerService
    participant JobsieRegistry@{ "type" : "collections" }
    participant Jobsie
    participant Database@{ "type": "database" }
    Trigger ->> Runner: Request jobsie run using ID
    Runner <<-->> Database: Retrieves jobsie definition
    Runner <<-->> JobsieRegistry: Retrieves jobsie class
    Runner ->> Jobsie: Creates jobsie instance and execute it
    activate Jobsie
    Jobsie ->> Runner: Returns result
    deactivate Jobsie
    Runner -->> Database: Stores execution result
```
> Sequence diagram of how jobsie execution happens

where trigger can be: scheduled execution, API call, or user pressing the run button.


## Database

```mermaid
erDiagram
    direction LR

    jobsies_definitions ||--o{ jobsies_outputs : "jobsie_id (logical reference; not enforced)"

    jobsies_definitions {
        int id PK
        datetime created_at "nullable"
        datetime updated_at "nullable"
        text name
        text subclass_name
        text cron
        text retention
        json input_kwargs
        json output_vars
        json output_monitoring
        text status
    }

    jobsies_outputs {
        int id PK
        datetime created_at "nullable"
        datetime updated_at "nullable"
        text jobsie_name
        int jobsie_id
        text execution_id
        datetime retention "nullable"
        boolean success
        json output_data
        json execution_metadata
    }
```

```mermaid
erDiagram
    shared_configurations {
        int id PK
        datetime created_at "nullable"
        datetime updated_at "nullable"
        text name UK
        text description "nullable"
        text config_model
        text config "encrypted JSON when configured"
    }
```


## Plugin system
