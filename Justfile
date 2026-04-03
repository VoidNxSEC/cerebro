# Justfile - CEREBRO Automation

# ============================================================================
# TESTING
# ============================================================================

# Run all tests
test:
    pytest

# Run unit tests only
test-unit:
    pytest tests/ -v --ignore=tests/integration --cov=src/cerebro --cov-report=term

# Run integration tests only
test-integration:
    pytest tests/integration/ -v -m integration

# Run Vertex AI limit tests
test-vertex-limits:
    pytest tests/integration/test_vertex_limits.py -v -m integration

# ============================================================================
# CODE QUALITY
# ============================================================================

# Run linting with ruff
lint:
    ruff check src/ tests/

# Run linting and fix issues
lint-fix:
    ruff check --fix src/ tests/

# Format code with ruff
format:
    ruff format src/ tests/

# Type checking with mypy
type-check:
    mypy src/cerebro --ignore-missing-imports

# Run all quality checks (lint + format + tests)
quality: lint format type-check test

# Comprehensive validation of everything
validate-all: quality validate-cli-smoke
    @echo "🚀 All validations passed! System is production-ready."

# Smoke tests for each CLI command group to ensure they actually run
validate-cli-smoke:
    @echo "🔍 Running CLI smoke tests..."
    nix develop --command cerebro --help > /dev/null
    nix develop --command cerebro info
    nix develop --command cerebro ops health
    nix develop --command cerebro metrics --help > /dev/null
    nix develop --command cerebro knowledge --help > /dev/null
    nix develop --command cerebro rag --help > /dev/null
    @echo "✅ CLI smoke tests passed!"

# CI/CD SPECIFIC
# ============================================================================

# Run CI pipeline locally (simulates GitLab CI)
ci-local:
    @echo "Running local CI pipeline..."
    just validate-syntax
    just validate-imports
    just validate-all
    @echo "✅ Local CI pipeline passed!"

# Validate imports
validate-imports:
    python -c "from cerebro.core import gcp"
    python -c "from cerebro.core.rag import engine"
    python -c "import typer; import rich"

# Validate syntax
validate-syntax:
    find src/cerebro/ -name "*.py" -exec python -m py_compile {} \;

# Run CLI tests
test-cli:
    cerebro --help
    cerebro info
    cerebro version
    cerebro ops status

# ============================================================================
# DASHBOARD
# ============================================================================

# Start the Dashboard API server (kills any stale process on port 8009 first)
serve:
    @kill $(lsof -ti:8009) 2>/dev/null || true
    uvicorn cerebro.api.server:app --host 0.0.0.0 --port 8009 --reload

# Launch the web dashboard (React GUI → http://localhost:18321)
dashboard:
    cerebro dashboard

# Launch the TUI (Textual terminal UI)
tui:
    cerebro tui

# Install React dashboard dependencies
dashboard-install:
    cd dashboard && npm install

# Lint the React dashboard
dashboard-lint:
    cd dashboard && npm run lint

# Build the React dashboard
dashboard-build:
    cd dashboard && npm run build

# Type-check the React dashboard
dashboard-type-check:
    cd dashboard && npm run type-check

# ============================================================================
# DOCKER
# ============================================================================

# Build Docker image
docker-build:
    docker build -t cerebro:latest .

# Run Docker image
docker-run:
    docker run -it --rm cerebro:latest cerebro --help

# ============================================================================
# DEPLOYMENT
# ============================================================================

# Deploy to Cloud Run (requires GCP credentials)
deploy-cloud-run:
    gcloud run deploy cerebro-api \
        --source . \
        --region us-central1 \
        --platform managed \
        --allow-unauthenticated \
        --set-env-vars "GCP_PROJECT_ID=${GCP_PROJECT_ID}"

# ============================================================================
# UTILITIES
# ============================================================================

# Show Cerebro environment info
info:
    cerebro info

# Run health check
health:
    cerebro ops health

# Run code analysis on a repository
analyze path context="General Review":
    cerebro knowledge analyze {{path}} "{{context}}"

# Sync data with GCS (Staging for Ingestion)
sync local_dir="./data/analyzed":
    ./scripts/sync_data.sh {{local_dir}}

# Start RAG ingestion (Discovery Engine Import)
ingest:
    cerebro rag ingest

# Query the knowledge base
query question:
    cerebro rag query "{{question}}"

# Setup environment
install:
    poetry install --only main --no-interaction

# Run full validation pipeline
pipeline:
    ./scripts/pipeline.sh

# Clean build artifacts
clean:
    rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
