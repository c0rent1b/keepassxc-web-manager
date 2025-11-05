"""
Health check endpoints.

Provides system health status for monitoring.
"""

import logging

from fastapi import APIRouter

from app.api.dependencies import CacheDep, RepositoryDep, SettingsDep
from app.api.schemas import HealthCheckResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health check",
    description="Check if the service is healthy and all dependencies are available",
)
async def health_check(
    settings: SettingsDep,
    repository: RepositoryDep,
    cache: CacheDep,
) -> HealthCheckResponse:
    """
    Health check endpoint.

    Checks:
    - KeePassXC CLI availability
    - Cache backend health
    - Application status

    Returns:
        HealthCheckResponse with system status
    """
    logger.debug("Health check requested")

    # Check KeePassXC CLI
    keepassxc_available = await repository.check_cli_available()

    # Check cache
    cache_healthy = await cache.health_check()

    # Determine overall status
    if keepassxc_available and cache_healthy:
        status_str = "healthy"
    elif keepassxc_available:
        status_str = "degraded"  # Cache down but core functionality works
    else:
        status_str = "unhealthy"  # KeePassXC not available

    logger.info(
        f"Health check: {status_str} "
        f"(KeePassXC: {keepassxc_available}, Cache: {cache_healthy})"
    )

    return HealthCheckResponse(
        status=status_str,
        version=settings.APP_VERSION,
        keepassxc_available=keepassxc_available,
        cache_healthy=cache_healthy,
    )


@router.get(
    "/ping",
    summary="Ping",
    description="Simple ping endpoint for uptime checks",
    include_in_schema=False,
)
async def ping() -> dict:
    """
    Ping endpoint.

    Minimal endpoint for simple uptime checks (e.g., load balancer health checks).

    Returns:
        Simple pong response
    """
    return {"ping": "pong"}
