from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from jobsies.api.health import router as health_router
from jobsies.api.v1 import jobsies_definition_router, jobsies_execution_router, jobsies_output_router
from jobsies.api.web import definition_component_router, results_component_router, web_pages_router
from jobsies.config import get_config

config = get_config()

tags_metadata = [
    {
        "name": "Health",
        "description": "Running status of the application.",
    },
    {
        "name": "Jobsies Definition",
        "description": "Define jobsies and theirs schedule.",
    },
]

app = FastAPI(
    title="Jobsies",
    version=config.app_version,
    docs_url="/docs",
    openapi_tags=tags_metadata,
)

app.mount("/static", StaticFiles(directory="src/jobsies/static"), name="static")

app.include_router(health_router)

app.include_router(jobsies_definition_router)
app.include_router(jobsies_output_router)
app.include_router(jobsies_execution_router)

app.include_router(web_pages_router)
app.include_router(definition_component_router)
app.include_router(results_component_router)
