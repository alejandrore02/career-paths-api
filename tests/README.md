# Tests

Test suite: unit (no DB), integration (real DB), e2e (full workflow).

**Migraciones automáticas**: Las migraciones de Alembic se ejecutan automáticamente antes de cada ejecución de tests.

## Quick Start

```bash
# All tests (migraciones automáticas)
./scripts/run_tests.sh all

# Specific type
./scripts/run_tests.sh unit
./scripts/run_tests.sh integration  
./scripts/run_tests.sh e2e

# With coverage
./scripts/run_tests.sh coverage
```

## Structure

```text
tests/
├── conftest.py           # Mock fixtures (AI responses)
├── conftest_db.py        # Shared DB fixtures
├── unit/                 # Unit tests (no DB)
│   ├── domain/           # Business logic
│   ├── services/         # Service layer
│   └── integrations/     # Circuit breaker, retry
├── integration/         # Integration tests (real DB)
│   └── api/              # HTTP endpoints
└── e2e/                 # End-to-end workflows
    ├── test_evaluation_pipeline.py
    └── test_api_workflow.py
```

```bash
./scripts/run_tests.sh unit          # Tests unitarios (rápido, sin DB)
./scripts/run_tests.sh integration   # Tests de integración en Docker
./scripts/run_tests.sh all           # Todos los tests en Docker
./scripts/run_tests.sh coverage      # Con reporte de cobertura
./scripts/run_tests.sh watch         # Modo watch (local)
./scripts/run_tests.sh clean         # Limpiar artifacts
```

## Docs

- `.github/copilot-instructions.md` - Testing patterns
