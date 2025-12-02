"""
UserSkillScore model for aggregated/consolidated skill profiles.
"""
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.core.user import User
    from app.db.models.evaluation.evaluation_cycle import EvaluationCycle
    from app.db.models.core.skill import Skill


class UserSkillScore(Base):
    """
    Consolidated skill profile for a user in an evaluation cycle.
    
    Aggregates multiple evaluation scores into a unified profile:
    - Average scores across evaluators
    - Statistical confidence measures
    - Source tracking (360°, self-only, manager-only, etc.)
    - Raw statistical metadata
    """
    __tablename__ = "user_skill_scores"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Foreign Keys
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    evaluation_cycle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evaluation_cycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    skill_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Aggregation Metadata
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )  # 360_aggregated, self_only, manager_only
    
    # Aggregated Score Data
    score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True
    )
    raw_stats: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True
    )  # {"mean": 7.8, "std": 0.5, "n": 8}

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
    user: Mapped["User"] = relationship(
        back_populates="user_skill_scores",
    )
    evaluation_cycle: Mapped["EvaluationCycle"] = relationship(
        back_populates="user_skill_scores",
    )
    skill: Mapped["Skill"] = relationship(
        back_populates="user_scores",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "evaluation_cycle_id",
            "skill_id",
            "source",
            name="uq_user_cycle_skill_source"
        ),
        CheckConstraint(
            "score >= 0 AND score <= 10",
            name="ck_score_range"
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_confidence_range"
        ),
    )


    def __repr__(self) -> str:
        return (
            f"<UserSkillScore(user_id={self.user_id}, skill_id={self.skill_id}, "
            f"source='{self.source}', score={self.score})>"
        )
