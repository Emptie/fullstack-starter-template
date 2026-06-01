"""Health check endpoint.

Verifies that the backend is running and the type bridge works correctly.
The HealthCheck Pydantic model is exported to TypeScript via `make generate`.
"""

from fastapi import APIRouter

from starter_shared.types.health import HealthCheck

router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """Check if the web backend is healthy.

    Returns a HealthCheck model that is shared with the frontend via the type bridge.
    """
    return HealthCheck(
        status="ok",
        version="0.1.0",
        database="connected",
    )
