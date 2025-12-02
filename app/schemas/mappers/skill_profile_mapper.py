"""Mapper for Skill Profile aggregate (ORM ↔ Entity ↔ Schema)."""
from app.db.models.evaluation.user_skill_score import UserSkillScore as UserSkillScoreORM
from app.domain.entities.skill_profile import SkillProfile, UserSkillScore
from app.schemas.evaluation.evaluation import (
    UserSkillScoreResponse,
    UserSkillProfile as UserSkillProfileSchema,
)


class SkillProfileMapper:
    """Bidirectional mapping for skill profile entities."""
    
    @staticmethod
    def orm_to_skill_score(orm: UserSkillScoreORM) -> UserSkillScore:
        """Convert ORM to domain value object.
        
        Args:
            orm: SQLAlchemy ORM instance
            
        Returns:
            UserSkillScore: Domain value object
        """
        return UserSkillScore(
            skill_id=orm.skill_id,
            score=float(orm.score),
            confidence=float(orm.confidence) if orm.confidence else 0.0,
            source=orm.source,
            raw_stats=orm.raw_stats or {},
        )
    
    @staticmethod
    def skill_score_to_response(skill: UserSkillScore, orm: UserSkillScoreORM) -> UserSkillScoreResponse:
        """Convert domain value object to API response.
        
        Note: Requires ORM for metadata (id, timestamps) not in entity.
        
        Args:
            skill: Domain value object
            orm: Original ORM instance for metadata
            
        Returns:
            UserSkillScoreResponse: API response schema
        """
        return UserSkillScoreResponse(
            id=orm.id,
            user_id=orm.user_id,
            evaluation_cycle_id=orm.evaluation_cycle_id,
            skill_id=skill.skill_id,
            source=skill.source,
            score=skill.score,
            confidence=skill.confidence,
            raw_stats=skill.raw_stats,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
    
    @staticmethod
    def orm_to_response(orm: UserSkillScoreORM) -> UserSkillScoreResponse:
        """Direct ORM to API Response (shortcut).
        
        Args:
            orm: SQLAlchemy ORM instance
            
        Returns:
            UserSkillScoreResponse
        """
        return UserSkillScoreResponse.model_validate(orm)
    
    @staticmethod
    def orms_to_profile(orms: list[UserSkillScoreORM]) -> SkillProfile:
        """Create skill profile entity from ORM list.
        
        Args:
            orms: List of user skill score ORMs
            
        Returns:
            SkillProfile: Domain entity
        """
        if not orms:
            raise ValueError("Cannot create profile from empty skill scores list")
        
        # All ORMs should have same user_id and cycle_id
        first = orms[0]
        user_id = first.user_id
        cycle_id = first.evaluation_cycle_id
        
        skills = [SkillProfileMapper.orm_to_skill_score(orm) for orm in orms]
        
        return SkillProfile(
            user_id=user_id,
            cycle_id=cycle_id,
            skills=skills,
            created_at=first.created_at,
            updated_at=max(orm.updated_at for orm in orms) if orms else None,
        )
    
    @staticmethod
    def profile_to_schema(profile: SkillProfile, orms: list[UserSkillScoreORM]) -> UserSkillProfileSchema:
        """Convert domain entity to API schema.
        
        Args:
            profile: Domain entity
            orms: Original ORMs (for metadata)
            
        Returns:
            UserSkillProfileSchema
        """
        # Create mapping from skill_id to ORM for metadata lookup
        orm_map = {orm.skill_id: orm for orm in orms}
        
        skill_scores = [
            SkillProfileMapper.skill_score_to_response(skill, orm_map[skill.skill_id])
            for skill in profile.skills
            if skill.skill_id in orm_map
        ]
        
        return UserSkillProfileSchema(
            user_id=profile.user_id,
            evaluation_cycle_id=profile.cycle_id,
            skill_scores=skill_scores,
        )
