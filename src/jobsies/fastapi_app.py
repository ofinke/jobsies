from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from jobsies.api.health import router as health_router
from jobsies.api.v1 import jobsies_definition_router, jobsies_execution_router, jobsies_output_router
from jobsies.api.web import (
    definition_component_router,
    documentation_component_router,
    results_component_router,
    web_pages_router,
    worker_component_router,
)
from jobsies.services import DefinitionService
from jobsies.settings import get_settings

settings = get_settings()

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


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Refresh jobsie executability statuses before application starts."""
    DefinitionService().refresh_executability_statuses()
    yield


app = FastAPI(
    title="Jobsies",
    version=version("jobsies"),
    docs_url="/swagger",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=settings.static_location_), name="static")

app.include_router(health_router)

app.include_router(jobsies_definition_router)
app.include_router(jobsies_output_router)
app.include_router(jobsies_execution_router)

app.include_router(web_pages_router)
app.include_router(definition_component_router)
app.include_router(documentation_component_router)
app.include_router(results_component_router)
app.include_router(worker_component_router)
