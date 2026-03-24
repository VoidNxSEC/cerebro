#!/usr/bin/env bash
#
# Cerebro Validation Script
# Testa todos os comandos e gera relatório de sucesso
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contadores
TOTAL=0
PASSED=0
FAILED=0
SKIPPED=0

# Arquivo de log
LOG_FILE="validation_$(date +%Y%m%d_%H%M%S).log"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 CEREBRO VALIDATION TEST SUITE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Função para testar comando
test_command() {
  local name="$1"
  local cmd="$2"
  local expect_fail="${3:-false}"

  TOTAL=$((TOTAL + 1))
  echo -n "Testing: $name ... "

  # Captura stdout e stderr
  local output_file=$(mktemp)
  local error_file=$(mktemp)

  if eval "$cmd" > "$output_file" 2> "$error_file"; then
    # Comando teve sucesso
    cat "$output_file" "$error_file" >> "$LOG_FILE"

    if [ "$expect_fail" = "true" ]; then
      echo -e "${RED}UNEXPECTED SUCCESS${NC}"
      FAILED=$((FAILED + 1))
      rm -f "$output_file" "$error_file"
      return 1
    else
      echo -e "${GREEN}PASS${NC}"
      PASSED=$((PASSED + 1))
      rm -f "$output_file" "$error_file"
      return 0
    fi
  else
    # Comando falhou
    local exit_code=$?
    cat "$output_file" "$error_file" >> "$LOG_FILE"

    if [ "$expect_fail" = "true" ]; then
      echo -e "${YELLOW}EXPECTED FAIL${NC} (exit $exit_code)"
      PASSED=$((PASSED + 1))
      rm -f "$output_file" "$error_file"
      return 0
    else
      echo -e "${RED}FAIL${NC} (exit $exit_code)"

      # Mostra o erro
      if [ -s "$error_file" ]; then
        echo -e "${RED}  Error:${NC}"
        sed 's/^/    /' "$error_file" | head -5
      elif [ -s "$output_file" ]; then
        echo -e "${RED}  Output:${NC}"
        sed 's/^/    /' "$output_file" | head -5
      fi

      FAILED=$((FAILED + 1))
      rm -f "$output_file" "$error_file"
      return 1
    fi
  fi
}

# Função para skip
skip_test() {
  local name="$1"
  local reason="$2"

  TOTAL=$((TOTAL + 1))
  SKIPPED=$((SKIPPED + 1))
  echo -e "Testing: $name ... ${YELLOW}SKIP${NC} ($reason)"
}

echo "═══════════════════════════════════════════════════════════"
echo "  BASIC COMMANDS"
echo "═══════════════════════════════════════════════════════════"

test_command "cerebro --help" "python -m cerebro.cli --help"
test_command "cerebro info" "python -m cerebro.cli info"
test_command "cerebro version" "python -m cerebro.cli version"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  PYTHON IMPORTS"
echo "═══════════════════════════════════════════════════════════"

test_command "Import cerebro.core" "python -c 'from cerebro.core import rag'"
test_command "Import cerebro.modules" "python -c 'from cerebro.cli import app'"
test_command "Import typer" "python -c 'import typer'"
test_command "Import rich" "python -c 'import rich'"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  INVALID COMMANDS (should fail)"
echo "═══════════════════════════════════════════════════════════"

test_command "cerebro invalid" "python -m cerebro.cli invalid_command 2>&1 | grep -q 'Usage:'"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 RESULTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Total Tests:    $TOTAL"
echo -e "Passed:         ${GREEN}$PASSED${NC}"
echo -e "Failed:         ${RED}$FAILED${NC}"
echo -e "Skipped:        ${YELLOW}$SKIPPED${NC}"
echo ""

# Calcula taxa de sucesso
if [ $TOTAL -gt 0 ]; then
  SUCCESS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASSED / $TOTAL) * 100}")
  echo "Success Rate:   ${SUCCESS_RATE}%"
else
  echo "Success Rate:   N/A"
fi

echo ""
echo "Log saved to: $LOG_FILE"
echo ""

# Exit code baseado em falhas
if [ $FAILED -gt 0 ]; then
  echo -e "${RED}❌ VALIDATION FAILED${NC}"
  exit 1
else
  echo -e "${GREEN}✅ VALIDATION PASSED${NC}"
  exit 0
fi
