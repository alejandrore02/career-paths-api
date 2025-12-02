"""
RoleSkillRequirement model for the competency matrix (role → required skills).
"""
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.core import Role, Skill


class RoleSkillRequirement(Base):
    """
    Competency matrix: defines required skill levels per role.
    
    Used for:
    - Gap analysis (comparing user skill levels vs role requirements)
    - Career path generation (identifying development needs)
    - Readiness assessment (determining preparedness for roles)
    """
    __tablename__ = "role_skill_requirements"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Foreign Keys
    role_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    skill_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Requirement Fields
    required_level: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False
    )
    importance_weight: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=1.0
    )
    is_core: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    framework_version: Mapped[Optional[str]] = mapped_column(
        String(50),
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
    role: Mapped["Role"] = relationship("Role", back_populates="skill_requirements")
    skill: Mapped["Skill"] = relationship(back_populates="role_requirements")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "skill_id",
            "framework_version",
            name="uq_role_skill_framework"
        ),
        CheckConstraint(
            "required_level >= 0 AND required_level <= 10",
            name="ck_required_level_range"
        ),
        CheckConstraint(
            "importance_weight >= 0 AND importance_weight <= 1",
            name="ck_importance_weight_range"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<RoleSkillRequirement(role_id={self.role_id}, skill_id={self.skill_id}, "
            f"required_level={self.required_level})>"
        )
