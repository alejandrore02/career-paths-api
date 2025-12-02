"""
EvaluationCycle model for grouping 360° evaluations into campaigns/periods.
"""
from datetime import date, datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Date, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.evaluation import Evaluation, UserSkillScore
    from app.db.models.skills_assessment import SkillsAssessment


class EvaluationCycle(Base):
    """
    Represents a performance evaluation campaign/period.
    
    Groups evaluations together for:
    - Organizational performance review periods
    - Batch processing of assessments
    - Historical tracking of evaluation waves
    """
    __tablename__ = "evaluation_cycles"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Core Fields
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True
    )  # draft, active, closed
    
    # Foreign Keys
    created_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True
    )

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
    evaluations: Mapped[list["Evaluation"]] = relationship(
        "Evaluation",
        back_populates="evaluation_cycle",
        cascade="all, delete-orphan"
    )
    
    user_skill_scores: Mapped[list["UserSkillScore"]] = relationship(
        "UserSkillScore",
        back_populates="evaluation_cycle",
        cascade="all, delete-orphan"
    )
    
    skills_assessments: Mapped[list["SkillsAssessment"]] = relationship(
        "SkillsAssessment",
        back_populates="evaluation_cycle"
    )

    def __repr__(self) -> str:
        return (
            f"<EvaluationCycle(id={self.id}, name='{self.name}', "
            f"status='{self.status}')>"
        )
