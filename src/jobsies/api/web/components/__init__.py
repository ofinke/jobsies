from .config import router as config_component_router
from .definition import router as definition_component_router
from .documentation import router as documentation_component_router
from .output import router as results_component_router
from .worker import router as worker_component_router

__all__ = [
    "config_component_router",
    "definition_component_router",
    "documentation_component_router",
    "results_component_router",
    "worker_component_router",
]
