"""
Skill model representing competencies/abilities in the talent framework.
"""
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.core import RoleSkillRequirement
    from app.db.models.evaluation import EvaluationCompetencyScore
    from app.db.models import UserSkillScore
    from app.db.models.skills_assessment import SkillsAssessmentItem
    from app.db.models.career_path import DevelopmentAction


class Skill(Base):
    """
    Global catalog of competencies/skills/abilities.
    
    Used in:
    - Role skill requirements (competency matrix)
    - Evaluation competency scores (360° reviews)
    - User skill scores (aggregated profiles)
    - Skills assessment items (AI analysis)
    - Development actions (targeted improvements)
    """
    __tablename__ = "skills"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Core Fields
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        index=True
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    behavioral_indicators: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    is_global: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )

    # Relationships
    role_requirements: Mapped[list["RoleSkillRequirement"]] = relationship(
        "RoleSkillRequirement",
        back_populates="skill",
        cascade="all, delete-orphan"
    )
    
    evaluation_scores: Mapped[list["EvaluationCompetencyScore"]] = relationship(
        "EvaluationCompetencyScore",
        back_populates="skill",
        cascade="all, delete-orphan"
    )
    
    user_scores: Mapped[list["UserSkillScore"]] = relationship(
        "UserSkillScore",
        back_populates="skill",
        cascade="all, delete-orphan"
    )
    
    assessment_items: Mapped[list["SkillsAssessmentItem"]] = relationship(
        "SkillsAssessmentItem",
        back_populates="skill"
    )
    
    development_actions: Mapped[list["DevelopmentAction"]] = relationship(
        "DevelopmentAction",
        back_populates="skill"
    )

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name='{self.name}', category='{self.category}')>"
