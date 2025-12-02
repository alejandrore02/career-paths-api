"""AI Career Path client."""

from datetime import datetime
from typing import Any, Dict, Union
from uuid import UUID, uuid4

import httpx
import asyncio
from app.core.config import get_settings
from app.core.errors import AIServiceError
from app.core.logging import get_logger
from app.integrations.base_ai_client import BaseAIClient
from app.integrations.circuit_breaker import with_circuit_breaker
from app.integrations.retry import with_retry

settings = get_settings()
logger = get_logger(__name__)


class AICareerClient(BaseAIClient):
    """Client for AI Career Path service."""

    def __init__(self) -> None:
        """Initialize AI Career client."""
        super().__init__(
            base_url=settings.ai_career_service_url,
            api_key=getattr(settings, "ai_career_api_key", None),
            timeout=settings.ai_service_timeout,
        )

    async def generate_career_paths(
        self,
        skills_data: Dict[str, Any],
        user_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate career path recommendations.
        
        Automatically uses dummy responses if USE_AI_DUMMY_MODE=True in settings.

        Args:
            skills_data: User skills assessment data
            user_profile: User profile information (user_id, current_position, etc.)

        Returns:
            Career paths response with generated_paths array

        Raises:
            AIServiceError: If production service fails
        """
        if settings.use_ai_dummy_mode:
            
            await asyncio.sleep(0.5)
            user_id = user_profile.get("user_id", "unknown")
            current_position = user_profile.get("current_position", "Gerente de Sucursal")
            logger.info("Using dummy AI Career paths for user %s", user_id)
            return self._get_dummy_career_paths(user_id, current_position=current_position)

        return await self._call_production_api(skills_data, user_profile)

    @with_circuit_breaker(
        failure_threshold=settings.ai_circuit_breaker_threshold,
        timeout=settings.ai_circuit_breaker_timeout,
        name="ai_career_service",
    )
    @with_retry(
        max_retries=settings.ai_service_max_retries,
        initial_delay=settings.ai_service_retry_delay,
        backoff_factor=2.0,  # Fixed value
    )
    async def _call_production_api(
        self,
        skills_data: Dict[str, Any],
        user_profile: Dict[str, Any],
    ) -> Dict[str, Any]:

        try:
            response = await self.client.post(
                "/",
                json={
                    "skills": skills_data,
                    "profile": user_profile,
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("AI Career service returned error: %s", e)
            raise AIServiceError(
                "AI Career service failed",
                details={"status_code": status, "message": str(e)},
            )
        except httpx.RequestError as e:
            logger.error("AI Career service request failed: %s", e)
            raise AIServiceError(
                "Failed to connect to AI Career service",
                details={"error": str(e)},
            )

    def _get_dummy_career_paths(
        self,
        user_id: Union[UUID, str],
        current_position: str = "Gerente de Sucursal",
    ) -> Dict[str, Any]:
        """
        Generate dummy career paths for testing/development.
        """
        if isinstance(user_id, UUID):
            user_id_str = str(user_id)
        else:
            user_id_str = user_id

        main_career_path_id = str(uuid4())

        return {
            "career_path_id": main_career_path_id,
            "user_id": user_id_str,
            "generated_paths": [
                {
                    "path_id": str(uuid4()),
                    "path_name": "Ruta de Liderazgo Regional",
                    "recommended": True,
                    "total_duration_months": 24,
                    # IMPORTANTE: 0–1 (coincide con CareerPath.feasibility_score)
                    "feasibility_score": 0.85,
                    "steps": [
                        {
                            "step_number": 1,
                            "step_name": "Consolidación como Gerente de Sucursal Senior",
                            "target_role": "Gerente de Sucursal Senior",
                            "duration_months": 12,
                            "required_competencies": [
                                {
                                    "name": "Pensamiento Estratégico",
                                    "current_level": 5,
                                    "required_level": 7,
                                    "development_actions": [
                                        "Curso: Estrategia de Negocios Avanzada",
                                        "Proyecto: Plan estratégico para sucursal",
                                        "Mentoría con Gerente Regional",
                                    ],
                                }
                            ],
                        },
                        {
                            "step_number": 2,
                            "step_name": "Transición a Gerente Regional",
                            "target_role": "Gerente Regional",
                            "duration_months": 12,
                            "required_competencies": [
                                {
                                    "name": "Gestión de P&L",
                                    "current_level": 4,
                                    "required_level": 8,
                                    "development_actions": [
                                        "Certificación: Finanzas para Managers",
                                        "Shadowing: Director Financiero",
                                        "Proyecto: Análisis de rentabilidad regional",
                                    ],
                                }
                            ],
                        },
                    ],
                },
                {
                    "path_id": str(uuid4()),
                    "path_name": "Ruta de Especialización en Operaciones",
                    "recommended": False,
                    "total_duration_months": 18,
                    "feasibility_score": 0.72,
                    "steps": [
                        {
                            "step_number": 1,
                            "step_name": "Especialista Senior en Operaciones",
                            "target_role": "Especialista Senior en Operaciones",
                            "duration_months": 9,
                            "required_competencies": [
                                {
                                    "name": "Optimización de Procesos",
                                    "current_level": 5,
                                    "required_level": 8,
                                    "development_actions": [
                                        "Curso: Lean Six Sigma",
                                        "Proyecto: Mejora de procesos en sucursal",
                                    ],
                                }
                            ],
                        },
                        {
                            "step_number": 2,
                            "step_name": "Gerente de Operaciones",
                            "target_role": "Gerente de Operaciones",
                            "duration_months": 9,
                            "required_competencies": [
                                {
                                    "name": "Gestión de Proyectos",
                                    "current_level": 6,
                                    "required_level": 8,
                                    "development_actions": [
                                        "Certificación: Project Management Professional (PMP)",
                                        "Shadowing: Director de Operaciones",
                                    ],
                                }
                            ],
                        },
                    ],
                },
            ],
            "current_position": current_position,
            "timestamp": datetime.utcnow().isoformat(),
        }
