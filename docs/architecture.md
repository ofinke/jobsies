---

---

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

Tables schemas:


## Plugin system