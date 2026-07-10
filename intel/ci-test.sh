#!/usr/bin/env bash
#
# CI Test Runner - Executa testes localmente simulando CI
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 CI Test Runner"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

run_test() {
  local name="$1"
  local cmd="$2"

  echo -e "${BLUE}▶${NC} Running: $name"
  if eval "$cmd"; then
    echo -e "${GREEN}✅ PASSED${NC}: $name"
    return 0
  else
    echo -e "${RED}❌ FAILED${NC}: $name"
    return 1
  fi
}

# Job 1: Import Tests
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Job: Import Tests"
echo "═══════════════════════════════════════════════════════════"

run_test "Import phantom.core.gcp" \
  "nix develop -c python -c 'from phantom.core import gcp'"

run_test "Import phantom.modules.credit_burner" \
  "nix develop -c python -c 'from phantom.modules import credit_burner'"

run_test "Import typer" \
  "nix develop -c python -c 'import typer'"

run_test "Import rich" \
  "nix develop -c python -c 'import rich'"

# Job 2: CLI Tests
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Job: CLI Tests"
echo "═══════════════════════════════════════════════════════════"

run_test "cerebro --help" \
  "nix develop -c cerebro --help"

run_test "cerebro info" \
  "nix develop -c cerebro info"

run_test "cerebro version" \
  "nix develop -c cerebro version"

run_test "cerebro ops status" \
  "nix develop -c cerebro ops status"

# Job 3: Syntax Check
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Job: Syntax Check"
echo "═══════════════════════════════════════════════════════════"

run_test "Check all Python files" \
  "nix develop -c bash -c 'find src/phantom/ -name \"*.py\" -exec python -m py_compile {} \;'"

# Job 4: Unit Tests
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Job: Unit Tests"
echo "═══════════════════════════════════════════════════════════"

run_test "Pytest suite" \
  "nix develop -c pytest tests/"

# Job 5: Full Validation
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Job: Full Validation Suite"
echo "═══════════════════════════════════════════════════════════"

run_test "Full validation suite" \
  "nix develop -c bash scripts/validate.sh"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ All CI tests completed${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
