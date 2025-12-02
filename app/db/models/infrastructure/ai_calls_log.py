"""
AICallsLog model for tracing all AI service interactions.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AICallsLog(Base):
    """
    Audit log for all AI service calls.
    
    Tracks:
    - Request/response payloads
    - Service endpoints and models used
    - Success/failure status
    - Performance metrics (latency)
    - Links to related entities
    """
    __tablename__ = "ai_calls_log"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Service Identification
    service_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )  # skills_assessment, career_paths

    # Foreign Keys (Optional - for linking)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    evaluation_cycle_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evaluation_cycles.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    skills_assessment_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills_assessments.id", ondelete="SET NULL"),   
        nullable=True,
        index=True
    )
    career_path_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("career_paths.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Request/Response Data
    request_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    response_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Status and Errors
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )  # success, error, timeout
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Model Metadata
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Performance Metrics
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<AICallsLog(id={self.id}, service_name='{self.service_name}', "
            f"status='{self.status}', latency_ms={self.latency_ms})>"
        )
