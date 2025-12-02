"""Career path service: build payloads, call AI client and persist results."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from app.core.errors import NotFoundError, ExternalServiceError as ServiceError, ValidationError, ConflictError
from app.core.logging import get_logger
from app.db.models import (
    CareerPath,
    CareerPathStep,
    DevelopmentAction,
    AICallsLog,
)
from app.db.unit_of_work import UnitOfWork
from app.schemas.career_path.career_path import (
    CareerPathResponse,
    CareerPathWithSteps,
    CareerPathStepResponse,
)
from app.schemas.mappers.career_path_mapper import CareerPathMapper
from app.integrations.ai_career_client import AICareerClient

logger = get_logger(__name__)


class CareerPathService:
    """Orchestrates career-path generation and management."""

    def __init__(
        self,
        uow: UnitOfWork,
        ai_career_client: AICareerClient,
    ) -> None:
        """
        Initialize career path service.
        
        Args:
            uow: Unit of Work for database operations
            ai_career_client: Client for AI Career Path service
        """
        self.uow = uow
        self.ai_career_client = ai_career_client

    async def generate_career_paths(
        self,
        user_id: UUID,
        skills_assessment_id: Optional[UUID] = None,
        career_interests: Optional[list[str]] = None,
        time_horizon_years: int = 3,
    ) -> list[CareerPathResponse]:
        """Generate AI career paths for a user and persist results.

        Raises NotFoundError when required resources are missing and
        ServiceError when the external AI call fails.
        """
        logger.info(
            f"Generating career paths for user {user_id} "
            f"(time_horizon: {time_horizon_years} years)"
        )
        
        # Verify user exists
        user = await self.uow.users.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        # Load skills assessment (specific or latest)
        if skills_assessment_id:
            # Use specific assessment if provided
            assessment = await self.uow.skills_assessments.get_by_id(
                skills_assessment_id,
                load_items=True,  # Include items for richer context
            )
            if not assessment:
                raise NotFoundError(
                    f"Skills assessment {skills_assessment_id} not found"
                )
        else:
            # Typical flow: use the latest assessment
            assessment = await self.uow.skills_assessments.get_latest_by_user_id(
                user_id=user_id,
                load_items=True,
            )
            if not assessment:
                raise NotFoundError(
                    f"No skills assessment found for user {user_id}. "
                    "Please complete 360° evaluation and skills assessment first."
                )
        
        # Determine current position from user's role
        current_position = "Unknown"
        if user.role_id:
            role = await self.uow.roles.get_by_id(user.role_id)
            if role:
                current_position = role.name
        
        # Build organization structure (available roles)
        all_roles = await self.uow.roles.get_all_active(limit=1000)  # Get all active roles
        organization_structure = [
            {
                "role_id": str(role.id),
                "role_name": role.name,
                "job_family": role.job_family,  # e.g., "Engineering", "Sales", "Management"
                "seniority_level": role.seniority_level,  # e.g., "Junior", "Senior", "Lead"
            }
            for role in all_roles
        ]
        
        # Prepare request payload for AI
        request_payload = {
            "user_id": str(user_id),
            "skills_assessment_id": str(assessment.id),  # Links to the assessment this is based on
            "current_position": current_position,  # Where the user is now
            "career_interests": career_interests or [],  # User's stated interests (optional)
            "time_horizon_years": time_horizon_years,  # Planning horizon (typically 3-5 years)
            "organization_structure": organization_structure,  # Available roles in the org
        }
        
        logger.info(
            f"Built career path payload with {len(organization_structure)} available roles"
        )
        
        # Create AI call log entry (pre-call)
        ai_log = AICallsLog(
            id=uuid4(),
            service_name="career_paths",
            user_id=user_id,
            skills_assessment_id=assessment.id,
            evaluation_cycle_id=assessment.evaluation_cycle_id,
            request_payload=request_payload,
            status="pending",  # Will update after call completes
        )
        created_log = await self.uow.ai_calls_log.create(ai_log)
        await self.uow.commit()
        
        # Call AI Career Path service
        try:
            start_time = datetime.now(timezone.utc)
            
            # Call the AI service client (handles HTTP, retries, circuit breaker)
            ai_response = await self.ai_career_client.generate_career_paths(
                skills_data={
                    "assessment_id": str(assessment.id),
                    "career_interests": career_interests or [],
                    "time_horizon_years": time_horizon_years,
                },
                user_profile={
                    "user_id": str(user_id),
                    "current_position": current_position,
                    "organization_structure": organization_structure,
                },
            )
            
            end_time = datetime.now(timezone.utc)
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.info(
                f"AI Career Path generation succeeded (latency: {latency_ms}ms)"
            )
            
        except Exception as e:
            # Handle AI service errors: update log and re-raise as ServiceError
            logger.error(f"AI Career Path generation failed: {e}")
            
            # Update AI log with error details for monitoring and debugging
            created_log.status = "error"
            created_log.error_message = str(e)
            await self.uow.ai_calls_log.update(created_log)
            await self.uow.commit()
            
            # Raise ServiceError to be handled by the API layer
            # This will result in a 502 Bad Gateway or similar error to the client
            raise ServiceError(
                f"AI Career Path service failed: {e}",
                service_name="career_paths",
            )
        
        # Persist AI response: career paths, steps and actions
        created_paths = []
        
        # Process each generated path from AI response
        # Typically the AI returns 2-4 alternative paths
        for path_data in ai_response.get("generated_paths", []):
            # Create top-level career_path record
            career_path = CareerPath(
                id=uuid4(),
                user_id=user_id,
                skills_assessment_id=assessment.id,  # Links to the assessment this is based on
                path_name=path_data.get("path_name"),  # e.g., "Regional Leadership Track"
                recommended=path_data.get("recommended", False),  # AI's top pick
                feasibility_score=path_data.get("feasibility_score"),  # Range: 0.0-1.0
                total_duration_months=path_data.get("total_duration_months"),  # e.g., 24 months
                status="proposed",  # Initial status as per flows.md: user hasn't accepted yet
            )
            
            created_path = await self.uow.career_paths.create(career_path)
            
            # Create steps for the path
            steps_data = path_data.get("steps", [])
            created_steps = []
            
            for step_data in steps_data:
                # Resolve optional role link by name
                target_role_id = None
                target_role_name = step_data.get("target_role")  # e.g., "Senior Manager"
                
                if target_role_name:
                    role = await self.uow.roles.get_by_name(target_role_name)
                    if role:
                        target_role_id = role.id
                    # Note: If role not found, we still create the step but without role link
                    # This handles cases where AI suggests roles not in our catalog
                
                # Create step record (may be created without role link)
                step = CareerPathStep(
                    id=uuid4(),
                    career_path_id=created_path.id,
                    step_number=step_data.get("step_number"),  # Sequential: 1, 2, 3...
                    target_role_id=target_role_id,  # FK to roles table (nullable)
                    description=f"Progress to {target_role_name}",
                    duration_months=step_data.get("duration_months"),  # How long this step takes
                )
                created_steps.append(step)
            
            # Bulk create steps for efficiency
            if created_steps:
                await self.uow.career_path_steps.create_bulk(created_steps)
                logger.info(
                    f"Created {len(created_steps)} steps for path {created_path.id}"
                )
            
            # Create development actions for each step
            for step, step_data in zip(created_steps, steps_data):
                actions = []
                
                # Process required_competencies and their development_actions
                # The AI identifies skills needed for each step and suggests actions
                for competency in step_data.get("required_competencies", []):
                    skill_name = competency.get("name")  # e.g., "Strategic Thinking"
                    
                    # Resolve skill_id from our skills catalog
                    skill_id = None
                    if skill_name:
                        skill = await self.uow.skills.get_by_name(skill_name)
                        if skill:
                            skill_id = skill.id
                    
                    # Create development actions for this skill
                    for action_title in competency.get("development_actions", []):
                        # Parse action type from title (simple heuristic)
                        # In production, the AI might provide structured action_type
                        action_type = "other"
                        if "Curso" in action_title or "Course" in action_title:
                            action_type = "course"
                        elif "Proyecto" in action_title or "Project" in action_title:
                            action_type = "project"
                        elif "Mentoría" in action_title or "Mentoring" in action_title:
                            action_type = "mentoring"
                        elif "Shadowing" in action_title:
                            action_type = "shadowing"
                        elif "Certificación" in action_title or "Certification" in action_title:
                            action_type = "certification"
                        
                        # Create development action record
                        action = DevelopmentAction(
                            id=uuid4(),
                            career_path_step_id=step.id,
                            skill_id=skill_id,  # Links to skill being developed
                            action_type=action_type,  # course/project/mentoring/etc.
                            title=action_title,  # e.g., "Advanced Strategy Course"
                        )
                        actions.append(action)
                
                # Bulk insert actions
                if actions:
                    await self.uow.development_actions.create_bulk(actions)
                    logger.info(
                        f"Created {len(actions)} development actions for step {step.id}"
                    )
            
            created_paths.append(created_path)
        
        # Update AI log with success and commit
        if created_paths:
            created_log.career_path_id = created_paths[0].id
        
        created_log.status = "success"
        created_log.response_payload = ai_response
        created_log.latency_ms = latency_ms
        await self.uow.ai_calls_log.update(created_log)
        
        # Commit transaction
        # All changes (paths + steps + actions + log update) are atomic
        # If anything fails, the entire operation is rolled back
        await self.uow.commit()
        
        logger.info(
            f"Successfully created {len(created_paths)} career paths for user {user_id}"
        )
        
        return [CareerPathMapper.orm_to_response(path) for path in created_paths]

    async def get_paths_for_user(
        self,
        user_id: UUID,
        status: Optional[str] = None,
    ) -> list[CareerPathResponse]:
        """
        Get career paths for a user.
        
        This implements Flow 2.1 from flows.md:
        - Retrieve all paths for user (optionally filtered by status)
        - Ordered by recommended flag and creation date
        
        Args:
            user_id: User UUID
            status: Optional status filter (proposed, accepted, in_progress, completed, discarded)
            
        Returns:
            List of career path responses
        """
        paths = await self.uow.career_paths.get_by_user_id(
            user_id=user_id,
            status=status,
        )
        
        return [CareerPathMapper.orm_to_response(path) for path in paths]

    async def get_path_detail(
        self,
        path_id: UUID,
    ) -> CareerPathWithSteps:
        """
        Get detailed career path with steps and development actions.
        
        This implements Flow 2.2 from flows.md:
        - Retrieve path with all steps
        - Each step includes development actions
        - Enrich with role information
        
        Args:
            path_id: Career path UUID
            
        Returns:
            Detailed career path with steps
            
        Raises:
            NotFoundError: If path not found
        """
        path = await self.uow.career_paths.get_by_id(
            path_id=path_id,
            load_steps=True,
        )
        
        if not path:
            raise NotFoundError(f"Career path {path_id} not found")
        
        return CareerPathWithSteps.model_validate(path)

    async def accept_path(
        self,
        path_id: UUID,
        user_id: UUID,
    ) -> CareerPathResponse:
        """
        Accept a career path and mark others as discarded.
        
        This implements Flow 2.3 from flows.md:
        - Validate path exists and belongs to user
        - Validate status is 'proposed'
        - Mark path as 'accepted'
        - Mark other proposed/accepted paths as 'discarded'
        - Atomic transaction
        
        Args:
            path_id: Career path UUID to accept
            user_id: User UUID (for validation)
            
        Returns:
            Accepted career path response
            
        Raises:
            NotFoundError: If path not found
            ValidationError: If path doesn't belong to user
            ConflictError: If path status doesn't allow acceptance
        """
        logger.info(
            f"User {user_id} accepting career path {path_id}"
        )

        path = await self.uow.career_paths.get_by_id(path_id)
        if not path:
            raise NotFoundError(f"Career path {path_id} not found")
        if path.user_id != user_id:
            raise ValidationError("Career path does not belong to user")
        if path.status != "proposed":
            raise ConflictError("Only proposed paths can be accepted")

        # Use repository method that handles the status updates atomically
        accepted_path = await self.uow.career_paths.accept_path(
            path_id=path_id,
            user_id=user_id,
        )
        
        if not accepted_path:
            raise NotFoundError(
                f"Career path {path_id} not found or doesn't belong to user {user_id}"
            )
        
        # Commit transaction
        await self.uow.commit()
        
        logger.info(
            f"Career path {path_id} accepted by user {user_id}"
        )
        
        return CareerPathMapper.orm_to_response(accepted_path)

    async def get_recommended_paths(
        self,
        user_id: UUID,
    ) -> list[CareerPathResponse]:
        """
        Get recommended career paths for a user.
        
        Retrieves paths where recommended=true and status is active
        (proposed, accepted, in_progress).
        
        Args:
            user_id: User UUID
            
        Returns:
            List of recommended career paths
        """
        paths = await self.uow.career_paths.get_recommended_by_user_id(
            user_id=user_id,
        )
        
        return [CareerPathMapper.orm_to_response(path) for path in paths]
