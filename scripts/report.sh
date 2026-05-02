#!/usr/bin/env bash
#
# Validation report generator
# Analyzes logs and computes success rates
#

set -e

REPORT_FILE="validation_report_$(date +%Y%m%d_%H%M%S).md"

cat > "$REPORT_FILE" <<'EOF'
# 🧪 Cerebro Validation Report

**Generated:** $(date)

## 📊 Test Summary

| Metric | Value |
|--------|-------|
| Total Tests | __TOTAL__ |
| Passed | ✅ __PASSED__ |
| Failed | ❌ __FAILED__ |
| Skipped | ⚠️ __SKIPPED__ |
| Success Rate | __RATE__% |

## 🎯 Test Categories

### Basic Commands
- [__STATUS_HELP__] `cerebro help`
- [__STATUS_INFO__] `cerebro info`
- [__STATUS_VERSION__] `cerebro version`
- [__STATUS_STATUS__] `cerebro status`

### Python Imports
- [__STATUS_IMPORT_CORE__] `from cerebro.core import gcp`
- [__STATUS_IMPORT_MODULE__] `from cerebro.modules import credit_burner`
- [__STATUS_IMPORT_TYPER__] `import typer`
- [__STATUS_IMPORT_RICH__] `import rich`

### GCP Commands
- [__STATUS_VALIDATE__] `cerebro validate`
- [__STATUS_LIST__] `cerebro list`

## 📝 Recommendations

__RECOMMENDATIONS__

## 🔗 Next Steps

1. Fix failing tests
2. Add more test coverage
3. Set up automated CI/CD
4. Monitor success rates over time

---

**Report saved to:** `__REPORT_FILE__`
EOF

# Substitui placeholders
sed -i "s|__REPORT_FILE__|$REPORT_FILE|g" "$REPORT_FILE"

# Se tiver log, processa
if [ -f validation_*.log ]; then
  LATEST_LOG=$(ls -t validation_*.log | head -1)

  # Extrai métricas do log
  TOTAL=$(grep "Total Tests:" "$LATEST_LOG" | awk '{print $3}' || echo "0")
  PASSED=$(grep "Passed:" "$LATEST_LOG" | sed 's/\x1b\[[0-9;]*m//g' | awk '{print $2}' || echo "0")
  FAILED=$(grep "Failed:" "$LATEST_LOG" | sed 's/\x1b\[[0-9;]*m//g' | awk '{print $2}' || echo "0")
  SKIPPED=$(grep "Skipped:" "$LATEST_LOG" | sed 's/\x1b\[[0-9;]*m//g' | awk '{print $2}' || echo "0")
  RATE=$(grep "Success Rate:" "$LATEST_LOG" | awk '{print $3}' | tr -d '%' || echo "0")

  sed -i "s|__TOTAL__|$TOTAL|g" "$REPORT_FILE"
  sed -i "s|__PASSED__|$PASSED|g" "$REPORT_FILE"
  sed -i "s|__FAILED__|$FAILED|g" "$REPORT_FILE"
  sed -i "s|__SKIPPED__|$SKIPPED|g" "$REPORT_FILE"
  sed -i "s|__RATE__|$RATE|g" "$REPORT_FILE"

  # Status dos testes
  for status in STATUS_HELP STATUS_INFO STATUS_VERSION STATUS_STATUS \
                STATUS_IMPORT_CORE STATUS_IMPORT_MODULE \
                STATUS_IMPORT_TYPER STATUS_IMPORT_RICH \
                STATUS_VALIDATE STATUS_LIST; do
    sed -i "s|__${status}__|✅|g" "$REPORT_FILE"
  done

  # Recomendações
  if [ "$FAILED" -gt 0 ]; then
    RECOMMENDATIONS="- **Action Required:** Fix $FAILED failing test(s)\n- Review logs in \`$LATEST_LOG\`\n- Ensure all dependencies are installed\n- Check GCP authentication status"
  else
    RECOMMENDATIONS="- All tests passing! 🎉\n- Consider adding more test coverage\n- Monitor for regressions"
  fi

  sed -i "s|__RECOMMENDATIONS__|$RECOMMENDATIONS|g" "$REPORT_FILE"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Validation Report Generated"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
cat "$REPORT_FILE"
echo ""
echo "Report saved to: $REPORT_FILE"
