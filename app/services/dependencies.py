"""DI dependencies for services and AI clients."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.services.evaluation_service import EvaluationService
from app.services.evaluation_cycle_service import EvaluationCycleService
from app.services.user_service import UserService
from app.services.skill_service import SkillService
from app.services.role_service import RoleService
from app.services.skills_assessment_service import SkillsAssessmentService
from app.services.career_path_service import CareerPathService
from app.integrations.ai_skills_client import AISkillsClient
from app.integrations.ai_career_client import AICareerClient


async def get_uow(session: AsyncSession = Depends(get_db)) -> UnitOfWork:
    return UnitOfWork(session)


async def get_ai_skills_client() -> AsyncGenerator[AISkillsClient, None]:
    client = AISkillsClient()
    try:
        yield client
    finally:
        await client.close()


async def get_ai_career_client() -> AsyncGenerator[AICareerClient, None]:
    client = AICareerClient()
    try:
        yield client
    finally:
        await client.close()


async def get_evaluation_service(
    uow: UnitOfWork = Depends(get_uow),
    ai_skills_client: AISkillsClient = Depends(get_ai_skills_client),
) -> EvaluationService:
    return EvaluationService(uow, ai_skills_client)


async def get_evaluation_cycle_service(
    uow: UnitOfWork = Depends(get_uow),
) -> EvaluationCycleService:
    return EvaluationCycleService(uow)


async def get_user_service(
    uow: UnitOfWork = Depends(get_uow),
) -> UserService:
    return UserService(uow)


async def get_skill_service(
    uow: UnitOfWork = Depends(get_uow),
) -> SkillService:
    return SkillService(uow)


async def get_role_service(
    uow: UnitOfWork = Depends(get_uow),
) -> RoleService:
    return RoleService(uow)


async def get_skills_assessment_service(
    uow: UnitOfWork = Depends(get_uow),
    ai_skills_client: AISkillsClient = Depends(get_ai_skills_client),
) -> SkillsAssessmentService:
    return SkillsAssessmentService(uow, ai_skills_client)


async def get_career_path_service(
    uow: UnitOfWork = Depends(get_uow),
    ai_career_client: AICareerClient = Depends(get_ai_career_client),
) -> CareerPathService:
    return CareerPathService(uow, ai_career_client)
