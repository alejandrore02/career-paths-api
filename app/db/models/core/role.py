"""
Role model representing job positions/titles in the organization.
"""
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.core import User, RoleSkillRequirement
    from app.db.models.career_path import CareerPathStep


class Role(Base):
    """
    Catalog of positions/job titles in the organization.
    
    Used for:
    - Assigning users to roles
    - Defining skill requirements per role (competency matrix)
    - Career path target roles
    """
    __tablename__ = "roles"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Core Fields
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        index=True
    )
    job_family: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    seniority_level: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

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
    users: Mapped[list["User"]] = relationship(
        foreign_keys="User.role_id",
        back_populates="role"
    )
    
    skill_requirements: Mapped[list["RoleSkillRequirement"]] = relationship(
        "RoleSkillRequirement",
        back_populates="role",
        cascade="all, delete-orphan"
    )
    
    career_path_steps: Mapped[list["CareerPathStep"]] = relationship(
        foreign_keys="CareerPathStep.target_role_id",
        back_populates="target_role"
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}', seniority='{self.seniority_level}')>"
