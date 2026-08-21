from importlib.metadata import version

from fastapi import FastAPI

from jobsies.api.v1 import jobsies_definition_router, jobsies_execution_router

app = FastAPI(
    title="Jobsies",
    version=version("jobsies"),
    docs_url="/docs",
)

app.include_router(jobsies_definition_router)
app.include_router(jobsies_execution_router)
