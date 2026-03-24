#!/usr/bin/env bash
#
# Metrics Feature Validation
# Validates MetricsCollector, RepoWatcher imports, snapshot integrity,
# and the shape expected by the dashboard frontend (MetricsSnapshot / RepoMetrics).
#
# Usage:  bash scripts/validate_metrics.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
export PYTHONPATH="${PROJECT_ROOT}/src"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TOTAL=0; PASSED=0; FAILED=0

run() {
  local name="$1"; shift
  TOTAL=$((TOTAL + 1))
  printf "  %-55s" "$name"
  if output=$(python "$@" 2>&1); then
    echo -e "${GREEN}PASS${NC}"
    PASSED=$((PASSED + 1))
  else
    echo -e "${RED}FAIL${NC}"
    echo "$output" | head -5 | sed 's/^/    /'
    FAILED=$((FAILED + 1))
  fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CEREBRO METRICS — Validation Suite"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── 1  Import checks ─────────────────────────────────────────────
echo "  [Imports]"
run "MetricsCollector" -c "from cerebro.core.metrics_collector import MetricsCollector"
run "RepoWatcher" -c "from cerebro.core.watcher import RepoWatcher"
run "core.__init__ (guarded gcp)" -c "import cerebro.core"
echo ""

# ── 2  Discovery ─────────────────────────────────────────────────
echo "  [Discovery]"
run "discover_repos returns >= 30 repos" -c "
from cerebro.core.metrics_collector import MetricsCollector
repos = MetricsCollector('/home/kernelcore/arch').discover_repos()
assert len(repos) >= 30, f'only {len(repos)} repos'
print(f'{len(repos)} repos discovered')
"

run "no duplicate repo names" -c "
from cerebro.core.metrics_collector import MetricsCollector
repos = MetricsCollector('/home/kernelcore/arch').discover_repos()
names = [r.name for r in repos]
dupes = [n for n in set(names) if names.count(n) > 1]
assert not dupes, f'duplicates: {dupes}'
"
echo ""

# ── 3  Full scan + snapshot ──────────────────────────────────────
echo "  [Scan & Snapshot]"
run "collect_all completes and saves snapshot" -c "
from cerebro.core.metrics_collector import MetricsCollector
mc = MetricsCollector('/home/kernelcore/arch')
results = mc.collect_all()
assert len(results) >= 30, f'only {len(results)} results'
print(f'{len(results)} repos scanned')
"

run "snapshot file is valid JSON" -c "
import json
from pathlib import Path
p = Path('/home/kernelcore/arch/cerebro/data/metrics/metrics_snapshot.json')
assert p.exists(), 'snapshot file missing'
data = json.loads(p.read_text())
assert 'repos' in data
print(f'{len(data[\"repos\"])} repos in snapshot JSON')
"
echo ""

# ── 4  Snapshot shape (mirrors TypeScript MetricsSnapshot / RepoMetrics) ──
echo "  [Shape / Contract]"
run "top-level keys: generated_at, repo_count, repos" -c "
import json
from pathlib import Path
data = json.loads(Path('/home/kernelcore/arch/cerebro/data/metrics/metrics_snapshot.json').read_text())
for k in ('generated_at', 'repo_count', 'repos'):
    assert k in data, f'missing top-level key: {k}'
assert data['repo_count'] == len(data['repos'])
"

run "every repo has all RepoMetrics fields" -c "
import json
from pathlib import Path
FIELDS = [
    'name','path','collected_at','total_files','total_loc','languages',
    'primary_language','git','dependencies','dep_count',
    'security_findings','security_score','has_tests','test_files',
    'has_ci','has_readme','has_docs','has_flake','health_score','status',
]
data = json.loads(Path('/home/kernelcore/arch/cerebro/data/metrics/metrics_snapshot.json').read_text())
for repo in data['repos']:
    missing = [f for f in FIELDS if f not in repo]
    assert not missing, f'{repo.get(\"name\",\"?\")} missing: {missing}'
print(f'All {len(data[\"repos\"])} repos have complete field sets')
"

run "languages map has files + lines per entry" -c "
import json
from pathlib import Path
data = json.loads(Path('/home/kernelcore/arch/cerebro/data/metrics/metrics_snapshot.json').read_text())
for repo in data['repos']:
    for lang, stats in repo.get('languages', {}).items():
        assert 'files' in stats and 'lines' in stats, \
            f'{repo[\"name\"]}:{lang} missing files/lines'
print('language stats structure valid')
"

run "git object has expected keys (non-empty repos)" -c "
import json
from pathlib import Path
GIT_KEYS = ['total_commits','commits_30d','commits_90d','contributors','branches','tags']
data = json.loads(Path('/home/kernelcore/arch/cerebro/data/metrics/metrics_snapshot.json').read_text())
checked = 0
for repo in data['repos']:
    if repo['status'] == 'empty':
        continue
    for k in GIT_KEYS:
        assert k in repo['git'], f'{repo[\"name\"]}.git missing: {k}'
    checked += 1
print(f'git structure valid for {checked} non-empty repos')
"
echo ""

# ── 5  Watcher class smoke ───────────────────────────────────────
echo "  [Watcher]"
run "RepoWatcher instantiation + tracked_count" -c "
from cerebro.core.watcher import RepoWatcher
w = RepoWatcher(arch_path='/home/kernelcore/arch', poll_interval=10)
# not started — tracked_count is 0 until start()
assert w.tracked_count == 0
assert w.is_running is False
assert w.changes_detected == 0
print('RepoWatcher constructed OK')
"

run "get_head_hash returns 40-char SHA (non-empty repo)" -c "
from cerebro.core.metrics_collector import MetricsCollector
mc = MetricsCollector('/home/kernelcore/arch')
for repo in mc.discover_repos():
    h = mc.get_head_hash(repo)
    if h:
        assert len(h) == 40 and all(c in '0123456789abcdef' for c in h), f'bad hash: {h!r}'
        print(f'{repo.name}: {h[:12]}…')
        break
else:
    raise AssertionError('no repo with a valid HEAD found')
"
echo ""

# ── summary ──────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "  Total: %-4d " "$TOTAL"
printf "${GREEN}Pass: %-4d${NC} " "$PASSED"
printf "${RED}Fail: %-4d${NC}\n" "$FAILED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

[ "$FAILED" -eq 0 ] && echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}" && exit 0
echo -e "${RED}❌ SOME CHECKS FAILED${NC}" && exit 1
