#!/bin/bash
# .gitlab-ci/scripts/test.sh
# Test script for CI/CD pipeline

set -e

echo "Running tests..."

# Run unit tests with coverage
poetry run pytest tests/ -v --ignore=tests/integration --cov=src/cerebro --cov-report=xml --cov-report=term

# Run linting
poetry run ruff check src/ tests/

# Run formatting check
poetry run ruff format --check src/ tests/

# Run CLI tests
poetry run cerebro --help
poetry run cerebro info
poetry run cerebro version
poetry run cerebro ops status

echo "✅ All tests passed"
