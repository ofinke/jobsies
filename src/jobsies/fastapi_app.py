from importlib.metadata import version

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from jobsies.api.v1 import jobsies_definition_router, jobsies_execution_router, jobsies_output_router
from jobsies.api.web import definition_component_router, results_component_router, web_pages_router

app = FastAPI(
    title="Jobsies",
    version=version("jobsies"),
    docs_url="/docs",
)

app.mount("/static", StaticFiles(directory="src/jobsies/static"), name="static")

app.include_router(jobsies_definition_router)
app.include_router(jobsies_output_router)
app.include_router(jobsies_execution_router)

app.include_router(web_pages_router)
app.include_router(definition_component_router)
app.include_router(results_component_router)
