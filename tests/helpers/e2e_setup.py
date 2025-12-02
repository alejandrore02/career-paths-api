"""Helper functions for E2E test setup.

Extracted from seed_dummy_data.py to be reusable in tests.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Sequence
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Role, Skill, User, EvaluationCycle
from app.db.unit_of_work import UnitOfWork
from app.schemas.evaluation.evaluation import CompetencyScoreCreate


@dataclass
class EvaluationScenario:
    """Complete scenario for E2E evaluation testing."""
    
    # Roles
    manager_role: Role
    regional_role: Role
    peer_role: Role
    
    # Skills
    skills: dict[str, Skill]
    
    # Users
    manager_user: User
    evaluated_user: User
    peer_one: User
    peer_two: User
    
    # Cycle
    cycle: EvaluationCycle
    
    # Base competencies for evaluations
    base_competencies: Sequence[CompetencyScoreCreate]


async def create_role(
    uow: UnitOfWork,
    name: str,
    job_family: str,
    seniority: str,
) -> Role:
    """Create a role for testing."""
    role = Role(
        id=uuid4(),
        name=name,
        job_family=job_family,
        seniority_level=seniority,
        is_active=True,
    )
    await uow.roles.create(role)
    return role


async def create_skill(
    uow: UnitOfWork,
    name: str,
    category: str,
) -> Skill:
    """Create a skill for testing."""
    skill = Skill(
        id=uuid4(),
        name=name,
        category=category,
        is_global=True,
        is_active=True,
    )
    await uow.skills.create(skill)
    return skill


async def create_user(
    uow: UnitOfWork,
    email: str,
    full_name: str,
    role_id: UUID,
    manager_id: UUID | None = None,
) -> User:
    """Create a user for testing."""
    user = User(
        id=uuid4(),
        email=email,
        full_name=full_name,
        role_id=role_id,
        manager_id=manager_id,
        hire_date=date.today() - timedelta(days=365 * 5),
        is_active=True,
    )
    await uow.users.create(user)
    return user


async def create_evaluation_scenario(
    uow: UnitOfWork,
    cycle_name: str | None = None,
) -> EvaluationScenario:
    """Create complete evaluation scenario for E2E testing.
    
    Creates:
    - 3 roles (regional, manager, peer)
    - 4 skills (Liderazgo, Comunicación, Pensamiento Estratégico, Gestión de P&L)
    - 4 users (manager, evaluated, peer1, peer2)
    - 1 active evaluation cycle
    - Base competencies template
    
    Args:
        uow: Unit of Work for database operations
        cycle_name: Optional custom cycle name
        
    Returns:
        EvaluationScenario with all entities created
    """
    # Create roles
    regional_role = await create_role(
        uow,
        name=f"Gerente Regional E2E {uuid4().hex[:8]}",
        job_family="Operaciones",
        seniority="Director",
    )
    
    manager_role = await create_role(
        uow,
        name=f"Gerente de Sucursal E2E {uuid4().hex[:8]}",
        job_family="Operaciones",
        seniority="Senior",
    )
    
    peer_role = await create_role(
        uow,
        name=f"Especialista Senior E2E {uuid4().hex[:8]}",
        job_family="Operaciones",
        seniority="Senior",
    )
    
    # Create skills
    skill_definitions = [
        ("Liderazgo", "soft"),
        ("Comunicación", "soft"),
        ("Pensamiento Estratégico", "leadership"),
        ("Gestión de P&L", "finance"),
    ]
    
    skills = {}
    for skill_name, category in skill_definitions:
        skill = await create_skill(uow, skill_name, category)
        skills[skill_name] = skill
    
    # Create users
    manager_user = await create_user(
        uow,
        email=f"manager.e2e.{uuid4().hex[:8]}@example.com",
        full_name="Manager E2E",
        role_id=regional_role.id,
    )
    
    evaluated_user = await create_user(
        uow,
        email=f"evaluated.e2e.{uuid4().hex[:8]}@example.com",
        full_name="Evaluated User E2E",
        role_id=manager_role.id,
        manager_id=manager_user.id,
    )
    
    peer_one = await create_user(
        uow,
        email=f"peer.one.e2e.{uuid4().hex[:8]}@example.com",
        full_name="Peer One E2E",
        role_id=peer_role.id,
    )
    
    peer_two = await create_user(
        uow,
        email=f"peer.two.e2e.{uuid4().hex[:8]}@example.com",
        full_name="Peer Two E2E",
        role_id=peer_role.id,
    )
    
    # Create evaluation cycle
    if cycle_name is None:
        cycle_name = f"E2E Cycle {date.today().isoformat()} {uuid4().hex[:8]}"
    
    cycle = EvaluationCycle(
        id=uuid4(),
        name=cycle_name,
        description="E2E test evaluation cycle",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        status="active",
    )
    await uow.evaluation_cycles.create(cycle)
    
    # Commit all entities
    await uow.commit()
    
    # Create base competencies template
    base_competencies: Sequence[CompetencyScoreCreate] = [
        CompetencyScoreCreate(
            competency_name="Liderazgo",
            score=8.5,
            comments="Excelente capacidad de liderazgo",
        ),
        CompetencyScoreCreate(
            competency_name="Comunicación",
            score=8.0,
            comments="Comunicación clara y efectiva",
        ),
        CompetencyScoreCreate(
            competency_name="Pensamiento Estratégico",
            score=7.0,
            comments="Buen pensamiento estratégico, puede mejorar",
        ),
        CompetencyScoreCreate(
            competency_name="Gestión de P&L",
            score=6.5,
            comments="Área de oportunidad",
        ),
    ]
    
    return EvaluationScenario(
        manager_role=manager_role,
        regional_role=regional_role,
        peer_role=peer_role,
        skills=skills,
        manager_user=manager_user,
        evaluated_user=evaluated_user,
        peer_one=peer_one,
        peer_two=peer_two,
        cycle=cycle,
        base_competencies=base_competencies,
    )
