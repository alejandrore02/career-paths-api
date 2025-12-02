# DB_SCHEMA.md

## Talent Management / Career Paths API – Database Schema

Este documento define el **esquema de base de datos** para el sistema de Evaluaciones 360°, Skills Assessment con IA y Senderos de Carrera.

Está pensado para:

- Implementarse en **PostgreSQL 15+**
- Usarse con **SQLAlchemy 2.0 async**
- Ser consumido por **Copilot / Cursor** para generar modelos, migraciones y repositorios.

---

## 0. Convenciones generales

- Todas las tablas principales usan:
  - `id` como **PK** (`UUID`).
  - Campos `created_at` y `updated_at` (`TIMESTAMPTZ`).
- Todas las FKs deben tener índices.
- Se prefiere nombrado en `snake_case` para tablas y columnas.
- Se usan tipos específicos de PostgreSQL:
  - `UUID` (via `sqlalchemy.dialects.postgresql.UUID`)
  - `JSONB`
  - `TIMESTAMPTZ` (`DateTime(timezone=True)`)

## 0.1 Escalas y Rangos

Esta sección centraliza las decisiones sobre escalas numéricas usadas en el dominio. La intención es mantener consistencia entre la base de datos, las validaciones en los modelos (Pydantic) y las APIs.

- **Escala de competencia / nivel / score**
  - Rango: **0.0 – 10.0**
  - Uso (ejemplos de campos en el esquema):
    - `evaluation_competency_scores.score`
    - `role_skill_requirements.required_level`
    - `skills_assessment_items.current_level`
    - `skills_assessment_items.target_level`
    - `skills_assessment_items.gap_score`
    - `skills_assessment_items.score`
    - `skills_assessment_items.potential_score`
    - `user_skill_scores.score`
  - Recomendaciones DB: usar `NUMERIC(5,2)` o `NUMERIC(6,2)` y añadir constraint CHECK, por ejemplo:
    - `CHECK (score >= 0 AND score <= 10)`
    - Para `required_level` si es entero: `SMALLINT` con `CHECK (required_level BETWEEN 0 AND 10)`
  - Recomendaciones Python / Pydantic:
    - usar `confloat(ge=0.0, le=10.0)` o `condecimal(ge=0, le=10, max_digits=5, decimal_places=2)` según necesidad de precisión.

- **Probabilidades / "confidence-like"**
  - Rango interno: **0.0 – 1.0**
  - Uso (ejemplos de campos en el esquema):
    - `career_paths.feasibility_score`
    - `user_skill_scores.confidence`
    - `skills_assessment_items.readiness_percentage` (internamente 0–1; la API puede exponerlo como 0–100 si se desea)
  - Recomendaciones DB: usar `NUMERIC(5,4)` o `NUMERIC(3,2)` y añadir constraint CHECK, por ejemplo:
    - `CHECK (feasibility_score >= 0 AND feasibility_score <= 1)`
  - Recomendaciones Python / Pydantic:
    - usar `confloat(ge=0.0, le=1.0)` o `condecimal(ge=0, le=1, max_digits=5, decimal_places=4)` para mayor precisión.

- **Idea clave**:
  - Todo lo que sea "nivel / habilidad / calificación" estará en **0–10**.
  - Todo lo que sea "probabilidad / factibilidad / confianza" estará en **0–1**.

Notas de implementación:

- En SQLAlchemy use `mapped_column(Numeric(5,2))` para scores y `mapped_column(Numeric(5,4))` para probabilidades/confianza cuando sea necesario.
- En las APIs públicas puede ser conveniente documentar y/o transformar `readiness_percentage` a 0–100; internamente almacenar siempre 0–1 para evitar ambigüedades y facilitar cálculos.

---

## 1. Módulo de Identidad y Organización

### 1.1 Tabla `users`

**Propósito:** Representar colaboradores del sistema.

**Columnas:**

- `id` – `UUID`, PK, not null.
- `email` – `VARCHAR(255)`, not null, UNIQUE.
- `full_name` – `VARCHAR(255)`, not null.
- `role_id` – `UUID`, FK → `roles.id`, nullable.
- `manager_id` – `UUID`, FK → `users.id`, nullable (relación jerárquica).
- `hire_date` – `DATE`, nullable.
- `is_active` – `BOOLEAN`, not null, default `TRUE`.

- `created_at` – `TIMESTAMPTZ`, default `NOW()`.
- `updated_at` – `TIMESTAMPTZ`, default `NOW()`.

**Índices:**

- `idx_users_email` (UNIQUE).
- `idx_users_role_id`.
- `idx_users_manager_id`.

**Notas para implementación SQLAlchemy:**

- Modelo `User` con relación:
  - `role = relationship("Role", back_populates="users")`
  - `manager = relationship("User", remote_side="User.id")`
  - `direct_reports = relationship("User", back_populates="manager")` (opcional).

---

### 1.2 Tabla `roles`

**Propósito:** Catálogo de puestos/posiciones.

**Columnas:**

- `id` – `UUID`, PK.
- `name` – `VARCHAR(150)`, not null, UNIQUE (ej. “Store Manager”).
- `job_family` – `VARCHAR(100)`, nullable (ej. “Operations”, “Sales”).
- `seniority_level` – `VARCHAR(50)`, nullable (ej. “Junior”, “Mid”, “Senior”, “Director”).
- `description` – `TEXT`, nullable.
- `is_active` – `BOOLEAN`, not null, default `TRUE`.

- `created_at` – `TIMESTAMPTZ`.
- `updated_at` – `TIMESTAMPTZ`.

**Relaciones:**

- 1:N con `users`.
- 1:N con `role_skill_requirements`.
- 1:N con `career_path_steps` (como `target_role_id`).

**Índices:**

- `idx_roles_name` (UNIQUE).

---

### 1.3 Tabla `skills` (o `competencies`)

**Propósito:** Catálogo global de competencias / habilidades.

**Columnas:**

- `id` – `UUID`, PK.
- `name` – `VARCHAR(150)`, not null, UNIQUE.
- `category` – `VARCHAR(100)`, nullable (ej. “soft”, “technical”, “leadership”).
- `description` – `TEXT`, nullable.
- `behavioral_indicators` – `TEXT`, nullable (descripcion de conductas observables).
- `is_global` – `BOOLEAN`, not null, default `TRUE`.
- `is_active` – `BOOLEAN`, not null, default `TRUE`.

- `created_at` – `TIMESTAMPTZ`.
- `updated_at` – `TIMESTAMPTZ`.

**Relaciones (lógicas):**

- 1:N con `role_skill_requirements`.
- 1:N con `evaluation_competency_scores`.
- 1:N con `user_skill_scores`.
- 1:N con `skills_assessment_items`.
- 1:N con `development_actions`.

**Índices:**

- `idx_skills_name` (UNIQUE).

---

### 1.4 Tabla `role_skill_requirements`

**Propósito:** Matriz de competencias requeridas por rol, para gap analysis y generación de rutas.

**Columnas:**

- `id` – `UUID`, PK.
- `role_id` – `UUID`, FK → `roles.id`, not null.
- `skill_id` – `UUID`, FK → `skills.id`, not null.
- `required_level` – `SMALLINT`, not null (ej. 1–5 o 1–10).
- `importance_weight` – `NUMERIC(5,2)`, not null, default `1.0` (0.0–1.0).
- `is_core` – `BOOLEAN`, not null, default `TRUE`.
- `framework_version` – `VARCHAR(50)`, nullable (para versionar el modelo de competencias).

- `created_at` – `TIMESTAMPTZ`.
- `updated_at` – `TIMESTAMPTZ`.

**Constraints:**

- UNIQUE `(role_id, skill_id, framework_version)`.
- CHECK `required_level >= 0`.
- CHECK `importance_weight BETWEEN 0 AND 1`.

- CHECK `required_level BETWEEN 0 AND 10`.

**Índices:**

- `idx_rsr_role_id`.
- `idx_rsr_skill_id`.

---

## 2. Módulo de Evaluación 360°

### 2.1 Tabla `evaluation_cycles`

**Propósito:** Agrupar evaluaciones en campañas/periodos.

**Columnas:**

- `id` – `UUID`, PK.
- `name` – `VARCHAR(200)`, not null (ej. “360 2025 Q1”).
- `description` – `TEXT`, nullable.
- `start_date` – `DATE`, not null.
- `end_date` – `DATE`, not null.
- `status` – `VARCHAR(30)`, not null (ej. `"draft"`, `"active"`, `"closed"`).
- `created_by` – `UUID`, FK → `users.id`, nullable.

- `created_at` – `TIMESTAMPTZ`.
- `updated_at` – `TIMESTAMPTZ`.

**Índices:**

- `idx_evaluation_cycles_status`.
- `idx_evaluation_cycles_dates` en `(start_date, end_date)`.

---

### 2.2 Tabla `evaluations`

**Propósito:** Una evaluación concreta (self/peer/manager/direct_report) de un evaluador a un evaluado en un ciclo.

**Columnas:**

- `id` – `UUID`, PK.
- `user_id` – `UUID`, FK → `users.id`, not null (colaborador evaluado).
- `evaluation_cycle_id` – `UUID`, FK → `evaluation_cycles.id`, not null.
- `evaluator_id` – `UUID`, FK → `users.id`, not null.
- `evaluator_relationship` – `VARCHAR(30)`, not null.  
  Valores esperados: `"self"`, `"peer"`, `"manager"`, `"direct_report"`.
- `status` – `VARCHAR(30)`, not null.  
  Ej. `"pending"`, `"submitted"`, `"cancelled"`.
- `submitted_at` – `TIMESTAMPTZ`, nullable.

- `created_at` – `TIMESTAMPTZ`.
- `updated_at` – `TIMESTAMPTZ`.

**Relaciones:**

- N:1 con `User` como `user` (evaluado).
- N:1 con `User` como `evaluator`.
- N:1 con `EvaluationCycle`.
- 1:N con `evaluation_competency_scores`.

**Índices:**

- `idx_evaluations_user_cycle` en `(user_id, evaluation_cycle_id)`.
- `idx_evaluations_evaluator_cycle` en `(evaluator_id, evaluation_cycle_id)`.

---

### 2.3 Tabla `evaluation_competency_scores`

**Propósito:** Guardar los scores por competencia dentro de cada evaluación.

**Columnas:**

- `id` – `UUID`, PK.
- `evaluation_id` – `UUID`, FK → `evaluations.id`, not null.
- `skill_id` – `UUID`, FK → `skills.id`, not null.
- `score` – `NUMERIC(5,2)`, not null.
- `comments` – `TEXT`, nullable.

- `created_at` – `TIMESTAMPTZ`.
- `updated_at` – `TIMESTAMPTZ`.

**Constraints:**

- CHECK `score BETWEEN 0 AND 10` (ajustar rango según negocio).
- UNIQUE `(evaluation_id, skill_id)` si se quiere impedir repetir una skill en la misma evaluación.

**Índices:**

- `idx_eval_comp_scores_eval` en `evaluation_id`.
- `idx_eval_comp_scores_skill` en `skill_id`.

---

### 2.4 Tabla `user_skill_scores` (derivada / agregada)

**Propósito:** Perfil consolidado de habilidades de un usuario para un ciclo (resultado de agregar todas las evaluaciones de 360°).

**Columnas:**

- `id` – `UUID`, PK.
- `user_id` – `UUID`, FK → `users.id`, not null.
- `evaluation_cycle_id` – `UUID`, FK → `evaluation_cycles.id`, not null.
- `skill_id` – `UUID`, FK → `skills.id`, not null.
- `source` – `VARCHAR(50)`, not null.  
  Ej.: `"360_aggregated"`, `"self_only"`, `"manager_only"`.
- `score` – `NUMERIC(5,2)`, not null.
  - `confidence` – `NUMERIC(5,4)`, nullable (0–1, confianza estadística). Recomendable `CHECK (confidence >= 0 AND confidence <= 1)`.
- `raw_stats` – `JSONB`, nullable (ej.: `{ "mean": 7.8, "std": 0.5, "n": 8 }`).

- `created_at` – `TIMESTAMPTZ`.
- `updated_at` – `TIMESTAMPTZ`.

**Constraints:**

- UNIQUE `(user_id, evaluation_cycle_id, skill_id, source)`.

**Índices:**

- `idx_user_skill_scores_user_cycle` en `(user_id, evaluation_cycle_id)`.
- `idx_user_skill_scores_skill` en `skill_id`.

---

## 3. Módulo de Skills Assessment (IA)

### 3.1 Tabla `skills_assessments`

**Propósito:** Resultado global de la IA sobre el perfil de habilidades de un usuario.

**Columnas:**

- `id` – `UUID`, PK.
- `user_id` – `UUID`, FK → `users.id`, not null.
- `evaluation_cycle_id` – `UUID`, FK → `evaluation_cycles.id`, nullable.
- `status` – `VARCHAR(30)`, not null.  
  Ej.: `"pending"`, `"processing"`, `"completed"`, `"failed"`.
- `summary` – `TEXT`, nullable (resumen del perfil).
- `model_name` – `VARCHAR(100)`, nullable (ej. `"gpt-4.1"`).
- `model_version` – `VARCHAR(50)`, nullable.
- `raw_request` – `JSONB`, nullable (prompt/payload).
- `raw_response` – `JSONB`, nullable (respuesta completa de la IA).
- `error_message` – `TEXT`, nullable.
- `processed_at` – `TIMESTAMPTZ`, nullable.

- `created_at` – `TIMESTAMPTZ`.
- `updated_at` – `TIMESTAMPTZ`.

**Relaciones:**

- N:1 con `User`.
- N:1 con `EvaluationCycle`.
- 1:N con `skills_assessment_items`.
- 1:N con `career_paths`.

**Índices:**

- `idx_skills_assessments_user_cycle` en `(user_id, evaluation_cycle_id)`.
- `idx_skills_assessments_status` en `status`.

---

### 3.2 Tabla `skills_assessment_items`

**Propósito:** Detalle estructurado del resultado IA (fortalezas, áreas de crecimiento, talentos ocultos, readiness de rol, etc.).

**Columnas:**

- `id` – `UUID`, PK.
- `skills_assessment_id` – `UUID`, FK → `skills_assessments.id`, not null.
- `item_type` – `VARCHAR(50)`, not null.  
  Ej.: `"strength"`, `"growth_area"`, `"hidden_talent"`, `"role_readiness"`.
- `skill_id` – `UUID`, FK → `skills.id`, nullable.
- `role_id` – `UUID`, FK → `roles.id`, nullable (para items de readiness por rol).
- `label` – `VARCHAR(150)`, nullable (texto si no apunta a catálogo).
- `current_level` – `NUMERIC(5,2)`, nullable.
- `target_level` – `NUMERIC(5,2)`, nullable.
- `gap_score` – `NUMERIC(5,2)`, nullable.
- `score` – `NUMERIC(5,2)`, nullable.
- `priority` – `VARCHAR(50)`, nullable (ej. `"Alta"`, `"Media"`, `"Baja"`).
  - `readiness_percentage` – `NUMERIC(5,4)`, nullable.
  - `evidence` – `TEXT`, nullable.
  - `metadata` – `JSONB`, nullable.

  **Rangos y constraints sugeridos para items de assessment:**

  - Campos de nivel/puntuación (`current_level`, `target_level`, `gap_score`, `score`, `potential_score`) deben seguir la escala **0.0–10.0** y llevar `CHECK` adecuados (por ejemplo `CHECK (current_level >= 0 AND current_level <= 10)`).
  - `readiness_percentage` se almacena internamente en **0.0–1.0** (`NUMERIC(5,4)` recomendado) con `CHECK (readiness_percentage >= 0 AND readiness_percentage <= 1)`. La API puede exponerlo como 0–100 si se desea.

  - `created_at` – `TIMESTAMPTZ`.
  - `updated_at` – `TIMESTAMPTZ`.

**Índices:**

- `idx_sai_assessment` en `skills_assessment_id`.
- `idx_sai_item_type` en `item_type`.
- `idx_sai_skill` en `skill_id`.
- `idx_sai_role` en `role_id`.

---

## 4. Módulo de Career Paths (IA)

### 4.1 Tabla `career_paths`

**Propósito:** Senderos de carrera generados para un usuario.

**Columnas:**

- `id` – `UUID`, PK.
- `user_id` – `UUID`, FK → `users.id`, not null.
- `skills_assessment_id` – `UUID`, FK → `skills_assessments.id`, nullable.
- `path_name` – `VARCHAR(200)`, not null.
- `recommended` – `BOOLEAN`, not null, default `FALSE`.
  - `feasibility_score` – `NUMERIC(5,4)`, nullable (0–1). Recomendable `CHECK (feasibility_score >= 0 AND feasibility_score <= 1)`.
- `total_duration_months` – `INTEGER`, nullable.
- `status` – `VARCHAR(30)`, not null, default `"proposed"`.  
  Ej.: `"proposed"`, `"accepted"`, `"in_progress"`, `"completed"`, `"discarded"`.
- `ai_metadata` – `JSONB`, nullable (información del modelo IA).
- `notes` – `TEXT`, nullable.

- `created_at` – `TIMESTAMPTZ`.
- `updated_at` – `TIMESTAMPTZ`.

**Índices:**

- `idx_career_paths_user` en `user_id`.
- `idx_career_paths_assessment` en `skills_assessment_id`.
- `idx_career_paths_status` en `status`.

---

### 4.2 Tabla `career_path_steps`

**Propósito:** pasos que conforman un sendero de carrera.

**Columnas:**

- `id` – `UUID`, PK.
- `career_path_id` – `UUID`, FK → `career_paths.id`, not null.
- `step_number` – `INTEGER`, not null.
- `target_role_id` – `UUID`, FK → `roles.id`, nullable.
- `step_name` – `VARCHAR(200)`, nullable.
- `description` – `TEXT`, nullable.
- `duration_months` – `INTEGER`, nullable.
- `metadata` – `JSONB`, nullable.

- `created_at` – `TIMESTAMPTZ`.
- `updated_at` – `TIMESTAMPTZ`.

**Constraints:**

- UNIQUE `(career_path_id, step_number)`.

**Índices:**

- `idx_cps_career_path_id` en `career_path_id`.

---

### 4.3 Tabla `development_actions`

**Propósito:** Acciones de desarrollo recomendadas para cada paso (y opcionalmente por skill).

**Columnas:**

- `id` – `UUID`, PK.
- `career_path_step_id` – `UUID`, FK → `career_path_steps.id`, not null.
- `skill_id` – `UUID`, FK → `skills.id`, nullable.
- `action_type` – `VARCHAR(50)`, not null.  
  Ej.: `"course"`, `"project"`, `"mentoring"`, `"shadowing"`, `"certification"`.
- `title` – `VARCHAR(200)`, not null.
- `description` – `TEXT`, nullable.
- `provider` – `VARCHAR(200)`, nullable.
- `url` – `VARCHAR(500)`, nullable.
- `estimated_effort_hours` – `INTEGER`, nullable.
- `metadata` – `JSONB`, nullable.

- `created_at` – `TIMESTAMPTZ`.
- `updated_at` – `TIMESTAMPTZ`.

**Índices:**

- `idx_dev_actions_step` en `career_path_step_id`.
- `idx_dev_actions_skill` en `skill_id`.

---

## 5. Infraestructura IA: `ai_calls_log`

**Propósito:** Trazar todas las llamadas a servicios de IA (skills, career paths, etc.).

**Columnas:**

- `id` – `UUID`, PK.
- `service_name` – `VARCHAR(100)`, not null (ej. `"skills_assessment"`, `"career_paths"`).
- `user_id` – `UUID`, FK → `users.id`, nullable.
- `evaluation_cycle_id` – `UUID`, FK → `evaluation_cycles.id`, nullable.
- `skills_assessment_id` – `UUID`, FK → `skills_assessments.id`, nullable.
- `career_path_id` – `UUID`, FK → `career_paths.id`, nullable.
- `request_payload` – `JSONB`, not null.
- `response_payload` – `JSONB`, nullable.
- `status` – `VARCHAR(30)`, not null (ej. `"success"`, `"error"`, `"timeout"`).
- `error_message` – `TEXT`, nullable.
- `model_name` – `VARCHAR(100)`, nullable.
- `model_version` – `VARCHAR(50)`, nullable.
- `latency_ms` – `INTEGER`, nullable.
- `created_at` – `TIMESTAMPTZ`, not null, default `NOW()`.

**Índices:**

- `idx_ai_calls_service` en `service_name`.
- `idx_ai_calls_user` en `user_id`.
- `idx_ai_calls_assessment` en `skills_assessment_id`.
- `idx_ai_calls_career_path` en `career_path_id`.

---

## 6. Notas para generación con Copilot

- Usar `Mapped[...]` y `mapped_column`.
- Declarar `__tablename__`.
- Usar `UUID(as_uuid=True)` para PK/FK.
- Timestamps con `default=func.now()` y `onupdate=func.now()`.
- Configurar `relationship` con `back_populates`.
