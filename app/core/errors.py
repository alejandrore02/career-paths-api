"""Custom exceptions and error codes."""

from typing import Any, Optional

from app.core.error_constants import ERROR_CODES


class AppError(Exception):
    """Base application error."""

    def __init__(
        self,
        message: Optional[str] = None,
        code: str = "APP_ERROR",
        status_code: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize application error."""
        definition = ERROR_CODES.get(code, {})
        resolved_message = message or definition.get("message", "Application error")  # type: ignore[arg-type]
        resolved_status = status_code or int(definition.get("status_code", 500))  # type: ignore[arg-type]

        super().__init__(resolved_message)
        self.message = resolved_message
        self.code = code
        self.status_code = resolved_status
        self.details = details or {}


class NotFoundError(AppError):
    """Resource not found error."""

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize not found error."""
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=ERROR_CODES["NOT_FOUND"]["status_code"],  # type: ignore[arg-type]
            details=details,
        )


class ValidationError(AppError):
    """Validation error."""

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize validation error."""
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=ERROR_CODES["VALIDATION_ERROR"]["status_code"],  # type: ignore[arg-type]
            details=details,
        )


class DatabaseError(AppError):
    """Database operation error."""

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize database error."""
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=ERROR_CODES["APP_ERROR"]["status_code"],  # type: ignore[arg-type]
            details=details,
        )


class ExternalServiceError(AppError):
    """External service integration error."""

    def __init__(
        self,
        message: Optional[str] = None,
        service_name: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize external service error."""
        details = details or {}
        if service_name:
            details["service"] = service_name
        super().__init__(
            message=message,
            code="EXTERNAL_SERVICE_ERROR",
            status_code=ERROR_CODES["EXTERNAL_SERVICE_ERROR"]["status_code"],  # type: ignore[arg-type]
            details=details,
        )


class AIServiceError(ExternalServiceError):
    """AI service specific error."""

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize AI service error."""
        super().__init__(
            message=message,
            service_name="AI",
            details=details,
        )


class AuthenticationError(AppError):
    """Authentication error."""

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize authentication error."""
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details,
        )


class AuthorizationError(AppError):
    """Authorization error."""

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize authorization error."""
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details,
        )


class RateLimitError(AppError):
    """Rate limit exceeded error."""

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize rate limit error."""
        super().__init__(
            message=message,
            code="RATE_LIMIT_ERROR",
            status_code=429,
            details=details,
        )


class ConflictError(AppError):
    """Conflict error (e.g., resource already exists)."""

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize conflict error."""
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=ERROR_CODES["CONFLICT"]["status_code"],  # type: ignore[arg-type]
            details=details,
        )
