Services are resusable components provided by the application. Some are build for the application functionality and some are available as a components which can be used by various jobsies.

## Reusable Services

These services are primarly designed to be used with jobsies,

| Service  | Purpose | Usage   |
| -------- | ------- | ------- |
|          |         |         |

## Application Services

These services are meant primary for the application runtime. They can be reused for jobsies, but they are not designed with that purpose in mind.

| Service  | Purpose | Usage |
| -------- | ------- | ----- |
| `DatabaseHandler`    | Interface layer with the application database | singleton instance through cached `get_db_handler` function |
| `RedisHandler`       | Interface layer for the redis client | singleton instance through cached `get_redis_handler` function for each of the used databases |
| `DefinitionService`  | Layer for handling defining jobsies schedules via API or web application |     |
| `OutputService`      | Interface for retrieving results from jobsie executions table with predefined queries |     |
| `RunnerService`      | Interface layer for executing jobsies |     |
| `SchedulingService`  | Service for retrieving timestamps of future jobsie executions |     |
