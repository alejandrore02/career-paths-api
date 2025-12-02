# app/db/session.py
"""Async database session configuration."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

# Configuración básica del engine
engine_kwargs: dict = {
    "echo": settings.db_echo,
}

# En entorno de tests usamos NullPool para evitar conexiones persistentes
if settings.is_test():
    engine_kwargs["poolclass"] = NullPool
else:
    # En dev/staging/prod dejamos que SQLAlchemy maneje el pool por defecto
    engine_kwargs["pool_pre_ping"] = True

# Crear async engine
engine = create_async_engine(
    settings.database_url,
    **engine_kwargs,
)

# Crear session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    
    Yields:
        AsyncSession instance.
    """
    async with AsyncSessionLocal() as session:
        yield session
