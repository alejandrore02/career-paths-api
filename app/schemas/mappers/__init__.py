"""Mappers package for layer transformations.

This package contains bidirectional mappers that transform between:
- ORM models (SQLAlchemy) ↔ Domain entities ↔ API schemas (Pydantic)

Mappers follow the Adapter pattern to decouple layers and enable:
- Domain logic to work with pure Python objects
- Services to orchestrate without knowing ORM details
- Easy testing of domain logic without database

Usage:
    from app.schemas.mappers.evaluation_mapper import EvaluationMapper
    from app.schemas.mappers.skill_profile_mapper import SkillProfileMapper
    from app.schemas.mappers.career_path_mapper import CareerPathMapper
    
    # ORM to Entity
    entity = EvaluationMapper.orm_to_entity(orm_instance)
    
    # Entity to API Response
    response = EvaluationMapper.entity_to_response(entity)
    
    # Direct ORM to Response (shortcut when no domain logic needed)
    response = EvaluationMapper.orm_to_response(orm_instance)
"""

from app.schemas.mappers.evaluation_mapper import EvaluationMapper
from app.schemas.mappers.skill_profile_mapper import SkillProfileMapper
from app.schemas.mappers.career_path_mapper import CareerPathMapper

__all__ = [
    "EvaluationMapper",
    "SkillProfileMapper",
    "CareerPathMapper",
]
