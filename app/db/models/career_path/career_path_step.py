"""
CareerPathStep model for individual stages in career progression.
"""
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Integer, String, Text, UniqueConstraint, func, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.career_path import CareerPath
    from app.db.models.core import Role
    from app.db.models.career_path.development_action import DevelopmentAction


class CareerPathStep(Base):
    """
    Individual step/stage within a career path.
    
    Represents:
    - Sequential progression stages
    - Target roles at each stage
    - Duration estimates
    - Associated development actions
    """
    __tablename__ = "career_path_steps"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Foreign Keys
    career_path_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("career_paths.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_role_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Step Details
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    step_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # JSONB metadata (column name 'metadata' in DB, attribute 'step_metadata' in Python)
    # Using different attribute name to avoid conflict with SQLAlchemy reserved 'metadata'
    step_metadata: Mapped[Optional[dict]] = mapped_column(
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
    career_path: Mapped["CareerPath"] = relationship(
        "CareerPath",
        back_populates="steps",
    )
    target_role: Mapped[Optional["Role"]] = relationship(
        "Role",
        back_populates="career_path_steps",
    )
    development_actions: Mapped[list["DevelopmentAction"]] = relationship(
        "DevelopmentAction",
        back_populates="career_path_step",
        cascade="all, delete-orphan",
    )


    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "career_path_id",
            "step_number",
            name="uq_career_path_step_number"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<CareerPathStep(id={self.id}, career_path_id={self.career_path_id}, "
            f"step_number={self.step_number}, step_name='{self.step_name}')>"
        )
