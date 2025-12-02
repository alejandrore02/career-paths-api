"""
Shared database fixtures for integration and E2E tests.

These fixtures are imported by tests/integration/conftest.py and tests/e2e/conftest.py
to avoid duplication.
"""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.main import app
from tests.factories.evaluation_cycles import create_active_cycle, create_closed_cycle
from tests.factories.skills import ensure_skills_catalog
from tests.factories.users import create_evaluator, create_manager, create_user


# ============================================================================
# Test Database Configuration
# ============================================================================

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/talent_test"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an instance of the default event loop for the test session.
    
    This fixture ensures all async tests share the same event loop,
    preventing issues with multiple event loops.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """
    Create async database engine for test session.
    
    Uses NullPool to avoid connection pool issues in tests.
    Creates all tables at session start, drops at session end.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session for integration/E2E tests.
    
    Integration and E2E tests may commit transactions (simulating real usage),
    so we don't wrap in a transaction context. Database cleanup
    happens between tests via cleanup_db fixture to maintain isolation.
    """
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session
        # Close session after test
        await session.close()


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db(db_engine):
    """
    Clean database between integration/E2E tests.
    
    Truncates all tables after each test to ensure isolation.
    Auto-used for all tests that import from this module.
    """
    yield  # Test runs here
    
    # Cleanup after test
    async with db_engine.begin() as conn:
        # Disable foreign key checks temporarily
        await conn.execute(text("SET session_replication_role = 'replica';"))
        
        # Get all table names
        table_names = [table.name for table in Base.metadata.sorted_tables]
        
        # Truncate all tables
        for table_name in table_names:
            if table_name != "alembic_version":
                await conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE;"))
        
        # Re-enable foreign key checks
        await conn.execute(text("SET session_replication_role = 'origin';"))


@pytest_asyncio.fixture
async def uow(db_session: AsyncSession) -> UnitOfWork:
    """
    Provide a Unit of Work instance for tests.
    
    Uses the same session as db_session fixture.
    """
    return UnitOfWork(db_session)


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP client for API testing.
    
    Overrides the database dependency to use the test session.
    This ensures all API calls use the same transaction.
    """
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    
    app.dependency_overrides.clear()


# ============================================================================
# Sample Data Fixtures (Shared)
# ============================================================================

@pytest_asyncio.fixture
async def sample_user(db_session: AsyncSession):
    """Create a sample user for testing."""
    user = await create_user(db_session)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def sample_evaluator(db_session: AsyncSession):
    """Create a sample evaluator for testing."""
    evaluator = await create_evaluator(db_session)
    await db_session.commit()
    return evaluator


@pytest_asyncio.fixture
async def sample_manager(db_session: AsyncSession):
    """Create a sample manager for testing."""
    manager = await create_manager(db_session)
    await db_session.commit()
    return manager


@pytest_asyncio.fixture
async def sample_skills(db_session: AsyncSession):
    """Create sample skills catalog for testing."""
    skills = await ensure_skills_catalog(db_session)
    await db_session.commit()
    return skills


@pytest_asyncio.fixture
async def sample_cycle(db_session: AsyncSession, sample_user):
    """Create an active evaluation cycle for testing."""
    cycle = await create_active_cycle(db_session, created_by=sample_user)
    await db_session.commit()
    return cycle


@pytest_asyncio.fixture
async def sample_closed_cycle(db_session: AsyncSession, sample_user):
    """Create a closed evaluation cycle for testing."""
    cycle = await create_closed_cycle(db_session, created_by=sample_user)
    await db_session.commit()
    return cycle


@pytest_asyncio.fixture
async def inactive_cycle(db_session: AsyncSession, sample_user):
    """Alias for sample_closed_cycle - cycle with status='closed' (inactive)."""
    cycle = await create_closed_cycle(db_session, created_by=sample_user)
    await db_session.commit()
    return cycle
