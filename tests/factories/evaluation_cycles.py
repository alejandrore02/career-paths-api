# tests/factories/evaluation_cycles.py
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EvaluationCycle, User


async def create_active_cycle(
    db_session: AsyncSession,
    *,
    created_by: User,
    name: str = "Q1 2025 360° Review",
    description: str = "First quarter 2025 performance review cycle",
    start_offset_days: int = -30,
    end_offset_days: int = 30,
) -> EvaluationCycle:
    """Create an active evaluation cycle."""
    cycle = EvaluationCycle(
        id=uuid4(),
        name=name,
        description=description,
        start_date=date.today() + timedelta(days=start_offset_days),
        end_date=date.today() + timedelta(days=end_offset_days),
        status="active",
        created_by=created_by.id,
    )
    db_session.add(cycle)
    await db_session.flush()
    await db_session.refresh(cycle)
    return cycle


async def create_closed_cycle(
    db_session: AsyncSession,
    *,
    created_by: User,
    name: str = "Q4 2024 360° Review",
    description: str = "Fourth quarter 2024 performance review cycle",
    start_offset_days: int = -120,
    end_offset_days: int = -30,
) -> EvaluationCycle:
    """Create a closed evaluation cycle (no longer accepts evaluations)."""
    cycle = EvaluationCycle(
        id=uuid4(),
        name=name,
        description=description,
        start_date=date.today() + timedelta(days=start_offset_days),
        end_date=date.today() + timedelta(days=end_offset_days),
        status="closed",
        created_by=created_by.id,
    )
    db_session.add(cycle)
    await db_session.flush()
    await db_session.refresh(cycle)
    return cycle
