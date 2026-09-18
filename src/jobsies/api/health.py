from datetime import datetime

from fastapi import APIRouter, Response, status
from loguru import logger
from pytz import timezone
from sqlalchemy import text

from jobsies.database import get_db_handler
from jobsies.schemas.api.health import ResponseHealthLiveness, ResponseHealthReadiness
from jobsies.services import get_redis_handler
from jobsies.settings import get_settings

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
)
def app_liveness() -> ResponseHealthLiveness:
    """Returns status UP if application is alive."""
    logger.debug("GET /health/live called")
    return ResponseHealthLiveness(
        status="UP",
        timestamp=datetime.now(timezone(settings.tz_info)).strftime("%Y-%m-%dT%H:%M:%S%z"),
    )


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
)
def app_readiness(response: Response) -> ResponseHealthReadiness:
    """Return the availability status of the application components."""
    logger.debug("GET /health/ready called")
    components: dict[str, str] = {}

    try:
        with get_db_handler().engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as err:  # noqa: BLE001
        logger.error(f"Database readiness check failed: {err!s}")
        components["database"] = "DOWN"
    else:
        components["database"] = "UP"

    try:
        get_redis_handler(settings.broker_redis_url).client.ping()
    except Exception as err:  # noqa: BLE001
        logger.error(f"Redis readiness check failed: {err!s}")
        components["redis"] = "DOWN"
    else:
        components["redis"] = "UP"

    is_ready = all(component == "UP" for component in components.values())
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ResponseHealthReadiness(
        status="UP" if is_ready else "DOWN",
        timestamp=datetime.now(timezone(settings.tz_info)).strftime("%Y-%m-%dT%H:%M:%S%z"),
        components=components,
    )
