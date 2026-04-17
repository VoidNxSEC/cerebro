#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$REPO_ROOT"

if [[ -z "${IN_NIX_SHELL:-}" ]]; then
    if ! command -v nix &> /dev/null; then
        echo -e "${RED}❌ Nix is required to run this validation pipeline.${NC}"
        exit 1
    fi

    echo -e "${BLUE}🧊 Entering Cerebro dev shell...${NC}"
    exec nix develop --command bash "$SCRIPT_PATH" "$@"
fi

echo -e "${BLUE}🚀 Starting CEREBRO Validation Pipeline${NC}"
echo "========================================"

# 1. Environment Check
echo -e "\n${BLUE}🔍 Checking Environment...${NC}"
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}❌ Poetry is not available in the current dev shell.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Dev shell detected.${NC}"

# 2. Dependencies
echo -e "\n${BLUE}📦 Verifying Dependencies...${NC}"
poetry check
echo -e "${GREEN}✅ Dependencies are valid.${NC}"

# 3. Unit Tests
echo -e "\n${BLUE}🧪 Running Core Unit Tests...${NC}"
pytest tests/ -v --ignore=tests/integration
echo -e "${GREEN}✅ Tests Passed.${NC}"

# 4. Integration / CLI Tests
echo -e "\n${BLUE}🤖 Verifying CLI Commands...${NC}"

EXPECTED_VERSION="$(python - <<'PY'
import tomllib
from pathlib import Path

with Path("pyproject.toml").open("rb") as handle:
    print(tomllib.load(handle)["project"]["version"])
PY
)"

echo -n "  - cerebro info: "
if cerebro info > /dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    exit 1
fi

echo -n "  - cerebro version: "
if cerebro version | grep -q "$EXPECTED_VERSION"; then
  echo -e "${GREEN}OK${NC}"
else
  echo -e "${RED}FAILED${NC}"
    exit 1
fi

# 5. Functional Test (Analysis)
echo -e "\n${BLUE}🔬 Functional Test: Code Analysis...${NC}"
TEST_FILE="tests/debug_cli.py"
if [ ! -f "$TEST_FILE" ]; then
    echo "Creating dummy test file for analysis..."
    touch "$TEST_FILE"
fi

# Analyze the tests directory itself as a quick check
# Note: task_context has a default value, so Typer treats it as an option (--task-context)
if cerebro knowledge analyze ./tests --task-context "Pipeline Test" > /dev/null; then
    echo -e "${GREEN}✅ Analysis command executed successfully.${NC}"
else
    echo -e "${RED}❌ Analysis command failed.${NC}"
    exit 1
fi

echo -e "\n========================================"
echo -e "${GREEN}✅ PIPELINE COMPLETED SUCCESSFULLY${NC}"
echo "========================================"
