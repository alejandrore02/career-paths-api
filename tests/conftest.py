"""
Pytest configuration - Mock fixtures only.

Database fixtures moved to tests/integration/conftest.py and tests/e2e/conftest.py
"""
import asyncio
from typing import Generator
from uuid import uuid4
import pytest

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_ai_skills_assessment_response():
    """
    Mock AI Skills Assessment response matching the structure from AISkillsClient._get_dummy_assessment().
    
    Returns properly structured response for skills assessment with:
    - strengths, growth_areas, hidden_talents
    - readiness_for_roles
    """
    test_user_id = str(uuid4())
    return {
        "assessment_id": f"assess_{test_user_id}",
        "user_id": test_user_id,
        "skills_profile": {
            "strengths": [
                {
                    "skill": "Comunicación",
                    "proficiency_level": "Avanzado",
                    "score": 7.8,
                    "evidence": "Consistentemente evaluado positivamente por pares y equipo",
                },
                {
                    "skill": "Liderazgo",
                    "proficiency_level": "Avanzado",
                    "score": 8.2,
                    "evidence": "Excelente capacidad de liderazgo demostrada",
                },
            ],
            "growth_areas": [
                {
                    "skill": "Pensamiento Estratégico",
                    "current_level": "Intermedio",
                    "target_level": "Avanzado",
                    "gap_score": 1.5,
                    "priority": "Alta",
                },
                {
                    "skill": "Gestión de P&L",
                    "current_level": "Básico",
                    "target_level": "Avanzado",
                    "gap_score": 2.0,
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
            {
                "role": "Director de Operaciones",
                "readiness_percentage": 45,
                "missing_competencies": ["Pensamiento Estratégico", "Gestión de P&L", "Liderazgo Ejecutivo"],
            },
        ],
        "timestamp": "2025-01-15T10:30:00Z",
    }

@pytest.fixture
def mock_ai_career_path_response():
    """
    Mock AI Career Path response matching the structure from AICareerClient._get_dummy_career_paths().
    
    Returns properly structured response with:
    - generated_paths array with steps and development actions
    - feasibility scores
    - required competencies
    """
    test_user_id = str(uuid4())
    path1_id = str(uuid4())
    path2_id = str(uuid4())
    
    return {
        "career_path_id": str(uuid4()),
        "user_id": test_user_id,
        "generated_paths": [
            {
                "path_id": path1_id,
                "path_name": "Ruta de Liderazgo Regional",
                "recommended": True,
                "total_duration_months": 24,
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
                "path_id": path2_id,
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
        "current_position": "Gerente de Sucursal",
        "timestamp": "2025-01-15T10:30:00Z",
    }

def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: E2E tests")

