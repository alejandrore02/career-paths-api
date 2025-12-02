"""
Fixtures specific to E2E tests.

These fixtures require a real database connection and should NOT be available
to unit tests. Database fixtures are imported from tests/conftest_db.py to
avoid duplication with integration tests.
"""

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

# Import all shared database fixtures
from tests.conftest_db import (
    db_engine,
    db_session,
    cleanup_db,
    uow,
    async_client,
    sample_user,
    sample_evaluator,
    sample_manager,
    sample_skills,
    sample_cycle,
    sample_closed_cycle,
)


# ============================================================================
# E2E-Specific Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def e2e_evaluation_scenario(db_session: AsyncSession):
    """
    Create complete evaluation scenario for E2E tests.
    
    This fixture creates all necessary entities for running a complete
    360° evaluation flow:
    - Roles (regional, manager, peer)
    - Skills catalog
    - Users (manager, evaluated user, 2 peers)
    - Active evaluation cycle
    - Base competency template
    
    Returns:
        EvaluationScenario with all entities created and committed
    """
    from app.db.unit_of_work import UnitOfWork
    from tests.helpers.e2e_setup import create_evaluation_scenario
    
    uow = UnitOfWork(db_session)
    scenario = await create_evaluation_scenario(uow)
    
    # Ensure all changes are committed
    await db_session.commit()
    
    return scenario
