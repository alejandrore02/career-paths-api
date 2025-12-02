#!/bin/bash
# Test runner script for talent management API
# Provides convenient commands for running tests in different modes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_usage() {
    echo -e "${GREEN}Test Runner${NC}"
    echo ""
    echo "Usage: ./scripts/run_tests.sh [command]"
    echo ""
    echo "Commands:"
    echo "  unit         Unit tests (no DB)"
    echo "  integration  Integration tests (Docker)"
    echo "  e2e          E2E tests (Docker)"
    echo "  all          All tests (Docker)"
    echo "  coverage     All tests + coverage report"
    echo "  clean        Remove artifacts & containers"
    echo ""
    echo "Examples:"
    echo "  ./scripts/run_tests.sh all"
    echo "  ./scripts/run_tests.sh coverage"
    echo ""
    echo "Note: 'docker' command is internal, used by docker-compose only"
}

run_unit_tests() {
    echo -e "${GREEN}Running unit tests...${NC}"
    pytest tests/unit/ -v --tb=short
}

run_integration_tests() {
    echo -e "${GREEN}Integration tests (Docker)${NC}"
    PYTEST_ARGS="tests/integration/" docker compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test-runner
    EXIT_CODE=$?
    docker compose -f docker-compose.test.yml down -v
    return $EXIT_CODE
}

run_e2e_tests() {
    echo -e "${GREEN}E2E tests (Docker)${NC}"
    PYTEST_ARGS="tests/e2e/" docker compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test-runner
    EXIT_CODE=$?
    docker compose -f docker-compose.test.yml down -v
    return $EXIT_CODE
}

run_all_tests() {
    echo -e "${GREEN}All tests (Docker)${NC}"
    docker compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test-runner
    EXIT_CODE=$?
    docker compose -f docker-compose.test.yml down -v
    return $EXIT_CODE
}

run_with_coverage() {
    echo -e "${GREEN}Coverage report${NC}"
    docker compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test-runner
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}→ test-reports/coverage/index.html${NC}"
        command -v xdg-open > /dev/null && xdg-open test-reports/coverage/index.html 2>/dev/null || true
    fi
    
    docker compose -f docker-compose.test.yml down -v
    return $EXIT_CODE
}

clean_tests() {
    echo -e "${YELLOW}Cleaning${NC}"
    docker compose -f docker-compose.test.yml down -v 2>/dev/null || true
    rm -rf test-reports .pytest_cache htmlcov .coverage
    echo -e "${GREEN}✓${NC}"
}

run_in_docker() {
    echo -e "${GREEN}Running tests in Docker (with auto-migrations)${NC}"
    echo "🔄 Applying migrations to test database..."
    alembic upgrade head
    
    echo "✅ Migrations completed"
    echo "🧪 Running tests..."
    
    # Use environment variable or default
    PYTEST_ARGS="${PYTEST_ARGS:-tests/}"
    
    exec pytest $PYTEST_ARGS -v --tb=short --maxfail=5 \
      --cov=app --cov-report=html:/app/test-reports/coverage \
      --cov-report=term --junit-xml=/app/test-reports/junit.xml
}

# Main
case "${1:-}" in
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    e2e)
        run_e2e_tests
        ;;
    all)
        run_all_tests
        ;;
    coverage)
        run_with_coverage
        ;;
    docker)
        run_in_docker
        ;;
    clean)
        clean_tests
        ;;
    help|--help|-h|"")
        print_usage
        ;;
    *)
        echo -e "${RED}Unknown: $1${NC}"
        print_usage
        exit 1
        ;;
esac
