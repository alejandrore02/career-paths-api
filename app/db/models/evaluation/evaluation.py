"""
Evaluation model for 360° performance reviews.
"""
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.core.user import User
    from app.db.models.evaluation.evaluation_cycle import EvaluationCycle
    from app.db.models.evaluation.evaluation_competency_score import EvaluationCompetencyScore


class Evaluation(Base):
    """
    Represents a single 360° evaluation from one evaluator to one evaluated user.
    
    Captures:
    - Self-assessments (user evaluates themselves)
    - Peer reviews (colleagues evaluate user)
    - Manager reviews (manager evaluates direct report)
    - Direct report reviews (subordinate evaluates manager)
    """
    __tablename__ = "evaluations"

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
    evaluator_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Evaluation Metadata
    evaluator_relationship: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )  # self, peer, manager, direct_report
    
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )  # pending, submitted, cancelled
    
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
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
    user: Mapped["User"] = relationship(
        foreign_keys=[user_id],
        back_populates="evaluations_as_evaluated"
    )
    
    evaluator: Mapped["User"] = relationship(
        foreign_keys=[evaluator_id],
        back_populates="evaluations_as_evaluator"
    )
    
    evaluation_cycle: Mapped["EvaluationCycle"] = relationship(
        back_populates="evaluations"
    )
    
    competency_scores: Mapped[list["EvaluationCompetencyScore"]] = relationship(
        back_populates="evaluation",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Evaluation(id={self.id}, user_id={self.user_id}, "
            f"evaluator_relationship='{self.evaluator_relationship}', "
            f"status='{self.status}')>"
        )
