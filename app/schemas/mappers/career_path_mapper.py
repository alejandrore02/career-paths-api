"""Mapper for Career Path aggregate (ORM ↔ Entity ↔ Schema)."""
from app.db.models.career_path.career_path import CareerPath as CareerPathORM
from app.db.models.career_path.career_path_step import CareerPathStep as CareerPathStepORM
from app.db.models.career_path.development_action import DevelopmentAction as DevelopmentActionORM
from app.domain.entities.career_path import (
    CareerPathEntity,
    CareerPathStep,
    DevelopmentAction,
)
from app.schemas.career_path.career_path import (
    CareerPathResponse,
    CareerPathWithSteps,
    CareerPathStepResponse,
    DevelopmentActionResponse,
)


class CareerPathMapper:
    """Bidirectional mapping for career path entities."""
    
    @staticmethod
    def development_action_orm_to_entity(orm: DevelopmentActionORM) -> DevelopmentAction:
        """Convert ORM to domain value object.
        
        Args:
            orm: SQLAlchemy ORM instance
            
        Returns:
            DevelopmentAction: Domain value object
        """
        return DevelopmentAction(
            action_type=orm.action_type,
            title=orm.title,
            skill_id=orm.skill_id,
            description=orm.description,
            provider=orm.provider,
            url=orm.url,
            estimated_effort_hours=orm.estimated_effort_hours,
        )
    
    @staticmethod
    def career_path_step_orm_to_entity(orm: CareerPathStepORM) -> CareerPathStep:
        """Convert ORM to domain entity.
        
        Args:
            orm: SQLAlchemy ORM instance
            
        Returns:
            CareerPathStep: Domain entity
        """
        return CareerPathStep(
            step_number=orm.step_number,
            target_role_id=orm.target_role_id,
            step_name=orm.step_name,
            description=orm.description,
            duration_months=orm.duration_months,
            actions=[
                CareerPathMapper.development_action_orm_to_entity(action)
                for action in (orm.development_actions or [])
            ],
        )
    
    @staticmethod
    def orm_to_entity(orm: CareerPathORM) -> CareerPathEntity:
        """Convert ORM to domain entity.
        
        Args:
            orm: SQLAlchemy ORM instance
            
        Returns:
            CareerPathEntity: Domain entity
        """
        return CareerPathEntity(
            id=orm.id,
            user_id=orm.user_id,
            skills_assessment_id=orm.skills_assessment_id,
            path_name=orm.path_name,
            recommended=orm.recommended or False,
            feasibility_score=float(orm.feasibility_score) if orm.feasibility_score else 0.0,
            total_duration_months=orm.total_duration_months,
            status=orm.status,
            steps=[
                CareerPathMapper.career_path_step_orm_to_entity(step)
                for step in (orm.steps or [])
            ],
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
    
    @staticmethod
    def orm_to_response(orm: CareerPathORM, include_steps: bool = False) -> CareerPathResponse | CareerPathWithSteps:
        """Direct ORM to API Response (using Pydantic from_attributes).
        
        Args:
            orm: SQLAlchemy ORM instance
            include_steps: Whether to include steps
            
        Returns:
            CareerPathResponse or CareerPathWithSteps
        """
        if include_steps:
            return CareerPathWithSteps.model_validate(orm)
        return CareerPathResponse.model_validate(orm)
    
    @staticmethod
    def orms_to_entities(orms: list[CareerPathORM]) -> list[CareerPathEntity]:
        """Bulk convert ORM list to Entity list.
        
        Args:
            orms: List of ORM instances
            
        Returns:
            List of domain entities
        """
        return [CareerPathMapper.orm_to_entity(orm) for orm in orms]
