"""Health check endpoints."""

from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    status: str
    database: str
    ai_services: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check."""
    from app import __version__
    
    return HealthResponse(
        status="healthy",
        version=__version__,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """Readiness check including dependencies."""
    # TODO: Add actual DB and service checks
    return ReadinessResponse(
        status="ready",
        database="connected",
        ai_services="available",
    )
