"""
DevelopmentAction model for recommended learning/growth activities.
"""
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Integer, String, Text, func, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.career_path import CareerPathStep
    from app.db.models.core import Skill


class DevelopmentAction(Base):
    """
    Recommended development activity for a career path step.
    
    Types:
    - course: Formal training programs
    - project: Hands-on assignments
    - mentoring: Coaching relationships
    - shadowing: Observational learning
    - certification: Professional credentials
    """
    __tablename__ = "development_actions"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Foreign Keys
    career_path_step_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("career_path_steps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    skill_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Action Details
    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )  # course, project, mentoring, shadowing, certification
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    estimated_effort_hours: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    
    # JSONB metadata (column name 'metadata' in DB, attribute 'action_metadata' in Python)
    # Using different attribute name to avoid conflict with SQLAlchemy reserved 'metadata'
    action_metadata: Mapped[Optional[dict]] = mapped_column(
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
    career_path_step: Mapped["CareerPathStep"] = relationship(
        "CareerPathStep",
        back_populates="development_actions"
    )
    skill: Mapped[Optional["Skill"]] = relationship(
        "Skill",
        back_populates="development_actions"
    )

    def __repr__(self) -> str:
        return (
            f"<DevelopmentAction(id={self.id}, action_type='{self.action_type}', "
            f"title='{self.title}')>"
        )
