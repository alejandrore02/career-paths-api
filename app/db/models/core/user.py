"""
User model representing collaborators in the talent management system.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models import Role, Evaluation, SkillsAssessment, CareerPath, UserSkillScore



class User(Base):
    """
    Represents a collaborator in the organization.

    Relationships:
    - role: current role/position
    - manager: direct manager (self-referential)
    - direct_reports: users who report to this user
    - evaluations_as_evaluated: evaluations where this user is evaluated
    - evaluations_as_evaluator: evaluations where this user is the evaluator
    - skills_assessments: AI-generated skills assessments
    - career_paths: career path recommendations
    """

    __tablename__ = "users"

    # --- Primary key ---
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # --- Core fields ---
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # --- Foreign keys ---
    role_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    manager_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # --- HR fields ---
    hire_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # --- Timestamps ---
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # --- Relationships ---

    # Role relationship
    role: Mapped[Optional["Role"]] = relationship(
        "Role",
        back_populates="users",
    )

    # Self-referential hierarchy
    manager: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side="User.id",
        foreign_keys=[manager_id],
        back_populates="direct_reports",
        passive_deletes=True,  # compatible con ondelete="SET NULL"
    )
    direct_reports: Mapped[list["User"]] = relationship(
        "User",
        back_populates="manager",
        foreign_keys=[manager_id],
    )

    # Evaluations
    evaluations_as_evaluated: Mapped[list["Evaluation"]] = relationship(
        "Evaluation",
        foreign_keys="Evaluation.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    evaluations_as_evaluator: Mapped[list["Evaluation"]] = relationship(
        "Evaluation",
        foreign_keys="Evaluation.evaluator_id",
        back_populates="evaluator",
    )

    # Skills assessments
    skills_assessments: Mapped[list["SkillsAssessment"]] = relationship(
        "SkillsAssessment",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Career paths
    career_paths: Mapped[list["CareerPath"]] = relationship(
        "CareerPath",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # User skill scores (aggregated 360° results)
    user_skill_scores: Mapped[list["UserSkillScore"]] = relationship(
        "UserSkillScore",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', full_name='{self.full_name}')>"
