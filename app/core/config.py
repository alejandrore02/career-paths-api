# app/core/config.py
from functools import lru_cache
from typing import Literal, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    app_name: str = Field(
        default="Career Paths API",
        description="Application name for display and logging",
        alias="APP_NAME",
    )
    app_version: str = Field(
        default="0.1.0",
        description="API version",
        alias="APP_VERSION",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode (never use in production)",
        alias="DEBUG",
    )
    # OJO: ahora soporta también "test"
    environment: Literal["development", "staging", "production", "test"] = Field(
        default="development",
        description="Deployment environment",
        alias="ENVIRONMENT",
    )

    # -------------------------------------------------------------------------
    # Server
    # -------------------------------------------------------------------------
    host: str = Field(
        default="0.0.0.0",
        alias="HOST",
        description="Server host",
    )
    port: int = Field(
        default=8000,
        alias="PORT",
        description="Server port",
    )
    reload: bool = Field(
        default=False,
        alias="RELOAD",
        description="Enable auto-reload (only for development)",
    )

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/talent_management",
        alias="DATABASE_URL",
        description="PostgreSQL async connection string",
    )
    db_echo: bool = Field(
        default=False,
        alias="DB_ECHO",
        description="Log all SQL statements (use only in development/test)",
    )

    # -------------------------------------------------------------------------
    # AI Services
    # -------------------------------------------------------------------------
    use_ai_dummy_mode: bool = Field(
        default=True,
        alias="USE_AI_DUMMY_MODE",
        description="Use dummy/mock AI responses (True for dev/testing, False for production)",
    )

    ai_skills_service_url: str = Field(
        default="http://localhost:8001/api/v1/skills",
        alias="AI_SKILLS_SERVICE_URL",
    )
    ai_career_service_url: str = Field(
        default="http://localhost:8001/api/v1/career",
        alias="AI_CAREER_SERVICE_URL",
    )
    ai_skills_api_key: str = Field(
        default="dev-key-skills",
        alias="AI_SKILLS_API_KEY",
    )
    ai_career_api_key: str = Field(
        default="dev-key-career",
        alias="AI_CAREER_API_KEY",
    )

    ai_service_timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        alias="AI_SERVICE_TIMEOUT",
        description="Timeout for AI HTTP calls in seconds",
    )
    ai_service_max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        alias="AI_SERVICE_MAX_RETRIES",
        description="Max retries for AI calls",
    )
    ai_service_retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        alias="AI_SERVICE_RETRY_DELAY",
        description="Initial delay between retries (seconds)",
    )
    ai_circuit_breaker_threshold: int = Field(
        default=5,
        ge=1,
        le=20,
        alias="AI_CIRCUIT_BREAKER_THRESHOLD",
        description="Number of failures before opening circuit",
    )
    ai_circuit_breaker_timeout: int = Field(
        default=60,
        ge=10,
        le=600,
        alias="AI_CIRCUIT_BREAKER_TIMEOUT",
        description="Time (seconds) circuit remains open before half-open",
    )

    # -------------------------------------------------------------------------
    # Security Middleware not implemented yet
    # -------------------------------------------------------------------------
    secret_key: str = Field(
        default="dev-secret-key-CHANGE-ME-IN-PRODUCTION-MINIMUM-32-CHARACTERS",
        alias="SECRET_KEY",
        min_length=32,
        description="Secret key for JWT/session signing (min 32 chars)",
    )
    access_token_expire_minutes: int = Field(
        default=60,
        ge=5,
        le=1440,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="JWT access token expiration in minutes",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=30,
        alias="REFRESH_TOKEN_EXPIRE_DAYS",
        description="JWT refresh token expiration in days",
    )
    allowed_hosts: List[str] = Field(
        default=["*"],
        alias="ALLOWED_HOSTS",
        description="Allowed hosts for production (use specific domains in prod)",
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Reject default secret key outside development/test."""
        environment = info.data.get("environment", "development")
        if environment not in ("development", "test") and "CHANGE-ME" in v:
            raise ValueError(
                "Default secret key detected in non-development environment. "
                "Please set a strong SECRET_KEY environment variable."
            )
        return v

    # -------------------------------------------------------------------------
    # CORS
    # -------------------------------------------------------------------------
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        alias="CORS_ORIGINS",
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(
        default=True,
        alias="CORS_ALLOW_CREDENTIALS",
        description="Allow cookies/auth headers in CORS requests",
    )

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Logging level",
    )
    log_json: bool = Field(
        default=False,
        alias="LOG_JSON",
        description="Output logs in JSON format (recommended for production)",
    )

    @field_validator("log_level")
    @classmethod
    def set_log_level_for_environment(cls, v: str, info) -> str:
        """Auto-adjust log level based on environment if left as INFO."""
        environment = info.data.get("environment", "development")
        if v == "INFO":
            if environment in ("development", "test"):
                return "DEBUG"
            elif environment == "production":
                return "WARNING"
        return v

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def is_production(self) -> bool:
        return self.environment == "production"

    def is_development(self) -> bool:
        return self.environment == "development"

    def is_test(self) -> bool:
        return self.environment == "test"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
