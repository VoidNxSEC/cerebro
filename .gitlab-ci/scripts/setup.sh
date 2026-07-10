#!/bin/bash
# .gitlab-ci/scripts/setup.sh
# Setup script for CI/CD environment

set -e

echo "Setting up CI/CD environment..."

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
export PATH="/root/.local/bin:$PATH"

# Install dependencies
poetry install

echo "✅ CI/CD environment setup complete"
