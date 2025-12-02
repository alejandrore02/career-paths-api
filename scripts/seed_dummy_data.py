"""Seed dummy data to exercise E2E flows (evaluations → skills assessment → career paths)."""

import argparse
import asyncio
from datetime import date, datetime, timedelta, timezone
from typing import Sequence

from uuid import uuid4

from app.db.session import AsyncSessionLocal
from app.db.unit_of_work import UnitOfWork
from app.db.models import (
    Role,
    Skill,
    User,
    EvaluationCycle,
)
from app.schemas.evaluation.evaluation import EvaluationCreate, CompetencyScoreCreate
from app.services.evaluation_service import EvaluationService
from app.integrations.ai_skills_client import AISkillsClient
from app.integrations.ai_career_client import AICareerClient


async def _get_or_create_role(uow: UnitOfWork, name: str, job_family: str, seniority: str) -> Role:
    role = await uow.roles.get_by_name(name)
    if role:
        return role
    role = Role(
        id=uuid4(),
        name=name,
        job_family=job_family,
        seniority_level=seniority,
        is_active=True,
    )
    await uow.roles.create(role)
    await uow.commit()
    return role


async def _get_or_create_skill(uow: UnitOfWork, name: str, category: str) -> Skill:
    skill = await uow.skills.get_by_name(name)
    if skill:
        return skill
    skill = Skill(
        id=uuid4(),
        name=name,
        category=category,
        is_global=True,
        is_active=True,
    )
    await uow.skills.create(skill)
    await uow.commit()
    return skill


async def _get_or_create_user(
    uow: UnitOfWork,
    email: str,
    full_name: str,
    role_id,
    manager_id=None,
) -> User:
    user = await uow.users.get_by_email(email)
    if user:
        if user.role_id != role_id or user.manager_id != manager_id:
            user.role_id = role_id
            user.manager_id = manager_id
            await uow.users.update(user)
            await uow.commit()
        return user

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
    await uow.commit()
    return user


async def seed(process_pipeline: bool = False) -> None:
    """Create roles, skills, users, evaluations and optionally run the full AI pipeline."""
    async with AsyncSessionLocal() as session:
        uow = UnitOfWork(session)
        ai_skills_client = AISkillsClient()
        ai_career_client = AICareerClient()

        try:
            # Catalog data
            manager_role = await _get_or_create_role(uow, "Gerente de Sucursal", "Operaciones", "Senior")
            regional_role = await _get_or_create_role(uow, "Gerente Regional", "Operaciones", "Director")
            peer_role = await _get_or_create_role(uow, "Especialista Senior en Operaciones", "Operaciones", "Senior")

            skill_names = [
                ("Liderazgo", "soft"),
                ("Comunicación", "soft"),
                ("Pensamiento Estratégico", "leadership"),
                ("Gestión de P&L", "finance"),
            ]
            skills = {name: await _get_or_create_skill(uow, name, category) for name, category in skill_names}

            # Users
            manager_user = await _get_or_create_user(
                uow,
                email="manager.demo@example.com",
                full_name="Manager Demo",
                role_id=regional_role.id,
            )
            evaluated_user = await _get_or_create_user(
                uow,
                email="colaborador.demo@example.com",
                full_name="Colaborador Demo",
                role_id=manager_role.id,
                manager_id=manager_user.id,
            )
            peer_one = await _get_or_create_user(
                uow,
                email="peer.one@example.com",
                full_name="Peer Uno",
                role_id=peer_role.id,
            )
            peer_two = await _get_or_create_user(
                uow,
                email="peer.two@example.com",
                full_name="Peer Dos",
                role_id=peer_role.id,
            )

            # Evaluation cycle
            cycle_name = f"Dummy Cycle {date.today().isoformat()}"
            cycle = EvaluationCycle(
                id=uuid4(),
                name=cycle_name,
                description="Ciclo de pruebas E2E",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30),
                status="active",
            )
            await uow.evaluation_cycles.create(cycle)
            await uow.commit()

            eval_service = EvaluationService(
                uow=uow,
                ai_skills_client=ai_skills_client,
            )

            base_competencies: Sequence[CompetencyScoreCreate] = [
                CompetencyScoreCreate(competency_name="Liderazgo", score=8.5, comments="Buen liderazgo."),
                CompetencyScoreCreate(competency_name="Comunicación", score=8.0, comments="Comunicación clara."),
                CompetencyScoreCreate(competency_name="Pensamiento Estratégico", score=7.0, comments="Necesita mejorar."),
                CompetencyScoreCreate(competency_name="Gestión de P&L", score=6.5, comments=""),
            ]

            # Create evaluations (self, manager, peers)
            created_eval_ids: list = []
            relationships = [
                ("self", evaluated_user.id),
                ("manager", manager_user.id),
                ("peer", peer_one.id),
                ("peer", peer_two.id),
            ]
            for relationship, evaluator_id in relationships:
                evaluation = EvaluationCreate(
                    user_id=evaluated_user.id,
                    evaluation_cycle_id=cycle.id,
                    evaluator_id=evaluator_id,
                    evaluator_relationship=relationship,
                    competencies=list(base_competencies),
                )
                created = await eval_service.create_evaluation(evaluation)
                created_eval_ids.append(created.id)

            print(f"Created cycle '{cycle.name}' with {len(created_eval_ids)} evaluations.")

            if process_pipeline:
                # Use the self-evaluation ID to kick off processing (it loads all related evaluations)
                pipeline_result = await eval_service.process_evaluation(created_eval_ids[0])
                print("Pipeline executed:", pipeline_result)
            else:
                print("Pipeline not executed. Run with --process to trigger AI steps.")

        finally:
            await ai_skills_client.close()
            await ai_career_client.close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed dummy data for E2E testing.")
    parser.add_argument(
        "--process",
        action="store_true",
        help="Run full AI pipeline (skills assessment + career paths) after seeding.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    asyncio.run(seed(process_pipeline=args.process))
