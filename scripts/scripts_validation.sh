#!/usr/bin/env bash
# Agentics SDLC Setup Verification Script
# Runs 34 checks to confirm local environment is production-ready.
# Usage: ./scripts/scripts_validation.sh

set -uo pipefail

PASS=0
FAIL=0
WARN=0

# Helper functions

check_pass() { echo "  [PASS] $1"; ((PASS++)); }
check_fail() { echo "  [FAIL] $1"; ((FAIL++)); }
check_warn() { echo "  [WARN] $1"; ((WARN++)); }

section() { echo ""; echo "=== $1 ==="; }

# 1. Python & Tools

section "Python & Tools"

python3 --version &>/dev/null && check_pass "python3 available" || check_fail "python3 not found"
poetry --version &>/dev/null && check_pass "poetry available" || check_fail "poetry not found"
docker --version &>/dev/null && check_pass "docker available" || check_warn "docker not found (optional for local dev)"
gcloud --version &>/dev/null && check_pass "gcloud CLI available" || check_warn "gcloud not found (optional for local dev)"
terraform --version &>/dev/null && check_pass "terraform available" || check_warn "terraform not found (optional)"

# 2. Project Files

section "Project Files"

REQUIRED_FILES=(
    "pyproject.toml"
    ".env"
    ".gitignore"
    ".pre-commit-config.yaml"
    "docker-compose.yml"
    "platform/docker/Dockerfile.api"
    "platform/sql/init.sql"
    ".github/workflows/ci-cd.yml"
)

for f in "${REQUIRED_FILES[@]}"; do
    [[ -f "$f" ]] && check_pass "$f exists" || check_fail "$f MISSING"
done

# 3. Source Modules

section "Source Modules"

REQUIRED_MODULES=(
    "src/core/__init__.py"
    "src/core/core_config.py"
    "src/core/core_logging.py"
    "src/core/core_llm.py"
    "src/core/core_utils.py"
    "src/api/__init__.py"
    "src/api/main.py"
    "src/api/api_utils.py"
    "src/api/middleware/api_middleware_auth.py"
    "src/api/middleware/api_middleware_observability.py"
    "src/api/middleware/api_middleware_ratelimit.py"
    "src/api/routers/api_routers_health.py"
    "src/api/routers/api_routers_tasks.py"
    "src/api/routers/api_routers_agents.py"
    "src/agents/__init__.py"
    "src/agents/agents_base.py"
    "src/agents/agents_manager.py"
    "src/agents/agents_architect.py"
    "src/agents/agents_engineer.py"
    "src/agents/agents_validator.py"
    "src/agents/agents_librarian.py"
    "src/agents/agents_reflector.py"
    "src/agents/agents_protocol.py"
    "src/agents/agents_utils.py"
    "src/rag/__init__.py"
    "src/rag/rag_embeddings.py"
    "src/rag/rag_vector_store.py"
    "src/rag/rag_retriever.py"
    "src/rag/rag_ingestion.py"
    "src/rag/rag_evaluator.py"
    "src/rag/rag_utils.py"
    "src/analytics/__init__.py"
    "src/analytics/analytics_bigquery_ingest.py"
    "src/analytics/analytics_utils.py"
)

for m in "${REQUIRED_MODULES[@]}"; do
    [[ -f "$m" ]] && check_pass "$m" || check_fail "$m MISSING"
done

# 4. Environment Variables

section "Environment Variables"

if [[ -f ".env" ]]; then
    source .env 2>/dev/null || true
fi

[[ -n "${GCP_PROJECT_ID:-}" ]] && check_pass "GCP_PROJECT_ID set" || check_fail "GCP_PROJECT_ID not set (required for Vertex AI)"
[[ -n "${AGENTICS_SDLC_API_KEY:-}" ]] && check_pass "AGENTICS_SDLC_API_KEY set" || check_warn "AGENTICS_SDLC_API_KEY not set (auth disabled in local dev)"

# 5. Poetry Dependencies

section "Poetry Dependencies"

if poetry check &>/dev/null; then
    check_pass "pyproject.toml valid"
else
    check_fail "pyproject.toml invalid"
fi

if PYTHONPATH=src poetry run python -c "import fastapi, langchain, langgraph, pydantic" 2>/dev/null; then
    check_pass "Core deps importable"
else
    check_fail "Core deps not importable — run: poetry install"
fi

# 6. CONFIDENCE_THRESHOLD

section "Critical Constants"

if PYTHONPATH=src poetry run python -c "from agents.agents_utils import AGENTS_MANAGER_CONFIDENCE_THRESHOLD; assert AGENTS_MANAGER_CONFIDENCE_THRESHOLD == 0.85, f'Expected 0.85, got {AGENTS_MANAGER_CONFIDENCE_THRESHOLD}'" 2>/dev/null; then
    check_pass "AGENTS_MANAGER_CONFIDENCE_THRESHOLD == 0.85"
else
    check_fail "AGENTS_MANAGER_CONFIDENCE_THRESHOLD != 0.85 or import failed"
fi

# 7. Test Suite

section "Test Suite"

REQUIRED_TESTS=(
    "tests/__init__.py"
    "tests/unit/__init__.py"
    "tests/unit/test_schemas.py"
    "tests/unit/test_agents.py"
    "tests/integration/__init__.py"
    "tests/integration/test_api.py"
    "tests/rag/__init__.py"
)

for t in "${REQUIRED_TESTS[@]}"; do
    [[ -f "$t" ]] && check_pass "$t" || check_fail "$t MISSING"
done

# Summary

echo ""
echo "=================================================="
echo " Verification Summary"
echo "  PASS: ${PASS}"
echo "  WARN: ${WARN}"
echo "  FAIL: ${FAIL}"
echo "=================================================="

if [[ $FAIL -gt 0 ]]; then
    echo " STATUS: FAILED (${FAIL} critical issues)"
    exit 1
else
    echo " STATUS: READY (${WARN} warnings)"
    exit 0
fi
