"""FastAPI application main entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.core.errors import AppError
from app.api.v1 import (
    evaluations,
    evaluation_cycles,
    skills_assessments,
    career_paths,
    users,
    skills,
    roles,
    health,
)

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    setup_logging()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")
    
    # Security warnings
    if settings.is_production():
        if settings.debug:
            logger.critical("⚠️  DEBUG=true in production environment - SECURITY RISK!")
        if "*" in settings.cors_origins:
            logger.critical("⚠️  CORS allows all origins (*) in production - SECURITY RISK!")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Career Paths API - Talent Management System with AI-powered skills assessment and career development recommendations",
    lifespan=lifespan,
    debug=settings.debug,
    # Swagger UI enabled in development/test, disabled in production
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """Handle application errors."""
    logger.error(
        f"AppError: {exc.code} - {exc.message}",
        extra={"details": exc.details},
    )
    details = exc.details
    if details and not isinstance(details, list):
        details = [details]
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": details or [],
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.exception(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": [] if not settings.debug else [{"error": str(exc)}],
        },
    )


# Register routers
app.include_router(health.router)
app.include_router(evaluation_cycles.router, prefix="/api/v1")
app.include_router(evaluations.router, prefix="/api/v1")
app.include_router(skills_assessments.router, prefix="/api/v1")
app.include_router(career_paths.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(skills.router, prefix="/api/v1")
app.include_router(roles.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )
