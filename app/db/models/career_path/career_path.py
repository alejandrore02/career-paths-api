"""
CareerPath model for AI-generated career development routes.

This file defines the `CareerPath` model with clean relationships and
no duplicated or syntactically invalid code. Relationships use string
identifiers to avoid import-time circular dependencies.
"""
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.core import User  
    from app.db.models.skills_assessment import SkillsAssessment  
    from app.db.models.career_path import CareerPathStep  


class CareerPath(Base):
    """AI-generated career development path for a user.

    Represents recommended progression routes, alternative options and
    multi-step development journeys with feasibility estimates.
    """

    __tablename__ = "career_paths"

    # Primary Key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skills_assessment_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills_assessments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Path Metadata
    path_name: Mapped[str] = mapped_column(String(200), nullable=False)
    recommended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    feasibility_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    total_duration_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Path Status
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="proposed", index=True)

    # AI Metadata
    ai_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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

    # Relationships (use string names to avoid import cycles)
    user: Mapped["User"] = relationship("User", back_populates="career_paths")
    skills_assessment: Mapped[Optional["SkillsAssessment"]] = relationship(
        "SkillsAssessment", back_populates="career_paths"
    )
    steps: Mapped[list["CareerPathStep"]] = relationship(
        "CareerPathStep",
        back_populates="career_path",
        cascade="all, delete-orphan",
        order_by="CareerPathStep.step_number",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "feasibility_score >= 0 AND feasibility_score <= 1",
            name="ck_feasibility_score_range"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<CareerPath(id={self.id}, path_name='{self.path_name}', "
            f"status='{self.status}', recommended={self.recommended})>"
        )
