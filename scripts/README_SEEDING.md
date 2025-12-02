# Test Data Seeding Script

## Purpose

`seed_test_data.py` populates the database with realistic test data for **manual endpoint testing**. Use this when you want to test API endpoints directly via `curl`, Postman, or Swagger UI without running automated tests.

## Features

✅ Creates complete evaluation scenarios (users, roles, skills, cycles)  
✅ Generates 360° evaluations (self + manager + 2 peers)  
✅ Processes evaluations and aggregates scores  
✅ Calls AI services for skills assessments (real or mocked)  
✅ Generates career paths with steps and actions  
✅ Provides ready-to-use curl commands with actual IDs  
✅ Detailed console output showing what was created  

## Usage

### Development Environment

```bash
# Full scenario (recommended)
python scripts/seed_test_data.py

# Clean database first
python scripts/seed_test_data.py --clean

# Only base data (roles, skills, users, cycle)
python scripts/seed_test_data.py --scenario base

# Base + evaluations
python scripts/seed_test_data.py --scenario evaluations
```

### Docker Environment

```bash
# Full scenario
docker compose exec api python scripts/seed_test_data.py

# Clean and seed
docker compose exec api python scripts/seed_test_data.py --clean --scenario complete
```

## Scenarios

### `base` - Foundation Only
Creates:
- ✅ Roles (Regional Manager, Branch Manager, Specialist)
- ✅ Skills (Liderazgo, Comunicación, Pensamiento Estratégico, Gestión de P&L)
- ✅ Users (Manager, Evaluated User, 2 Peers)
- ✅ Evaluation Cycle (active, 30-day window)

**Use when:** You want to create evaluations manually via API

### `evaluations` - Base + 360° Evals
Creates:
- ✅ Everything from `base`
- ✅ 4 Evaluations (self, manager, 2 peers)
- ✅ Processed and aggregated scores

**Use when:** You want to test skills assessment or career path endpoints

### `complete` - Full Pipeline (Default)
Creates:
- ✅ Everything from `evaluations`
- ✅ Skills Assessment (AI-generated)
- ✅ Career Paths with steps and actions

**Use when:** You want to test all endpoints end-to-end

## Console Output

### Example: Complete Scenario

```bash
python scripts/seed_test_data.py --clean --scenario complete
```

**Output:**

```
================================================================================
🌱 TALENT MANAGEMENT API - Test Data Seeder
================================================================================

Database: localhost:5432/talent_management
Scenario: complete
Clean first: True

🧹 Cleaning existing test data...
   ✅ All tables cleaned

📊 Creating base scenario...
   ├─ Roles (Employee, Manager, Director, VP)
   ├─ Skills (Leadership, Communication, Strategic Thinking, etc.)
   ├─ Users (Evaluated user + evaluators)
   └─ Evaluation Cycle (2024-Q1)

✅ Base scenario created:
   • Evaluated User: evaluated.e2e.abc123@example.com
     ID: 78c1f6dc-6d24-4937-88e5-ca2be0cadf34
   • Manager: manager.e2e.xyz789@example.com
   • Peer 1: peer.one.e2e.def456@example.com
   • Peer 2: peer.two.e2e.ghi789@example.com
   • Cycle: E2E Cycle 2025-11-29 (ID: a3e6cad8-4a9e-4fc1-8ed7-c44bc0fcdc95)
   • Skills: 4 skills created
   • Roles: Employee → Manager → Director → VP

📝 Creating 360° Evaluations...
   [1/4] Creating SELF evaluation from Self-evaluation...
         ✅ Evaluation ID: d150d92c-425b-417b-b002-7c19a9d31cc5

   [2/4] Creating MANAGER evaluation from Manager E2E...
         ✅ Evaluation ID: d7e1a7c9-c5de-4cc7-bbb3-045cb4375529

   [3/4] Creating PEER evaluation from Peer One E2E...
         ✅ Evaluation ID: 024a4d4a-daf3-4a44-9e90-de110fb7a882

   [4/4] Creating PEER evaluation from Peer Two E2E...
         ✅ Evaluation ID: 03f47f65-5d29-4d7f-8bad-408293d3b2d2

✅ Created 4 evaluations
   Total competency scores: 16

⚙️  Processing evaluations...
   ├─ Checking cycle completeness
   ├─ Aggregating skill scores
   └─ Calculating confidence levels

✅ Evaluations processed:
   • Cycle Complete: True
   • User ID: 78c1f6dc-6d24-4937-88e5-ca2be0cadf34
   • Cycle ID: a3e6cad8-4a9e-4fc1-8ed7-c44bc0fcdc95

📊 Aggregated 4 skill scores:
   ────────────────────────────────────────────────────────────────────────────
   Skill                          Score      Confidence   Source
   ────────────────────────────────────────────────────────────────────────────
   Liderazgo                      8.50       0.70         360_aggregated
   Comunicación                   8.00       0.70         360_aggregated
   Pensamiento Estratégico        7.00       0.70         360_aggregated
   Gestión de P&L                 6.50       0.70         360_aggregated
   ... and 0 more
   ────────────────────────────────────────────────────────────────────────────

🤖 Generating Skills Assessment...
   Note: Using real AI service (may fail if not configured)

✅ Skills Assessment created:
   • Assessment ID: 8787255c-68ff-4ec9-baa1-e4c71a460b4b
   • Status: completed
   • Assessment Items: 4
      • strength: Liderazgo
      • strength: Comunicación
      • opportunity: Pensamiento Estratégico
      ... and 1 more

🎯 Generating Career Paths...
   Note: Using real AI service (may fail if not configured)

✅ Generated 1 career path(s):

   • Career Path ID: c679d73a-356e-4137-bace-63e857e1affc
     Status: proposed
     Steps: 3
        1. Fortalecer Gestión Financiera (6 months)
        2. Ampliar Visión Estratégica (6 months)
        ... and 1 more steps

================================================================================
✅ SEEDING COMPLETED SUCCESSFULLY
================================================================================

📋 QUICK REFERENCE - User Credentials:
   Evaluated User: evaluated.e2e.abc123@example.com
                   ID: 78c1f6dc-6d24-4937-88e5-ca2be0cadf34
   Manager:        manager.e2e.xyz789@example.com
   Peer 1:         peer.one.e2e.def456@example.com
   Peer 2:         peer.two.e2e.ghi789@example.com

📋 QUICK REFERENCE - Evaluation Cycle:
   Cycle Name: E2E Cycle 2025-11-29
   Cycle ID:   a3e6cad8-4a9e-4fc1-8ed7-c44bc0fcdc95

📋 TEST ENDPOINTS:
   # Health Check
   curl http://localhost:8000/health

   # Get User Evaluations
   curl http://localhost:8000/api/v1/evaluations?user_id=78c1f6dc-6d24-4937-88e5-ca2be0cadf34

   # Get Cycle Evaluations
   curl http://localhost:8000/api/v1/evaluations?cycle_id=a3e6cad8-4a9e-4fc1-8ed7-c44bc0fcdc95

   # Get Skills Assessment
   curl http://localhost:8000/api/v1/skills-assessments?user_id=78c1f6dc-6d24-4937-88e5-ca2be0cadf34

   # Get Career Paths
   curl http://localhost:8000/api/v1/career-paths?user_id=78c1f6dc-6d24-4937-88e5-ca2be0cadf34

   # Swagger UI
   http://localhost:8000/docs

================================================================================
```

## Options

```bash
python scripts/seed_test_data.py --help
```

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--clean` | flag | False | Truncate all tables before seeding |
| `--scenario` | `base`, `evaluations`, `complete` | `complete` | Amount of data to create |

## What Gets Created

### Database Tables Populated

| Table | Base | Evaluations | Complete |
|-------|------|-------------|----------|
| `roles` | 4 | 4 | 4 |
| `skills` | 4 | 4 | 4 |
| `users` | 4 | 4 | 4 |
| `evaluation_cycles` | 1 | 1 | 1 |
| `evaluations` | - | 4 | 4 |
| `evaluation_competency_scores` | - | 16 | 16 |
| `user_skill_scores` | - | 4 | 4 |
| `skills_assessments` | - | - | 1 |
| `skills_assessment_items` | - | - | 0-4 |
| `career_paths` | - | - | 1 |
| `career_path_steps` | - | - | 3 |
| `development_actions` | - | - | 0-6 |

### Test Data Characteristics

**Roles:**
- Employee (entry level)
- Manager (mid level)
- Director (senior level)
- VP (executive level)

**Skills:**
- Liderazgo (soft skill)
- Comunicación (soft skill)
- Pensamiento Estratégico (leadership)
- Gestión de P&L (finance)

**Users:**
- All have unique emails with random identifiers
- Realistic org structure (manager reports to regional)
- Hire dates ~5 years ago

**Evaluations:**
- Mix of scores (6.5-8.5 range)
- All submitted status
- Diverse comments for each competency

## Use Cases

### Testing Individual Endpoints

```bash
# Seed base data
python scripts/seed_test_data.py --clean --scenario base

# Now create an evaluation via Swagger UI
# Navigate to http://localhost:8000/docs
# Use the user IDs from console output
```

### Testing Complete Flow

```bash
# Seed everything
python scripts/seed_test_data.py --clean --scenario complete

# Now browse all data in Swagger UI
curl http://localhost:8000/api/v1/evaluations?user_id=<USER_ID>
curl http://localhost:8000/api/v1/skills-assessments?user_id=<USER_ID>
curl http://localhost:8000/api/v1/career-paths?user_id=<USER_ID>
```

### Resetting Database

```bash
# Clean all test data
python scripts/seed_test_data.py --clean --scenario base

# Or truncate everything
docker compose exec db psql -U postgres -d talent_management -c "TRUNCATE TABLE users CASCADE;"
```

## AI Service Behavior

### Development Mode (USE_AI_DUMMY_MODE=True)

Default in `.env.development`:

```python
USE_AI_DUMMY_MODE=True  # Uses mock AI responses
```

**Result:**
- ✅ Skills assessments created instantly
- ✅ Career paths created with dummy data
- ✅ No external API calls
- ✅ No cost, no latency

### Production Mode (USE_AI_DUMMY_MODE=False)

If configured with real AI service URLs:

```python
USE_AI_DUMMY_MODE=False
AI_SKILLS_SERVICE_URL=https://ai-skills.example.com
AI_CAREER_SERVICE_URL=https://ai-career.example.com
```

**Result:**
- ⚠️  Real API calls to external AI services
- ⚠️  May fail if services not available
- ⚠️  Incurs API costs
- ⚠️  Slower (network latency)

**Script output will show:**
```
⚠️  Skills Assessment failed: Connection refused
   This is expected if AI service is not configured
```

## Implementation Details

### Architecture

```python
class DataSeeder:
    def __init__(self, session: AsyncSession):
        self.uow = UnitOfWork(session)
        self.eval_service = EvaluationService(...)
        self.skills_service = SkillsAssessmentService(...)
        self.career_service = CareerPathService(...)
    
    async def seed_base_scenario(self) -> EvaluationScenario
    async def seed_evaluations(self) -> list[UUID]
    async def process_evaluations(self, eval_ids) -> dict
    async def generate_skills_assessment(self) -> SkillsAssessment
    async def generate_career_paths(self, assessment_id) -> list[CareerPath]
```

### Data Reuse

The script uses the same helpers as E2E tests:

```python
from tests.helpers.e2e_setup import (
    create_evaluation_scenario,
    EvaluationScenario
)
```

This ensures consistency between automated tests and manual testing data.

### Transaction Safety

```python
async with async_session_factory() as session:
    seeder = DataSeeder(session)
    try:
        await seeder.seed_base_scenario()
        await seeder.seed_evaluations()
        # ... more operations
    except Exception as e:
        # Automatic rollback on error
        logger.exception("Seeding failed")
        sys.exit(1)
```

## Troubleshooting

### "Connection refused" Database Error

**Cause**: Database not running  
**Fix**:
```bash
# Development
docker run -d --name talent-db -p 5432:5432 \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=talent_management postgres:15-alpine

# Docker Compose
docker compose up -d db
```

### "AI Service failed" Warning

**Status**: Expected if `USE_AI_DUMMY_MODE=False` and no real AI service configured  
**Fix**: Set `USE_AI_DUMMY_MODE=True` in `.env` for local testing

### Import Errors

**Cause**: Running from wrong directory  
**Fix**: Always run from project root:
```bash
cd /path/to/talent-management
python scripts/seed_test_data.py
```

### "Table does not exist" Error

**Cause**: Migrations not applied  
**Fix**:
```bash
alembic upgrade head
```

## Related Documentation

- `tests/e2e/README.md` - E2E testing guide
- `tests/helpers/e2e_setup.py` - Shared test data helpers
- `docs/ENV_CONFIG.md` - Environment configuration
- `docs/TESTING_GUIDE.md` - Complete testing strategy
- `docs/flows.md` - Business process flows
