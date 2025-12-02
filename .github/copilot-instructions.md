# AI Agent Instructions - Talent Management API

## Project Overview

FastAPI-based talent management system for 360° evaluations, AI-powered skills assessments, and personalized career path generation. Architecture follows **layered design** with clean separation between API, services, domain logic, and persistence.

## Core Architecture Patterns

### 1. Unit of Work Pattern (Critical)

**All database operations MUST use `UnitOfWork`** - never instantiate repositories directly:

```python
# ✅ Correct
async def my_service(uow: UnitOfWork):
    user = await uow.users.get_by_id(user_id)
    await uow.session.commit()

# ❌ Wrong - Don't instantiate repositories directly
repo = UserRepository(session)
```

Access repositories via UoW properties: `uow.users`, `uow.evaluations`, `uow.skills`, `uow.career_paths`, etc. See `app/db/unit_of_work.py` for full repository list.

### 2. Service Layer Pattern

Services orchestrate business logic, coordinate repositories, and call external integrations. Located in `app/services/`:

- `EvaluationService` - 360° evaluation lifecycle
- `SkillsAssessmentService` - AI-powered skills analysis
- `CareerPathService` - AI-powered career recommendations

Services receive dependencies via FastAPI DI (see `app/services/dependencies.py`).

### 3. Domain Logic Separation

Pure business rules live in `app/domain/` with NO framework dependencies:

- `evaluation_logic.py`: Cycle completion rules, score aggregation algorithms
- Example: `is_cycle_complete_for_user()` requires 1 self + 1 manager + 2 peers + 0+ direct_reports

### 4. AI Integration with Resilience

External AI clients in `app/integrations/` use **circuit breaker + retry decorators**:

```python
@with_circuit_breaker(failure_threshold=5, timeout=60, name="ai_service")
@with_retry(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
async def call_ai_service(...):
    # Automatically handles failures, retries, circuit breaking
```

## Critical Workflows

### Running the Application

**Development (local database):**

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
cp .env.development.example .env

# Start PostgreSQL (if not running)
docker run -d --name talent-db \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=talent_management -p 5432:5432 postgres:15-alpine

# Run migrations and start
alembic upgrade head
uvicorn app.main:app --reload
```

**Docker Compose (recommended):**

```bash
cp .env.docker.example .env
docker compose up --build
# Runs migrations automatically on startup
```

### Database Migrations

```bash
# Create migration after model changes
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

**Important**: Models use SQLAlchemy 2.0 async with `Mapped[]` type hints. All models inherit from `Base` in `app/db/base.py`.

## Project-Specific Conventions

### Schema Organization

Three-layer schema pattern per entity (see `app/schemas/evaluation/evaluation.py`):

- `*Base` - Shared fields
- `*Create` - Input for creation (may include optional creator IDs)
- `*Update` - Partial update (all fields optional)
- `*Response` - Full output with `id`, timestamps, relationships (uses `ConfigDict(from_attributes=True)`)

### Error Handling

Centralized exceptions in `app/core/errors.py`:

- `NotFoundError` - 404 for missing resources
- `ValidationError` - 422 for business rule violations
- `ConflictError` - 409 for state conflicts
- `AIServiceError` - 502/503 for external service failures

All inherit from `AppError` with `message`, `code`, `status_code`, and `details` dict.

### Configuration via Pydantic Settings

All config in `app/core/config.py` using `pydantic-settings`:

- Loads from `.env` files (environment-specific)
- Validation + defaults built-in
- Access via `get_settings()` singleton
- Critical vars: `DATABASE_URL`, `SECRET_KEY`, AI service URLs, circuit breaker thresholds

### Logging

Structured logging via `app/core/logging.py`:

```python
from app.core.logging import get_logger
logger = get_logger(__name__)
logger.info("Message", extra={"user_id": str(user_id), "action": "create"})
```

## Key Business Rules

### 360° Evaluation Completion

An evaluation cycle is complete for a user when (`app/domain/evaluation_logic.py`):

- ≥1 self-evaluation (`evaluator_relationship="self"`)
- ≥1 manager evaluation (`evaluator_relationship="manager"`)
- ≥2 peer evaluations (`evaluator_relationship="peer"`)
- ≥0 direct report evaluations (configurable, default 0)

Only `status="submitted"` evaluations count.

### Competency Score Aggregation

After cycle completion, `EvaluationService._aggregate_user_skill_scores()`:

1. Groups scores by `skill_id`
2. Calculates overall average + per-relationship averages
3. Computes confidence: 0.9 if n≥5, 0.7 if n≥3, 0.5 if n≥1
4. Stores in `user_skill_scores` with `source="360_aggregated"`
5. Raw stats saved as JSONB in `raw_stats` column

### AI Service Flows

1. **Skills Assessment**: After evaluation completion → `AISkillsClient.assess_skills()` → creates `SkillsAssessment` with items (strengths, opportunities, hidden talents, role readiness)
2. **Career Paths**: Based on skills + target role → `AICareerClient.generate_career_path()` → creates `CareerPath` with steps and development actions

## API Documentation

- **Swagger UI**: http://localhost:8000/docs (auto-generated, disable in production)
- **ReDoc**: http://localhost:8000/redoc
- **Health**: `GET /health`, `GET /ready` (checks DB connectivity)

## Development Tools

**Code Quality:**

```bash
black app/ tests/           # Format (line-length=100)
ruff check app/ tests/      # Lint
mypy app/                   # Type check
pytest --cov=app            # Tests with coverage
```

**Validation Script:**

```bash
python scripts/validate_config.py  # Validates .env configuration
```

## Common Gotchas

1. **Async/await everywhere** - SQLAlchemy uses asyncpg, all DB calls are async
2. **UUIDs are native** - Use `PG_UUID(as_uuid=True)` in models, receives/returns Python `UUID` objects
3. **Relationships are lazy** - Use `selectinload()` or `joinedload()` to eager load
4. **Transactions are manual** - Call `await uow.session.commit()` explicitly in services
5. **AI calls can fail** - Circuit breaker opens after 5 failures, rejects calls for 60s
6. **Environment matters** - Different configs for development/production (see `.env.*.example`)

## Key Files Reference

- `docs/ARCHITECTURE.md` - Full architectural decisions and rationale
- `docs/SERVICES.md` - Detailed service implementations and flows
- `docs/flows.md` - Step-by-step business process flows
- `docs/schema.md` - Database schema design
- `Linea-pensamiento.md` - Original business requirements (Spanish)

## Testing Strategy

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures (db_session, uow, sample data)
├── unit/                    # 70% coverage target
│   ├── domain/              # Pure business logic tests
│   ├── services/            # Service layer with mocked dependencies
│   └── repositories/        # Repository tests with test DB
└── integration/             # 25% coverage target
    ├── api/                 # Full endpoint tests
    └── flows/               # Complete business flow tests
```

### Running Tests

**Unit Tests (rápido, sin DB):**

```bash
# Localmente
pytest tests/unit/ -v

# Con script helper
./scripts/run_tests.sh unit
```

**Todos los Tests (Docker - Recomendado):**

```bash
# Docker Compose
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# Con script helper
./scripts/run_tests.sh all

# Con cobertura
./scripts/run_tests.sh coverage

# Limpiar
docker compose -f docker-compose.test.yml down -v
```

**Tests Específicos:**

```bash
# Archivo específico
pytest tests/unit/services/test_evaluation_service.py -v

# Función específica
pytest tests/unit/domain/test_evaluation_logic.py::test_is_cycle_complete_all_requirements_met -v

# Por marcador
pytest tests/ -m unit -v          # Solo unitarios
pytest tests/ -m integration -v   # Solo integración
```

Ver `docs/DOCKER_TESTING.md` para configuración completa de Docker testing.

### Testing Patterns (AAA)

**Unit Tests** - Mock external dependencies:

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_service_method(mocker):
    # Arrange: Setup mocks
    mock_uow = MagicMock()
    mock_uow.users.get_by_id = AsyncMock(return_value=mock_user)

    # Act: Execute service logic
    result = await service.do_something()

    # Assert: Verify behavior
    assert result.status == "success"
    mock_uow.users.get_by_id.assert_called_once()
```

**Integration Tests** - Real DB, mock AI only:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_endpoint(async_client, sample_user, mocker):
    # Arrange: Mock AI services only
    mocker.patch("app.integrations.ai_skills_client.AISkillsClient.assess_skills")

    # Act: Make HTTP request
    response = await async_client.post("/api/v1/evaluations", json=payload)

    # Assert: Verify response
    assert response.status_code == 201
    assert response.json()["status"] == "submitted"
```

### Key Fixtures (from conftest.py)

- `db_session` - Test database with auto-rollback
- `uow` - UnitOfWork for tests
- `async_client` - HTTP client for API tests
- `sample_user`, `sample_cycle`, `sample_skills` - Pre-created test data
- `mock_ai_skills_response`, `mock_ai_career_response` - AI mock data

### Test Database Setup

**Docker (Recomendado):**

```bash
# Tests en Docker (incluye DB automáticamente)
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# O con script
./scripts/run_tests.sh all
```

**Local PostgreSQL (opcional):**

```bash
# Crear test database
createdb talent_test

# Tests crean/eliminan tablas automáticamente
pytest tests/
```

La variable `TEST_DATABASE_URL` en `conftest.py` se configura automáticamente:

- Local: `postgresql+asyncpg://postgres:postgres@localhost:5432/talent_test`
- Docker: `postgresql+asyncpg://postgres:postgres@postgres-test:5432/talent_test`

### Coverage Goals

- **Domain Logic**: >90% (pure functions, critical business rules)
- **Services**: >85% (orchestration, error handling)
- **Repositories**: >80% (CRUD operations)
- **Endpoints**: >75% (happy path + error cases)

## When Adding New Features

1. **Model** → `app/db/models/<domain>/` (inherit from Base, use Mapped types)
2. **Repository** → `app/db/repositories/<domain>/` (async methods, takes AsyncSession)
3. **Register in UoW** → `app/db/unit_of_work.py` (add property)
4. **Schema** → `app/schemas/<domain>/` (Base, Create, Update, Response pattern)
5. **Service** → `app/services/` (business logic, uses UoW + AI clients)
6. **Router** → `app/api/v1/` (thin layer, FastAPI dependency injection)
7. **Register router** → `app/main.py` (`app.include_router()`)
8. **Migration** → `alembic revision --autogenerate -m "Description"`
9. **Tests** → Write unit tests for service logic, integration tests for endpoints
