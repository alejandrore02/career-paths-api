"""Structured logging configuration."""

import logging
import sys
from typing import Any

from app.core.config import get_settings


class RequestIdFilter(logging.Filter):
    """Add request_id to log records if available in context."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id attribute to record."""
        if not hasattr(record, "request_id"):
            record.request_id = "N/A"
        return True


def setup_logging() -> None:
    """Configure application logging."""
    settings = get_settings()
    
    # Create formatter
    log_format = (
        "[%(asctime)s] [%(levelname)s] [%(name)s] "
        "[request_id=%(request_id)s] %(message)s"
    )
    
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    
    # -------------------------------------------------------------------------
    # Root logger
    # -------------------------------------------------------------------------
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Limpiar handlers previos (por si uvicorn ya puso alguno)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestIdFilter())
    root_logger.addHandler(console_handler)

    # -------------------------------------------------------------------------
    # Third-party loggers
    # -------------------------------------------------------------------------
    # Por defecto, en dev/test queremos ver más detalle
    if settings.is_development() or settings.is_test():
        logging.getLogger("uvicorn").setLevel(logging.INFO)
        logging.getLogger("uvicorn.error").setLevel(logging.INFO)
        logging.getLogger("uvicorn.access").setLevel(logging.INFO)

        # Info útil de SQLAlchemy (además de echo=True si lo activas)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        logging.getLogger("sqlalchemy.pool").setLevel(logging.INFO)

        # Llamadas HTTP de httpx (por ejemplo tus clientes de AI)
        logging.getLogger("httpx").setLevel(logging.INFO)
    else:
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)
