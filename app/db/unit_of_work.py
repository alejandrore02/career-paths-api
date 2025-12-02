"""Unit of Work pattern implementation."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

# Core repositories
from app.db.repositories import (
    UserRepository,
    RoleRepository,
    SkillRepository,
    RoleSkillRequirementRepository,
)

# Evaluation repositories
from app.db.repositories import (
    EvaluationCycleRepository,
    EvaluationRepository,
    CompetencyScoreRepository,
    UserSkillScoreRepository,
)

# Skills Assessment repositories
from app.db.repositories import (
    SkillsAssessmentRepository,
    SkillsAssessmentItemRepository,
)

# Career Path repositories
from app.db.repositories import (
    CareerPathRepository,
    CareerPathStepRepository,
    DevelopmentActionRepository,
)

# Infrastructure repositories
from app.db.repositories import AICallsLogRepository


class UnitOfWork:
    """
    Unit of Work for managing database transactions.
    
    Provides centralized access to all repositories and ensures
    transactional consistency across operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize Unit of Work with database session."""
        self.session = session
        
        # Core
        self._user_repo: Optional[UserRepository] = None
        self._role_repo: Optional[RoleRepository] = None
        self._skill_repo: Optional[SkillRepository] = None
        self._role_skill_req_repo: Optional[RoleSkillRequirementRepository] = None
        
        # Evaluation
        self._eval_cycle_repo: Optional[EvaluationCycleRepository] = None
        self._evaluation_repo: Optional[EvaluationRepository] = None
        self._comp_score_repo: Optional[CompetencyScoreRepository] = None
        self._user_skill_score_repo: Optional[UserSkillScoreRepository] = None
        
        # Skills Assessment
        self._skills_assessment_repo: Optional[SkillsAssessmentRepository] = None
        self._skills_assessment_item_repo: Optional[SkillsAssessmentItemRepository] = None
        
        # Career Path
        self._career_path_repo: Optional[CareerPathRepository] = None
        self._career_path_step_repo: Optional[CareerPathStepRepository] = None
        self._development_action_repo: Optional[DevelopmentActionRepository] = None
        
        # Infrastructure
        self._ai_calls_log_repo: Optional[AICallsLogRepository] = None

    # Core repositories
    @property
    def users(self) -> UserRepository:
        """Get user repository."""
        if self._user_repo is None:
            self._user_repo = UserRepository(self.session)
        return self._user_repo

    @property
    def roles(self) -> RoleRepository:
        """Get role repository."""
        if self._role_repo is None:
            self._role_repo = RoleRepository(self.session)
        return self._role_repo

    @property
    def skills(self) -> SkillRepository:
        """Get skill repository."""
        if self._skill_repo is None:
            self._skill_repo = SkillRepository(self.session)
        return self._skill_repo

    @property
    def role_skill_requirements(self) -> RoleSkillRequirementRepository:
        """Get role skill requirement repository."""
        if self._role_skill_req_repo is None:
            self._role_skill_req_repo = RoleSkillRequirementRepository(self.session)
        return self._role_skill_req_repo

    # Evaluation repositories
    @property
    def evaluation_cycles(self) -> EvaluationCycleRepository:
        """Get evaluation cycle repository."""
        if self._eval_cycle_repo is None:
            self._eval_cycle_repo = EvaluationCycleRepository(self.session)
        return self._eval_cycle_repo

    @property
    def evaluations(self) -> EvaluationRepository:
        """Get evaluation repository."""
        if self._evaluation_repo is None:
            self._evaluation_repo = EvaluationRepository(self.session)
        return self._evaluation_repo

    @property
    def competency_scores(self) -> CompetencyScoreRepository:
        """Get competency score repository."""
        if self._comp_score_repo is None:
            self._comp_score_repo = CompetencyScoreRepository(self.session)
        return self._comp_score_repo

    @property
    def user_skill_scores(self) -> UserSkillScoreRepository:
        """Get user skill score repository."""
        if self._user_skill_score_repo is None:
            self._user_skill_score_repo = UserSkillScoreRepository(self.session)
        return self._user_skill_score_repo

    # Skills Assessment repositories
    @property
    def skills_assessments(self) -> SkillsAssessmentRepository:
        """Get skills assessment repository."""
        if self._skills_assessment_repo is None:
            self._skills_assessment_repo = SkillsAssessmentRepository(self.session)
        return self._skills_assessment_repo

    @property
    def skills_assessment_items(self) -> SkillsAssessmentItemRepository:
        """Get skills assessment item repository."""
        if self._skills_assessment_item_repo is None:
            self._skills_assessment_item_repo = SkillsAssessmentItemRepository(self.session)
        return self._skills_assessment_item_repo

    # Career Path repositories
    @property
    def career_paths(self) -> CareerPathRepository:
        """Get career path repository."""
        if self._career_path_repo is None:
            self._career_path_repo = CareerPathRepository(self.session)
        return self._career_path_repo

    @property
    def career_path_steps(self) -> CareerPathStepRepository:
        """Get career path step repository."""
        if self._career_path_step_repo is None:
            self._career_path_step_repo = CareerPathStepRepository(self.session)
        return self._career_path_step_repo

    @property
    def development_actions(self) -> DevelopmentActionRepository:
        """Get development action repository."""
        if self._development_action_repo is None:
            self._development_action_repo = DevelopmentActionRepository(self.session)
        return self._development_action_repo

    # Infrastructure repositories
    @property
    def ai_calls_log(self) -> AICallsLogRepository:
        """Get AI calls log repository."""
        if self._ai_calls_log_repo is None:
            self._ai_calls_log_repo = AICallsLogRepository(self.session)
        return self._ai_calls_log_repo

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self.session.rollback()

    async def __aenter__(self) -> "UnitOfWork":
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        if exc_type is not None:
            await self.rollback()
