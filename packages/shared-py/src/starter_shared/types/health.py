"""Health check types — used to verify the type bridge works end-to-end."""

from pydantic import BaseModel


class HealthCheck(BaseModel):
    """Health check response model.

    This model is exported to TypeScript via the type bridge.
    It serves as a simple verification that the entire pipeline works.
    """

    status: str = "ok"
    version: str = "0.1.0"
    database: str = "connected"
