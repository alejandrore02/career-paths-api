# tests/factories/skills.py
from uuid import uuid4
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Skill


DEFAULT_SKILLS_SPECS: list[dict] = [
    {
        "name": "Liderazgo",
        "description": "Capacidad para liderar equipos",
        "category": "soft_skills",
    },
    {
        "name": "Comunicación",
        "description": "Habilidades de comunicación efectiva",
        "category": "soft_skills",
    },
    {
        "name": "Python",
        "description": "Programación en Python",
        "category": "technical_skills",
    },
    {
        "name": "Resolución de Problemas",
        "description": "Capacidad analítica para resolver problemas complejos",
        "category": "soft_skills",
    },
    {
        "name": "Trabajo en Equipo",
        "description": "Colaboración efectiva con otros",
        "category": "soft_skills",
    },
]


async def ensure_skills_catalog(
    db_session: AsyncSession,
    specs: Sequence[dict] | None = None,
) -> list[Skill]:
    """
    Ensure a catalog of skills exists.

    Idempotente: si ya existen, las reutiliza; si faltan, las crea.
    """
    if specs is None:
        specs = DEFAULT_SKILLS_SPECS

    names = [s["name"] for s in specs]

    result = await db_session.execute(
        select(Skill).where(Skill.name.in_(names))
    )
    existing_skills = result.scalars().all()
    existing_by_name = {s.name: s for s in existing_skills}

    skills: list[Skill] = []

    for spec in specs:
        existing = existing_by_name.get(spec["name"])
        if existing:
            skills.append(existing)
            continue

        skill = Skill(
            id=uuid4(),
            name=spec["name"],
            description=spec["description"],
            category=spec["category"],
            is_active=True,
            is_global=True,
        )
        db_session.add(skill)
        skills.append(skill)

    await db_session.flush()

    for skill in skills:
        await db_session.refresh(skill)

    return skills
