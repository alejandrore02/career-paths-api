"""
EvaluationCompetencyScore model for individual skill ratings within evaluations.
"""
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.evaluation import Evaluation
    from app.db.models.core import Skill


class EvaluationCompetencyScore(Base):
    """
    Individual competency/skill score within a 360° evaluation.
    
    Stores:
    - Numeric rating for a specific skill
    - Optional comments/justification
    - Links to parent evaluation and skill catalog
    """
    __tablename__ = "evaluation_competency_scores"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Foreign Keys
    evaluation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    skill_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Score Data
    score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    evaluation: Mapped["Evaluation"] = relationship(
        "Evaluation",
        back_populates="competency_scores"
    )
    skill: Mapped["Skill"] = relationship(
        "Skill",
        back_populates="evaluation_scores"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "evaluation_id",
            "skill_id",
            name="uq_evaluation_skill"
        ),
        CheckConstraint(
            "score >= 0 AND score <= 10",
            name="ck_score_range"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<EvaluationCompetencyScore(evaluation_id={self.evaluation_id}, "
            f"skill_id={self.skill_id}, score={self.score})>"
        )
