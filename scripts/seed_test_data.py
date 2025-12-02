#!/usr/bin/env python3
"""
Seed test data for manual endpoint testing.

This script populates the database with realistic test data including:
- Users with different roles (Employee, Manager, Director, VP)
- Skills across different categories
- Active evaluation cycle
- Complete 360° evaluations
- Aggregated skill scores
- AI-generated skills assessments
- AI-generated career paths

Usage:
    # Development environment
    python scripts/seed_test_data.py
    
    # Docker environment
    docker compose exec api python scripts/seed_test_data.py
    
    # With specific scenario
    python scripts/seed_test_data.py --scenario complete
    
    # Clean and reseed
    python scripts/seed_test_data.py --clean
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional
from uuid import UUID

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.base import Base
from app.db.unit_of_work import UnitOfWork
from tests.helpers.e2e_setup import create_evaluation_scenario, EvaluationScenario
from app.services.evaluation_service import EvaluationService
from app.services.skills_assessment_service import SkillsAssessmentService
from app.services.career_path_service import CareerPathService
from app.integrations.ai_skills_client import AISkillsClient
from app.integrations.ai_career_client import AICareerClient
from app.schemas.evaluation.evaluation import EvaluationCreate

logger = get_logger(__name__)
settings = get_settings()


class DataSeeder:
    """Handles database seeding for testing."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.uow = UnitOfWork(session)
        self.ai_skills_client = AISkillsClient()
        self.ai_career_client = AICareerClient()
        
        self.eval_service = EvaluationService(self.uow, self.ai_skills_client)
        self.skills_service = SkillsAssessmentService(self.uow, self.ai_skills_client)
        self.career_service = CareerPathService(self.uow, self.ai_career_client)
        
        self.scenario: Optional[EvaluationScenario] = None
    
    async def clean_data(self):
        """Clean all test data from database."""
        print("\n🧹 Cleaning existing test data...")
        
        # Order matters due to foreign key constraints
        tables = [
            "development_actions",
            "career_path_steps",
            "career_paths",
            "skills_assessment_items",
            "skills_assessments",
            "user_skill_scores",
            "evaluation_competency_scores",
            "evaluations",
            "evaluation_cycles",
            "users",
            "skills",
            "roles",
        ]
        
        for table in tables:
            await self.session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        
        await self.session.commit()
        print("   ✅ All tables cleaned")
    
    async def seed_base_scenario(self) -> EvaluationScenario:
        """Create base evaluation scenario with users, roles, skills, and cycle."""
        print("\n📊 Creating base scenario...")
        print("   ├─ Roles (Employee, Manager, Director, VP)")
        print("   ├─ Skills (Leadership, Communication, Strategic Thinking, etc.)")
        print("   ├─ Users (Evaluated user + evaluators)")
        print("   └─ Evaluation Cycle (2024-Q1)")
        
        scenario = await create_evaluation_scenario(self.uow)
        self.scenario = scenario
        
        await self.session.commit()
        
        print("\n✅ Base scenario created:")
        print(f"   • Evaluated User: {scenario.evaluated_user.full_name} ({scenario.evaluated_user.email})")
        print(f"     ID: {scenario.evaluated_user.id}")
        print(f"   • Manager: {scenario.manager_user.full_name} ({scenario.manager_user.email})")
        print(f"   • Peer 1: {scenario.peer_one.full_name} ({scenario.peer_one.email})")
        print(f"   • Peer 2: {scenario.peer_two.full_name} ({scenario.peer_two.email})")
        print(f"   • Cycle: {scenario.cycle.name} (ID: {scenario.cycle.id})")
        print(f"   • Skills: {len(scenario.skills)} skills created")
        print(f"   • Roles: Employee → Manager → Director → VP")
        
        return scenario
    
    async def seed_evaluations(self):
        """Create complete 360° evaluations."""
        if not self.scenario:
            raise ValueError("Must call seed_base_scenario first")
        
        print("\n📝 Creating 360° Evaluations...")
        
        relationships_and_evaluators = [
            ("self", self.scenario.evaluated_user.id, "Self-evaluation"),
            ("manager", self.scenario.manager_user.id, self.scenario.manager_user.full_name),
            ("peer", self.scenario.peer_one.id, self.scenario.peer_one.full_name),
            ("peer", self.scenario.peer_two.id, self.scenario.peer_two.full_name),
        ]
        
        evaluation_ids = []
        for idx, (relationship, evaluator_id, evaluator_name) in enumerate(relationships_and_evaluators, 1):
            print(f"   [{idx}/4] Creating {relationship.upper()} evaluation from {evaluator_name}...")
            
            evaluation_data = EvaluationCreate(
                user_id=self.scenario.evaluated_user.id,
                evaluation_cycle_id=self.scenario.cycle.id,
                evaluator_id=evaluator_id,
                evaluator_relationship=relationship,
                competencies=list(self.scenario.base_competencies),
            )
            
            created_eval = await self.eval_service.create_evaluation(evaluation_data)
            evaluation_ids.append(created_eval.id)
            
            print(f"         ✅ Evaluation ID: {created_eval.id}")
        
        await self.session.commit()
        
        print(f"\n✅ Created {len(evaluation_ids)} evaluations")
        print(f"   Total competency scores: {len(evaluation_ids) * len(self.scenario.base_competencies)}")
        
        return evaluation_ids
    
    async def process_evaluations(self, evaluation_ids: list[UUID]):
        """Process evaluations to trigger aggregation."""
        if not evaluation_ids:
            raise ValueError("No evaluations to process")
        
        print("\n⚙️  Processing evaluations...")
        print("   ├─ Checking cycle completeness")
        print("   ├─ Aggregating skill scores")
        print("   └─ Calculating confidence levels")
        
        result = await self.eval_service.process_evaluation(evaluation_ids[0])
        await self.session.commit()
        
        print(f"\n✅ Evaluations processed:")
        print(f"   • Cycle Complete: {result['cycle_complete']}")
        print(f"   • User ID: {result['user_id']}")
        print(f"   • Cycle ID: {result['cycle_id']}")
        
        # Load and display aggregated scores
        user_skill_scores = await self.uow.user_skill_scores.get_by_user_and_cycle(
            user_id=result['user_id'],
            cycle_id=result['cycle_id'],
        )
        
        print(f"\n📊 Aggregated {len(user_skill_scores)} skill scores:")
        print("   " + "─"*76)
        print(f"   {'Skill':<30} {'Score':<10} {'Confidence':<12} {'Source':<20}")
        print("   " + "─"*76)
        
        for score in user_skill_scores[:5]:  # Show first 5
            skill = await self.uow.skills.get_by_id(score.skill_id)
            if skill:
                print(f"   {skill.name:<30} {float(score.score):<10.2f} {score.confidence:<12.2f} {score.source:<20}")
        
        if len(user_skill_scores) > 5:
            print(f"   ... and {len(user_skill_scores) - 5} more")
        print("   " + "─"*76)
        
        return result
    
    async def generate_skills_assessment(self):
        """Generate AI skills assessment (mocked in test environment)."""
        if not self.scenario:
            raise ValueError("Must call seed_base_scenario first")
        
        print("\n🤖 Generating Skills Assessment...")
        print("   Note: Using real AI service (may fail if not configured)")
        
        try:
            assessment = await self.skills_service.generate_assessment(
                user_id=self.scenario.evaluated_user.id,
                cycle_id=self.scenario.cycle.id,
            )
            await self.session.commit()
            
            print(f"\n✅ Skills Assessment created:")
            print(f"   • Assessment ID: {assessment.id}")
            print(f"   • Status: {assessment.status}")
            
            # Load items
            items = await self.uow.skills_assessment_items.get_by_assessment_id(assessment.id)
            print(f"   • Assessment Items: {len(items)}")
            
            for item in items[:3]:  # Show first 3
                label = item.label or "No label"
                print(f"      • {item.item_type}: {label}")
            
            if len(items) > 3:
                print(f"      ... and {len(items) - 3} more")
            
            return assessment
        
        except Exception as e:
            print(f"\n⚠️  Skills Assessment failed: {e}")
            print("   This is expected if AI service is not configured")
            return None
    
    async def generate_career_paths(self, assessment_id: Optional[UUID] = None):
        """Generate AI career paths (mocked in test environment)."""
        if not self.scenario:
            raise ValueError("Must call seed_base_scenario first")
        
        print("\n🎯 Generating Career Paths...")
        print("   Note: Using real AI service (may fail if not configured)")
        
        try:
            career_paths = await self.career_service.generate_career_paths(
                user_id=self.scenario.evaluated_user.id,
                skills_assessment_id=assessment_id,
                career_interests=[self.scenario.regional_role.name],  # Next level up
                time_horizon_years=3,
            )
            await self.session.commit()
            
            print(f"\n✅ Generated {len(career_paths)} career path(s):")
            
            for path in career_paths:
                print(f"\n   • Career Path ID: {path.id}")
                print(f"     Status: {path.status}")
                
                # Load steps
                steps = await self.uow.career_path_steps.get_by_path_id(path.id, load_actions=True)
                print(f"     Steps: {len(steps)}")
                
                for step in steps[:2]:  # Show first 2 steps
                    step_name = step.step_name or f"Step {step.step_number}"
                    print(f"        {step.step_number}. {step_name} ({step.duration_months} months)")
                
                if len(steps) > 2:
                    print(f"        ... and {len(steps) - 2} more steps")
            
            return career_paths
        
        except Exception as e:
            print(f"\n⚠️  Career Path generation failed: {e}")
            print("   This is expected if AI service is not configured")
            return None


async def main(clean: bool = False, scenario: str = "complete"):
    """Main seeding function."""
    print("="*80)
    print("🌱 TALENT MANAGEMENT API - Test Data Seeder")
    print("="*80)
    print(f"\nDatabase: {settings.database_url.split('@')[-1]}")  # Hide credentials
    print(f"Scenario: {scenario}")
    print(f"Clean first: {clean}")
    
    # Create async engine
    engine = create_async_engine(
        str(settings.database_url),
        echo=False,
        pool_pre_ping=True,
    )
    
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_factory() as session:
        seeder = DataSeeder(session)
        
        try:
            # Clean if requested
            if clean:
                await seeder.clean_data()
            
            # Always create base scenario
            scenario_data = await seeder.seed_base_scenario()
            
            if scenario in ["complete", "evaluations"]:
                # Create evaluations
                eval_ids = await seeder.seed_evaluations()
                
                # Process evaluations
                await seeder.process_evaluations(eval_ids)
            
            if scenario == "complete":
                # Generate skills assessment
                assessment = await seeder.generate_skills_assessment()
                
                # Generate career paths (using regional_role as target)
                if assessment:
                    await seeder.generate_career_paths(assessment.id)
            
            print("\n" + "="*80)
            print("✅ SEEDING COMPLETED SUCCESSFULLY")
            print("="*80)
            
            print("\n📋 QUICK REFERENCE - User Credentials:")
            print(f"   Evaluated User: {scenario_data.evaluated_user.email}")
            print(f"                   ID: {scenario_data.evaluated_user.id}")
            print(f"   Manager:        {scenario_data.manager_user.email}")
            print(f"   Peer 1:         {scenario_data.peer_one.email}")
            print(f"   Peer 2:         {scenario_data.peer_two.email}")
            
            print("\n📋 QUICK REFERENCE - Evaluation Cycle:")
            print(f"   Cycle Name: {scenario_data.cycle.name}")
            print(f"   Cycle ID:   {scenario_data.cycle.id}")
            
            print("\n📋 TEST ENDPOINTS:")
            print("   # Health Check")
            print("   curl http://localhost:8000/health")
            print()
            print("   # Get User Evaluations")
            print(f"   curl http://localhost:8000/api/v1/evaluations?user_id={scenario_data.evaluated_user.id}")
            print()
            print("   # Get Cycle Evaluations")
            print(f"   curl http://localhost:8000/api/v1/evaluations?cycle_id={scenario_data.cycle.id}")
            print()
            print("   # Get Skills Assessment")
            print(f"   curl http://localhost:8000/api/v1/skills-assessments?user_id={scenario_data.evaluated_user.id}")
            print()
            print("   # Get Career Paths")
            print(f"   curl http://localhost:8000/api/v1/career-paths?user_id={scenario_data.evaluated_user.id}")
            print()
            print("   # Swagger UI")
            print("   http://localhost:8000/docs")
            print("\n" + "="*80 + "\n")
        
        except Exception as e:
            logger.exception("Seeding failed")
            print(f"\n❌ SEEDING FAILED: {e}")
            sys.exit(1)
        finally:
            await engine.dispose()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed test data for Talent Management API")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean all existing data before seeding"
    )
    parser.add_argument(
        "--scenario",
        choices=["base", "evaluations", "complete"],
        default="complete",
        help="Seeding scenario: base (users/roles/skills), evaluations (+360 evals), complete (+AI assessments)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(main(clean=args.clean, scenario=args.scenario))
