# E2E Tests

## Overview

E2E tests validate the **complete talent management workflow**: 360° evaluations → skills assessment → career paths. Real database, mocked AI services.

**Migraciones automáticas**: Las migraciones de Alembic se ejecutan automáticamente antes de los tests.

## Pipeline

```text
┌──────────────────────────────────────────────────────────────┐
│ STEP 1: Create 360° Evaluations                             │
│   → Self (1) + Manager (1) + Peers (2)                       │
│   → Stored in: evaluations, evaluation_competency_scores     │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 2: Process & Aggregate                                  │
│   → Detect cycle complete (business rules)                   │
│   → Aggregate scores by skill                                │
│   → Calculate overall + per-relationship averages            │
│   → Stored in: user_skill_scores                             │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 3: Generate AI Skills Assessment                        │
│   → Load aggregated user_skill_scores                        │
│   → Call AI service (mocked)                                 │
│   → Parse strengths, opportunities, hidden talents           │
│   → Stored in: skills_assessments, skills_assessment_items   │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 4: Generate AI Career Path                              │
│   → Load skills assessment + gap analysis                    │
│   → Call AI service (mocked)                                 │
│   → Parse career steps + development actions                 │
│   → Stored in: career_paths, career_path_steps, dev_actions  │
└──────────────────────────────────────────────────────────────┘
```

## What E2E Tests Do

1. **Create 360° evaluations** (self + manager + 2 peers)
2. **Process & aggregate scores** (detects cycle complete, calculates averages)
3. **Generate AI skills assessment** (mocked AI response)
4. **Generate AI career paths** (mocked AI response)
5. **Verify data persistence** (10+ database tables)

## Tests

- `test_complete_360_evaluation_to_career_path_pipeline` - Full workflow validation
- `test_complete_talent_management_workflow_via_api` - HTTP endpoint validation
- `test_incomplete_cycle_prevents_processing` - Business rules
- `test_evaluation_aggregation_calculates_correct_averages` - Score calculation accuracy

## Running Tests

```bash
# All tests (recommended)
./scripts/run_tests.sh all

# Only E2E
./scripts/run_tests.sh e2e

# With coverage
./scripts/run_tests.sh coverage
```

## Test Data

**Fixture**: `e2e_evaluation_scenario` auto-creates:

- 3 roles (Regional, Manager, Specialist)
- 4 skills (Liderazgo, Comunicación, etc.)
- 4 users (manager, evaluated, 2 peers)
- 1 active evaluation cycle
- Competency score templates

**AI Mocks**: Realistic responses from `tests/conftest.py`

## Manual Testing

```bash
# Seed test data
python scripts/seed_test_data.py --clean --scenario complete

# Test endpoints
curl http://localhost:8000/health
http://localhost:8000/docs
```

## Database Coverage

E2E tests populate **10+ tables**: users, roles, skills, evaluations, scores, assessments, career paths, steps, actions.

## Business Rules

**Cycle Complete**: ≥1 self + ≥1 manager + ≥2 peers (all `status="submitted"`)

**Score Aggregation**: Overall avg + per-relationship avg + confidence (0.5/0.7/0.9 based on sample size)

## Why Mock AI?

**Real DB + Mocked AI = Fast (<5s), reliable, free tests that focus on business logic, not AI accuracy.**

## Coverage

**Overall: 76%** (target: 70%) ✅
**58 tests** - unit, integration, e2e - **ALL PASSING** ✅

## Docs

- `docs/flows.md` - Business flows
- `docs/TESTING_GUIDE.md` - Testing strategy
- `tests/helpers/e2e_setup.py` - Test data helpers
