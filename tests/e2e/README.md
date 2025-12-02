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
