# app/integrations/ai_skills_client.py
import asyncio
from typing import Any, Dict
from uuid import UUID

import httpx

from app.core.config import get_settings
from app.core.errors import AIServiceError
from app.core.logging import get_logger
from app.integrations.base_ai_client import BaseAIClient
from app.integrations.retry import with_retry
from app.integrations.circuit_breaker import with_circuit_breaker

settings = get_settings()
logger = get_logger(__name__)


class AISkillsClient(BaseAIClient):
    """Client for AI Skills Assessment service."""

    def __init__(self) -> None:
        """Initialize AI Skills client."""
        super().__init__(
            base_url=settings.ai_skills_service_url,
            api_key=settings.ai_skills_api_key,
            timeout=settings.ai_service_timeout,
        )

    async def assess_skills(
        self,
        user_id: UUID,
        evaluation_data: Dict[str, Any],
        current_position: str,
        years_experience: int,
    ) -> Dict[str, Any]:
        """
        Automatically uses dummy responses if USE_AI_DUMMY_MODE=True in settings.
        
        Args:
            user_id: ID del colaborador
            evaluation_data: Data de evaluaciones consolidadas
            current_position: Puesto actual
            years_experience: Años de experiencia
        
        Returns:
            Dict con el assessment de habilidades generado por IA
        
        Raises:
            AIServiceError: Si el servicio falla o no es alcanzable
        """
        if settings.use_ai_dummy_mode:
            await asyncio.sleep(1.0)
            logger.info("Using dummy AI Skills assessment for user %s", user_id)
            return self._get_dummy_assessment(user_id)

        return await self._call_production_api(
            user_id=user_id,
            evaluation_data=evaluation_data,
            current_position=current_position,
            years_experience=years_experience,
        )

    @with_circuit_breaker(
        failure_threshold=settings.ai_circuit_breaker_threshold,
        timeout=settings.ai_circuit_breaker_timeout,
        name="ai_skills_service",
    )
    @with_retry(
        max_retries=settings.ai_service_max_retries,
        initial_delay=settings.ai_service_retry_delay,
        backoff_factor=2.0,  # Fixed value
    )
    async def _call_production_api(
        self,
        user_id: UUID,
        evaluation_data: Dict[str, Any],
        current_position: str,
        years_experience: int,
    ) -> Dict[str, Any]:
        """Call real AI Skills service."""
        payload = {
            "user_id": str(user_id),
            "evaluation_data": evaluation_data, ## evaluation data not defined in detail because is an integration
            "current_position": current_position,
            "years_experience": years_experience,
        }

        try:
            response = await self.client.post(
                "",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("AI Skills service returned error: %s", e)
            raise AIServiceError(
                "AI Skills service failed",
                details={"status_code": status, "message": str(e)},
            )
        except httpx.RequestError as e:
            logger.error("AI Skills service request failed: %s", e)
            raise AIServiceError(
                "Failed to connect to AI Skills service",
                details={"error": str(e)},
            )

    def _get_dummy_assessment(self, user_id: UUID) -> Dict[str, Any]:
        """Generate dummy assessment data for testing/development."""
        return {
            "assessment_id": f"assess_{user_id}",
            "user_id": str(user_id),
            "skills_profile": {
                "strengths": [
                    {
                        "skill": "Comunicación",
                        "proficiency_level": "Avanzado",
                        "score": 7.8,
                        "evidence": "Consistentemente evaluado positivamente por pares y equipo",
                    },
                ],
                "growth_areas": [
                    {
                        "skill": "Liderazgo",
                        "current_level": "Intermedio",
                        "target_level": "Avanzado",
                        "gap_score": 1.2,
                        "priority": "Alta",
                    },
                ],
                "hidden_talents": [
                    {
                        "skill": "Gestión de Conflictos",
                        "evidence": "Identificado en feedback cualitativo",
                        "potential_score": 8.5,
                    },
                ],
            },
            "readiness_for_roles": [
                {
                    "role": "Gerente Regional",
                    "readiness_percentage": 65,
                    "missing_competencies": ["Pensamiento Estratégico", "Gestión de P&L"],
                },
            ],
            "timestamp": "2025-01-15T10:30:00Z",
        }
