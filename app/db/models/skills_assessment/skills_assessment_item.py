"""
SkillsAssessmentItem model for detailed AI assessment results.
"""
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.skills_assessment import SkillsAssessment
    from app.db.models.core import Skill
    from app.db.models.core import Role


class SkillsAssessmentItem(Base):
    """
    Detailed structured output from AI skills assessment.
    
    Item types:
    - strength: Top competencies
    - growth_area: Development opportunities
    - hidden_talent: Underutilized skills
    - role_readiness: Preparedness for specific roles
    """
    __tablename__ = "skills_assessment_items"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Foreign Keys
    skills_assessment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    role_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Item Classification
    item_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # strength, growth_area, hidden_talent, role_readiness
    
    # Item Content
    label: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    current_level: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True
    )
    target_level: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True
    )
    gap_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True
    )
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # 0–1 readiness percentage (internal representation)
    readiness_percentage: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True
    )
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # JSONB metadata (column name 'metadata' in DB, attribute 'item_metadata' in Python)
    # Using different attribute name to avoid conflict with SQLAlchemy reserved 'metadata'
    item_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata",  # Column name in database
        JSONB,
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
    skills_assessment: Mapped["SkillsAssessment"] = relationship(
        "SkillsAssessment",
        back_populates="items",
    )
    skill: Mapped[Optional["Skill"]] = relationship(
        "Skill",
        back_populates="assessment_items",
    )
    role: Mapped[Optional["Role"]] = relationship("Role")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "current_level >= 0 AND current_level <= 10",
            name="ck_current_level_range"
        ),
        CheckConstraint(
            "target_level >= 0 AND target_level <= 10",
            name="ck_target_level_range"
        ),
        CheckConstraint(
            "gap_score >= 0 AND gap_score <= 10",
            name="ck_gap_score_range"
        ),
        CheckConstraint(
            "score >= 0 AND score <= 10",
            name="ck_score_range"
        ),
        CheckConstraint(
            "readiness_percentage >= 0 AND readiness_percentage <= 1",
            name="ck_readiness_percentage_range"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<SkillsAssessmentItem(id={self.id}, item_type='{self.item_type}', "
            f"label='{self.label}')>"
        )
