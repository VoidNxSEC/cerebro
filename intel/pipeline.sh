#!/usr/bin/env bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting PHANTOM Validation Pipeline${NC}"
echo "========================================"

# 1. Environment Check
echo -e "\n${BLUE}🔍 Checking Environment...${NC}"
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}❌ Poetry is not installed.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Poetry detected.${NC}"

# 2. Dependencies
echo -e "\n${BLUE}📦 Verifying Dependencies...${NC}"
poetry check
echo -e "${GREEN}✅ Dependencies are valid.${NC}"

# 3. Unit Tests
echo -e "\n${BLUE}🧪 Running Unit Tests...${NC}"
# Fix for NixOS + Python Wheels (handled by flake.nix)
# export LD_LIBRARY_PATH handled by devShell


poetry run pytest -v
echo -e "${GREEN}✅ Tests Passed.${NC}"

# 4. Integration / CLI Tests
echo -e "\n${BLUE}🤖 Verifying CLI Commands...${NC}"

echo -n "  - phantom info: "
if poetry run phantom info > /dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    exit 1
fi

echo -n "  - phantom version: "
if poetry run phantom version | grep -q "v0.1.0"; then
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
if poetry run phantom knowledge analyze ./tests --task-context "Pipeline Test" > /dev/null; then
    echo -e "${GREEN}✅ Analysis command executed successfully.${NC}"
else
    echo -e "${RED}❌ Analysis command failed.${NC}"
    exit 1
fi

echo -e "\n========================================"
echo -e "${GREEN}✅ PIPELINE COMPLETED SUCCESSFULLY${NC}"
echo "========================================"
