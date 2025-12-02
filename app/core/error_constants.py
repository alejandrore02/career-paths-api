"""Shared error codes and default messages/status for the API."""

# Centralized definitions to avoid hard-coded strings across services
ERROR_CODES: dict[str, dict[str, object]] = {
    "APP_ERROR": {
        "message": "Application error",
        "status_code": 500,
    },
    "NOT_FOUND": {
        "message": "Resource not found",
        "status_code": 404,
    },
    "VALIDATION_ERROR": {
        "message": "Validation failed",
        "status_code": 422,
    },
    "CONFLICT": {
        "message": "Conflict",
        "status_code": 409,
    },
    "EXTERNAL_SERVICE_ERROR": {
        "message": "External service error",
        "status_code": 502,
    },
    "AI_SERVICE_ERROR": {
        "message": "AI service error",
        "status_code": 502,
    },
    "INTERNAL_SERVER_ERROR": {
        "message": "An unexpected error occurred",
        "status_code": 500,
    },
}
