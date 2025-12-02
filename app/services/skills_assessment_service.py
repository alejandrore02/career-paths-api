"""
Skills Assessment service implementing flows from flows.md.

This service orchestrates:
- Construction of payload for AI Skills Assessment (Flow 1, Step 4)
- Calling AI Skills Assessment service (Flow 1, Step 5)
- Persisting assessment results and items
- Querying latest assessment (Flow 3)
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from app.core.errors import NotFoundError, ExternalServiceError as ServiceError
from app.core.logging import get_logger
from app.db.models import SkillsAssessment, SkillsAssessmentItem, AICallsLog
from app.db.unit_of_work import UnitOfWork
from app.schemas.skills_assessment.skills_assessment import (
    SkillsAssessmentResponse,
    SkillsAssessmentWithItems,
)
from app.schemas.mappers.skill_profile_mapper import SkillProfileMapper
from app.integrations.ai_skills_client import AISkillsClient

logger = get_logger(__name__)


class SkillsAssessmentService:
    """
    Service for AI Skills Assessment operations.
    
    Responsibilities:
    - Build payload from user_skill_scores
    - Call AI Skills Assessment service
    - Persist assessment results
    - Query assessment data
    """

    def __init__(
        self,
        uow: UnitOfWork,
        ai_skills_client: AISkillsClient,
    ) -> None:
        self.uow = uow
        self.ai_skills_client = ai_skills_client



    async def generate_assessment(
        self,
        user_id: UUID,
        cycle_id: UUID,
    ) -> SkillsAssessmentResponse:
        """
        Generate AI Skills Assessment for a user in a specific cycle.
        
        This implements Flow 1, Steps 4-5 from flows.md:
        - Step 4: Build payload from user_skill_scores
        - Step 5: Call AI service, handle errors, persist results
        
        Process:
        1. Retrieve user_skill_scores for user in cycle
        2. Build evaluation_data payload for AI
        3. Create AI call log entry
        4. Call AI service
        5. Persist skills_assessments and skills_assessment_items
        6. Update AI call log with result
        
        Args:
            user_id: User UUID
            cycle_id: Evaluation cycle UUID
            
        Returns:
            Created skills assessment response
            
        Raises:
            NotFoundError: If user or skill scores not found
            ServiceError: If AI service fails
        """
        logger.info(
            f"Generating skills assessment for user {user_id} in cycle {cycle_id}"
        )
        
        # Step 4.1: Verify user exists
        # We need a valid user before proceeding with assessment generation
        user = await self.uow.users.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        # Step 4.2: Retrieve user_skill_scores (aggregated from 360°)
        # These scores were created by the evaluation aggregation step
        # They contain consolidated feedback from self, peers, manager, and direct reports
        # If no scores exist, it means the 360° cycle hasn't been completed/aggregated yet
        skill_scores = await self.uow.user_skill_scores.get_by_user_and_cycle(
            user_id=user_id,
            cycle_id=cycle_id,
        )
        
        if not skill_scores:
            raise NotFoundError(
                f"No skill scores found for user {user_id} in cycle {cycle_id}. "
                "Please ensure 360° evaluations have been completed and aggregated."
            )
        
        # Convert ORM models to domain entity (SkillProfile)
        # This gives us a rich domain object with business methods
        skill_profile = SkillProfileMapper.orms_to_profile(skill_scores)
        
        # Step 4.3: Build evaluation_data payload
        # As per flows.md, the AI service expects competencies with:
        # - name: Human-readable competency name
        # - self_score: Average from self-evaluations
        # - peer_scores: List of individual peer scores (not averaged)
        # - manager_score: Average from manager evaluation(s)
        # - direct_report_scores: List of individual direct report scores
        # This rich structure allows the AI to detect patterns and discrepancies
        # Batch-resolve all skill names by IDs to avoid N queries
        competencies_payload = []
        skill_ids = [s.skill_id for s in skill_profile.skills]
        skills = await self.uow.skills.get_by_ids(skill_ids)
        id_to_skill = {s.id: s for s in skills}


        for user_skill in skill_profile.skills:
            skill = id_to_skill.get(user_skill.skill_id)
            if not skill:
                logger.warning(f"Skill {user_skill.skill_id} not found, skipping")
                continue

            raw_stats = user_skill.raw_stats
            competency_data = {
                "name": skill.name,
                "self_score": raw_stats.get("self_avg"),
                "peer_scores": raw_stats.get("peer_scores", []),
                "manager_score": raw_stats.get("manager_avg"),
                "direct_report_scores": raw_stats.get("direct_report_scores", []),
            }
            competencies_payload.append(competency_data)
        
        # Step 4.4: Get user position and experience
        # The AI uses this context to provide more relevant assessments
        # Derive current_position from user's role
        current_position = "Unknown"
        if user.role_id:
            role = await self.uow.roles.get_by_id(user.role_id)
            if role:
                current_position = role.name
        
        # Calculate years_experience (placeholder logic)
        # In production, this could be calculated from hire_date or employment history
        # years_experience helps the AI calibrate expectations for the user's career stage
        years_experience = 5  # Default
        
        # Step 4.5: Build complete request payload
        # This matches the structure expected by the AI Skills Assessment API
        # as defined in flows.md and SERVICES.md
        request_payload = {
            "user_id": str(user_id),
            "evaluation_data": {
                "competencies": competencies_payload,
            },
            "current_position": current_position,
            "years_experience": years_experience,
        }
        
        logger.info(
            f"Built assessment payload with {len(competencies_payload)} competencies"
        )
        
        # Step 5.1: Create AI call log entry (before calling service)
        # This provides full traceability of AI service calls
        # Useful for debugging, monitoring, and cost tracking
        ai_log = AICallsLog(
            service_name="skills_assessment",
            user_id=user_id,
            evaluation_cycle_id=cycle_id,
            skills_assessment_id=None,
            career_path_id=None,
            request_payload=request_payload,
            status="pending",  # estado inicial
        )
        created_log = await self.uow.ai_calls_log.create(ai_log)
        await self.uow.commit()
        
        # Step 5.2: Call AI Skills Assessment service
        # This is the external ML service that analyzes the 360° feedback
        # It returns insights on strengths, growth areas, hidden talents, and role readiness
        try:
            start_time = datetime.now(timezone.utc)
            
            # Call the AI service client (handles HTTP, retries, circuit breaker)
            ai_response = await self.ai_skills_client.assess_skills(
                user_id=user_id,
                evaluation_data=request_payload["evaluation_data"],
                current_position=current_position,
                years_experience=years_experience,
            )
            
            end_time = datetime.now(timezone.utc)
            latency_ms = int((end_time - start_time).total_seconds() * 1000) # aproximado en ms
            
            logger.info(
                f"AI Skills Assessment succeeded (latency: {latency_ms}ms)"
            )
            
        except Exception as e:
            logger.error(f"AI Skills Assessment failed: {e}")

            # Update AI log with error details
            created_log.status = "error"
            created_log.error_message = str(e)
            await self.uow.ai_calls_log.update(created_log)
            await self.uow.commit()

            raise ServiceError(
                f"AI Skills Assessment service failed: {e}",
                service_name="skills_assessment",
            )
        
        # Step 5.3b: AI call succeeded - persist results
        
        # Create skills_assessments record
        # This is the parent record that links to the evaluation cycle and user
        # It stores both the request and response for full auditability
        assessment = SkillsAssessment(
            id=uuid4(),
            user_id=user_id,
            evaluation_cycle_id=cycle_id,
            status="completed",  # Successfully generated by AI
            raw_request=request_payload,  # JSONB: full request sent to AI
            raw_response=ai_response,  # JSONB: full response from AI
            processed_at=datetime.now(timezone.utc),
        )
        
        created_assessment = await self.uow.skills_assessments.create(assessment)
        
        # Step 5.4: Create skills_assessment_items from AI response
        # The AI response contains different types of insights:
        # - strengths: Skills where the user excels
        # - growth_areas: Skills with gaps between current and target level
        # - hidden_talents: Skills with potential identified from qualitative feedback
        # - readiness_for_roles: Assessment of fit for different career paths
        # We normalize these into skills_assessment_items for consistent querying
        items: list[SkillsAssessmentItem] = []
        
        
        skills_profile = ai_response.get("skills_profile", {})

        # Strengths
        for strength in skills_profile.get("strengths", []):
            item = SkillsAssessmentItem(
                id=uuid4(),
                skills_assessment_id=created_assessment.id,
                item_type="strength",
                label=strength.get("skill"),
                score=strength.get("score"),
                evidence=strength.get("evidence"),
                metadata={
                    "proficiency_level": strength.get("proficiency_level"),
                },
            )
            items.append(item)

        # Growth areas
        for growth_area in skills_profile.get("growth_areas", []):
            item = SkillsAssessmentItem(
                id=uuid4(),
                skills_assessment_id=created_assessment.id,
                item_type="growth_area",
                label=growth_area.get("skill"),
                gap_score=growth_area.get("gap_score"),
                priority=growth_area.get("priority"),
                evidence=(
                    f"Current: {growth_area.get('current_level')}, "
                    f"Target: {growth_area.get('target_level')}"
                ),
                metadata={
                    "current_level": growth_area.get("current_level"),
                    "target_level": growth_area.get("target_level"),
                },
            )
            items.append(item)

        # Hidden talents
        for talent in skills_profile.get("hidden_talents", []):
            item = SkillsAssessmentItem(
                id=uuid4(),
                skills_assessment_id=created_assessment.id,
                item_type="hidden_talent",
                label=talent.get("skill"),
                score=talent.get("potential_score"),
                evidence=talent.get("evidence"),
            )
            items.append(item)

        # Role readiness
        for readiness in ai_response.get("readiness_for_roles", []):
            readiness_pct = readiness.get("readiness_percentage")
            normalized = (
                float(readiness_pct) / 1.0 if readiness_pct is not None else None
            )
            # O si quieres 0–1: float(readiness_pct)/100.0
            normalized = (
                float(readiness_pct) / 100.0 if readiness_pct is not None else None
            )

            item = SkillsAssessmentItem(
                id=uuid4(),
                skills_assessment_id=created_assessment.id,
                item_type="role_readiness",
                label=readiness.get("role"),
                readiness_percentage=normalized,
                evidence=None,
                metadata={
                    "missing_competencies": readiness.get(
                        "missing_competencies", []
                    ),
                },
            )
            items.append(item)

        if items:
            await self.uow.skills_assessment_items.create_bulk(items)
            logger.info(
                f"Created {len(items)} assessment items for assessment {created_assessment.id}"
            )

        # Step 5.5: Update AI call log with success
        created_log.status = "success"
        created_log.skills_assessment_id = created_assessment.id
        created_log.response_payload = ai_response
        created_log.latency_ms = latency_ms
        await self.uow.ai_calls_log.update(created_log)

        await self.uow.commit()

        logger.info(
            f"Successfully created skills assessment {created_assessment.id}"
        )

        return SkillsAssessmentResponse.model_validate(created_assessment)

    async def get_latest_assessment(
        self,
        user_id: UUID,
        include_items: bool = False,
    ) -> SkillsAssessmentResponse | SkillsAssessmentWithItems:
        """
        Get latest skills assessment for a user.
        
        - Retrieve latest completed assessment
        - Optionally include assessment items (strengths, growth areas, etc.)
        Returns:
            Latest assessment response (with or without items)
            
        Raises:
            NotFoundError: If no assessment found for user
        """
        assessment = await self.uow.skills_assessments.get_latest_by_user_id(
            user_id=user_id,
            load_items=include_items,
        )
        
        if not assessment:
            raise NotFoundError(
                f"No skills assessment found for user {user_id}"
            )
        
        if include_items:
            return SkillsAssessmentWithItems.model_validate(assessment)
        
        return SkillsAssessmentResponse.model_validate(assessment)

    async def get_assessment_by_id(
        self,
        assessment_id: UUID,
        include_items: bool = False,
    ) -> SkillsAssessmentResponse | SkillsAssessmentWithItems:
        """
        Get skills assessment by ID.
                   
        Raises:
            NotFoundError: If assessment not found
        """
        assessment = await self.uow.skills_assessments.get_by_id(
            assessment_id=assessment_id,
            load_items=include_items,
        )
        
        if not assessment:
            raise NotFoundError(f"Skills assessment {assessment_id} not found")
        
        if include_items:
            return SkillsAssessmentWithItems.model_validate(assessment)
        
        return SkillsAssessmentResponse.model_validate(assessment)
