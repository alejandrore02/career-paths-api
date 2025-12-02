"""
SkillsAssessment model for AI-generated competency analysis.
"""
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String, Text, func, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.core import User
    from app.db.models.evaluation import EvaluationCycle
    from app.db.models.skills_assessment import SkillsAssessmentItem
    from app.db.models.career_path import CareerPath


class SkillsAssessment(Base):
    """
    AI-generated skills assessment for a user.
    
    Consolidates:
    - 360° evaluation data
    - AI analysis (strengths, growth areas, hidden talents)
    - Role readiness scores
    - Model metadata and traceability
    """
    __tablename__ = "skills_assessments"

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
    evaluation_cycle_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evaluation_cycles.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Assessment Status
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True
    )  # pending, processing, completed, failed
    
    # Assessment Content
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # AI Model Metadata
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Raw AI Data
    raw_request: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    raw_response: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Error Handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Processing Timestamp
    processed_at: Mapped[Optional[datetime]] = mapped_column(
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
        "User",
        back_populates="skills_assessments"
    )
    evaluation_cycle: Mapped[Optional["EvaluationCycle"]] = relationship(
        "EvaluationCycle",
        back_populates="skills_assessments"
    )
    items: Mapped[list["SkillsAssessmentItem"]] = relationship(
        "SkillsAssessmentItem",
        back_populates="skills_assessment",
        cascade="all, delete-orphan"
    )
    career_paths: Mapped[list["CareerPath"]] = relationship(
        "CareerPath",
        back_populates="skills_assessment"
    )

    def __repr__(self) -> str:
        return (
            f"<SkillsAssessment(id={self.id}, user_id={self.user_id}, "
            f"status='{self.status}')>"
        )
