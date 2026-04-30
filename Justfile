# Justfile - CEREBRO Automation

# ============================================================================
# TODO — BETA LAUNCH TRACKER
# Migrate to: cerebro todo (future command)
# ============================================================================

# Print current BETA launch progress
todo:
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "🧠 CEREBRO v1.0.0b1 — BETA LAUNCH TODO"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo ""
    @echo "PROVIDERS                                          STATUS"
    @echo "  [x] Anthropic (claude-sonnet-4-6)               done"
    @echo "  [x] Groq (llama-3.3-70b-versatile)              done"
    @echo "  [x] Gemini (gemini-1.5-flash + embeddings)      done"
    @echo "  [x] Engine aliases + factory wired              done"
    @echo "  [x] Optional Poetry groups (pyproject.toml)     done"
    @echo ""
    @echo "BETA RELEASE                                       STATUS"
    @echo "  [x] Version bump → 1.0.0b1                      done"
    @echo "  [x] flake.nix: poetry2nix + packages.default    done"
    @echo "  [x] nix/cerebro.nix nixpkgs derivation          done"
    @echo "  [x] CHANGELOG.md                                 done"
    @echo "  [ ] poetry lock --no-update                      pending"
    @echo "  [ ] nix build .#default (verify packaging)       pending"
    @echo "  [ ] git tag v1.0.0b1 + push                      pending"
    @echo ""
    @echo "TESTS                                              STATUS"
    @echo "  [x] tests/test_anthropic_provider.py             done"
    @echo "  [x] tests/test_groq_provider.py                  done"
    @echo "  [x] tests/test_gemini_provider.py                done"
    @echo "  [x] tests/test_rag_engine_new_providers.py       done"
    @echo "  [ ] Run full test suite                          pending"
    @echo ""
    @echo "NEXT: just test-unit  →  just release VERSION=1.0.0b1"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ============================================================================
# TESTING
# ============================================================================

# Run all tests
test:
    nix develop --command pytest

# Run unit tests only
test-unit:
    nix develop --command pytest tests/ -v --ignore=tests/integration --cov=src/cerebro --cov-report=term

# Run optional integration tests only
test-integration:
    nix develop .#gcp --command pytest tests/integration/ -v -m integration

# Run optional Vertex AI limit tests
test-vertex-limits:
    nix develop .#gcp --command pytest tests/integration/test_vertex_limits.py -v -m integration

# ============================================================================
# CODE QUALITY
# ============================================================================

# Run linting with ruff
lint:
    nix develop --command ruff check src/ tests/

# Run linting and fix issues
lint-fix:
    nix develop --command ruff check --fix src/ tests/

# Format code with ruff
format:
    nix develop --command ruff format src/ tests/

# Type checking with mypy
type-check:
    nix develop --command mypy src/cerebro --ignore-missing-imports

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
    nix develop --command python -c "from cerebro.core.rag import engine"
    nix develop --command python -c "from cerebro.providers.llamacpp import LlamaCppProvider"
    nix develop --command python -c "from cerebro.providers.chroma import ChromaVectorStoreProvider"
    nix develop --command python -c "import typer; import rich"

# Validate syntax
validate-syntax:
    nix develop --command python -m compileall src/cerebro

# Run CLI tests
test-cli:
    nix develop --command cerebro --help
    nix develop --command cerebro info
    nix develop --command cerebro version
    nix develop --command cerebro ops status

# ============================================================================
# DOCS
# ============================================================================

# Serve docs locally with live reload (http://localhost:8001)
docs:
    nix develop --command poetry run mkdocs serve --dev-addr 0.0.0.0:8001

# Build static docs site into site/
docs-build:
    nix develop --command poetry run mkdocs build --clean

# Build and deploy docs to Cloudflare Pages (manual path)
docs-deploy:
    nix develop --command poetry run mkdocs build --clean
    test -n "$$CLOUDFLARE_PAGES_PROJECT"
    wrangler pages deploy site/ --project-name "$$CLOUDFLARE_PAGES_PROJECT" --branch main

# ============================================================================
# DASHBOARD
# ============================================================================

# Start the Dashboard API server (kills any stale process on port 8009 first)
serve:
    @kill $(lsof -ti:8009) 2>/dev/null || true
    nix develop --command uvicorn cerebro.api.server:app --host 0.0.0.0 --port 8009 --reload

# Launch the web dashboard (React GUI → http://localhost:18321)
dashboard:
    nix develop --command cerebro dashboard

# Launch the TUI (Textual terminal UI)
tui:
    nix develop --command cerebro tui

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

# Run the deployable API container
docker-run:
    docker run -it --rm -p 8000:8000 cerebro:latest

# ============================================================================
# DEPLOYMENT
# ============================================================================

# Optional Cloud Run deploy for teams using the GCP integration path
deploy-cloud-run:
    nix develop .#gcp --command gcloud run deploy cerebro-api \
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
    nix develop --command cerebro info

# Run health check
health:
    nix develop --command cerebro ops health

# Run code analysis on a repository
analyze path context="General Review":
    nix develop --command cerebro knowledge analyze {{path}} "{{context}}"

# Optional GCS sync for the GCP integration path
sync local_dir="./data/analyzed":
    nix develop .#gcp --command ./scripts/sync_data.sh {{local_dir}}

# Start RAG ingestion against the active backend
ingest:
    nix develop --command cerebro rag ingest

# Query the knowledge base
query question:
    nix develop --command cerebro rag query "{{question}}"

# Install/update Poetry-managed dependencies inside the dev shell
install:
    nix develop --command poetry install --only main --no-interaction

# Run full validation pipeline
pipeline:
    ./scripts/pipeline.sh

# Clean build artifacts
clean:
    rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete

# ============================================================================
# RELEASE
# ============================================================================

# Bump version, commit, and tag for release.
# Usage: just release VERSION=1.0.0b1
release VERSION="1.0.0b1":
    @echo "Preparing release {{VERSION}}..."
    nix develop --command poetry lock --check
    nix develop --command poetry version {{VERSION}}
    @sed -i 's/__version__ = ".*"/__version__ = "{{VERSION}}"/' src/cerebro/__init__.py
    @echo "Version bumped to {{VERSION}}"
    git add pyproject.toml poetry.lock src/cerebro/__init__.py
    git commit -m "chore: bump version to {{VERSION}}"
    git tag -a "v{{VERSION}}" -m "Release v{{VERSION}}"
    @echo "Tagged v{{VERSION}}. Push with: git push origin main --tags"
