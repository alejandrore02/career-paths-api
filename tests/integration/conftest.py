"""
Fixtures specific to integration tests.

These fixtures require a real database connection and should NOT be available
to unit tests. Database fixtures are imported from tests/conftest_db.py to
avoid duplication with E2E tests.
"""

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
    inactive_cycle,  # Added for integration tests
)

# Integration-specific fixtures can be added below
# (currently none - all fixtures are shared)
