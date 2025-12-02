"""
AI Calls Log repository for database operations.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    select,
    and_,
    func,
    case,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AICallsLog


class AICallsLogRepository:
    """Repository for AICallsLog model operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    # -------------------------------------------------------------------------
    # CRUD básico
    # -------------------------------------------------------------------------
    async def create(self, log: AICallsLog) -> AICallsLog:
        """Create a new AI call log entry."""
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log
    
    async def update(self, log: AICallsLog) -> AICallsLog:
        """Update existing AI call log entry."""
        # Basta con flush; el objeto ya está ligado a la sesión.
        await self.session.flush()
        await self.session.refresh(log)
        return log
    
    async def get_by_id(self, log_id: UUID) -> Optional[AICallsLog]:
        """Get AI call log by ID."""
        query = select(AICallsLog).where(AICallsLog.id == log_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    # -------------------------------------------------------------------------
    # Búsqueda por entidad relacionada
    # -------------------------------------------------------------------------
    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> list[AICallsLog]:
        """
        Get AI call logs for a specific related entity.
        
        entity_type:
            - "user"
            - "evaluation_cycle"
            - "skills_assessment"
            - "career_path"
        """
        column_map = {
            "user": AICallsLog.user_id,
            "evaluation_cycle": AICallsLog.evaluation_cycle_id,
            "skills_assessment": AICallsLog.skills_assessment_id,
            "career_path": AICallsLog.career_path_id,
        }

        if entity_type not in column_map:
            raise ValueError(f"Unsupported entity_type: {entity_type}")

        column = column_map[entity_type]

        query = (
            select(AICallsLog)
            .where(column == entity_id)
            .order_by(AICallsLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # -------------------------------------------------------------------------
    # Búsqueda por servicio y rango de fechas
    # -------------------------------------------------------------------------
    async def get_by_service(
        self,
        service_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AICallsLog]:
        """
        Get AI call logs for a specific service with optional date range.
        
        Args:
            service_name: AI service name (e.g. "skills_assessment", "career_paths")
            start_date: Optional start datetime (timezone-aware)
            end_date: Optional end datetime (timezone-aware)
            limit: Maximum number of results
            offset: Offset for pagination
        """
        query = select(AICallsLog).where(AICallsLog.service_name == service_name)

        if start_date:
            query = query.where(AICallsLog.created_at >= start_date)

        if end_date:
            query = query.where(AICallsLog.created_at <= end_date)

        query = (
            query.order_by(AICallsLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    # -------------------------------------------------------------------------
    # Llamadas fallidas
    # -------------------------------------------------------------------------
    async def get_failed_calls(
        self,
        service_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AICallsLog]:
        """
        Get failed AI call logs.
        
        Consideramos como fallidos:
          - status = 'error'
          - status = 'timeout'
        """
        query = select(AICallsLog).where(
            AICallsLog.status.in_(["error", "timeout"])
        )

        if service_name:
            query = query.where(AICallsLog.service_name == service_name)

        query = (
            query.order_by(AICallsLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    # -------------------------------------------------------------------------
    # Estadísticas agregadas por servicio
    # -------------------------------------------------------------------------
    async def get_stats_by_service(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[dict]:
        """
        Get aggregated statistics per AI service.
        
        Returns:
            List of dicts with:
                - service_name
                - total_calls
                - successful_calls
                - failed_calls
                - avg_latency_ms
        """
        # Contamos success usando un CASE sobre status
        success_case = case(
            (AICallsLog.status == "success", 1),
            else_=0,
        )

        query = select(
            AICallsLog.service_name,
            func.count(AICallsLog.id).label("total_calls"),
            func.sum(success_case).label("successful_calls"),
            func.avg(AICallsLog.latency_ms).label("avg_latency_ms"),
        ).group_by(AICallsLog.service_name)

        if start_date:
            query = query.where(AICallsLog.created_at >= start_date)

        if end_date:
            query = query.where(AICallsLog.created_at <= end_date)

        result = await self.session.execute(query)

        stats: list[dict] = []
        for row in result.all():
            total = row.total_calls or 0
            successful = row.successful_calls or 0
            failed = total - successful

            stats.append(
                {
                    "service_name": row.service_name,
                    "total_calls": total,
                    "successful_calls": successful,
                    "failed_calls": failed,
                    "avg_latency_ms": float(row.avg_latency_ms)
                    if row.avg_latency_ms is not None
                    else None,
                }
            )

        return stats
