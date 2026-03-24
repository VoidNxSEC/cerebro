"""
Metrics Collector — Zero-Token Repository Analysis Engine

Collects real metrics from all repositories using only:
  - git CLI (commit history, contributors, branches)
  - filesystem traversal (file counts, LoC by language)
  - config file parsing (dependencies from pyproject.toml / Cargo.toml / package.json / go.mod)
  - regex heuristics (security patterns)

Zero LLM tokens consumed.
"""

import json
import os
import re
import subprocess
import tomllib
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import logging

logger = logging.getLogger("cerebro.metrics")

# ---------------------------------------------------------------------------
# Language / extension maps
# ---------------------------------------------------------------------------
LANG_EXTENSIONS: Dict[str, List[str]] = {
    "Python": [".py"],
    "Rust": [".rs"],
    "TypeScript": [".ts", ".tsx"],
    "JavaScript": [".js", ".jsx", ".mjs"],
    "Nix": [".nix"],
    "Go": [".go"],
    "Solidity": [".sol"],
    "Shell": [".sh"],
    "YAML": [".yaml", ".yml"],
    "TOML": [".toml"],
    "JSON": [".json"],
    "Markdown": [".md"],
    "CSS": [".css"],
    "HTML": [".html"],
    "C": [".c", ".h"],
    "C++": [".cpp", ".hpp", ".cc", ".hh"],
    "Java": [".java"],
    "Zig": [".zig"],
    "Svelte": [".svelte"],
}

EXT_TO_LANG: Dict[str, str] = {ext: lang for lang, exts in LANG_EXTENSIONS.items() for ext in exts}

# ---------------------------------------------------------------------------
# Skip / security constants
# ---------------------------------------------------------------------------
SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "target", "dist", "build",
    "__pycache__", ".cache", ".nix-profile", "result", ".pytest_cache",
    ".nix-pip", ".archive", ".next",
}

MAX_FILES_PER_REPO = 80_000  # safety cap for huge data repos

SECURITY_PATTERNS: Dict[str, re.Pattern] = {
    "hardcoded_secret": re.compile(
        r'(?i)(api[_-]?key|secret[_-]?key|password|token)\s*[=:]\s*["\'][A-Za-z0-9+/=_-]{20,}',
    ),
    "unsafe_eval": re.compile(r'\b(eval|exec)\s*\('),
    "shell_true": re.compile(r'subprocess\.\w+\([^)]*shell\s*=\s*True'),
    "debug_left": re.compile(r'\b(pdb\.set_trace|breakpoint\(\)|debugger)\b'),
}

# ---------------------------------------------------------------------------
# Health-score weights (must sum to 1.0)
# ---------------------------------------------------------------------------
WEIGHT_ACTIVITY: float = 0.30     # recent git activity
WEIGHT_DOCS: float = 0.20         # README + docs presence
WEIGHT_TESTING: float = 0.20      # test files present
WEIGHT_CI: float = 0.15           # CI/CD pipeline present
WEIGHT_SECURITY: float = 0.15     # security scan score

# Activity score building-blocks (activity = commits * MULTIPLIER + BASELINE, capped at 100)
ACTIVITY_30D_MULTIPLIER: int = 5
ACTIVITY_30D_BASELINE: int = 20
ACTIVITY_90D_MULTIPLIER: int = 2
ACTIVITY_90D_BASELINE: int = 10

# Documentation sub-scores
DOC_README_POINTS: float = 40.0
DOC_DOCS_DIR_POINTS: float = 40.0
DOC_LOC_THRESHOLD: int = 100      # minimum LoC to earn doc bonus
DOC_LOC_POINTS: float = 20.0

# Testing sub-score thresholds
TEST_FILES_HIGH: int = 20         # score 100
TEST_FILES_MID: int = 5           # score 80
TEST_SCORE_HIGH: float = 100.0
TEST_SCORE_MID: float = 80.0
TEST_SCORE_LOW: float = 60.0


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class RepoMetricsSnapshot:
    """Full metrics snapshot for one repository."""

    name: str
    path: str
    collected_at: str = ""

    # code
    total_files: int = 0
    total_loc: int = 0
    languages: Dict[str, Dict[str, int]] = field(default_factory=dict)
    primary_language: str = ""

    # git
    git: Dict[str, Any] = field(default_factory=dict)

    # deps
    dependencies: List[str] = field(default_factory=list)
    dep_count: int = 0

    # security
    security_findings: List[Dict[str, Any]] = field(default_factory=list)
    security_score: float = 100.0

    # quality
    has_tests: bool = False
    test_files: int = 0
    has_ci: bool = False
    has_readme: bool = False
    has_docs: bool = False
    has_flake: bool = False

    # derived
    health_score: float = 0.0
    status: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------
class MetricsCollector:
    """Zero-token metrics collector.  git + fs + regex, no LLM."""

    def __init__(self, arch_path: str | None = None):
        self.arch_path = Path(arch_path or os.getenv("CEREBRO_ARCH_PATH", str(Path.home() / "arch")))
        self.metrics_dir = self.arch_path / "cerebro" / "data" / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------
    # Names that are vendor / skill sub-repos — skip them
    SKIP_REPO_NAMES = {"ux-agents", "forge-std", "sdk-core"}

    def discover_repos(self) -> List[Path]:
        """Discover git repos up to 2 levels deep under arch_path, deduplicated."""
        seen: set = set()          # resolved paths already added
        repos: List[Path] = []
        skip_top = {"scripts", "docs", "skills"}

        def _add(p: Path) -> None:
            resolved = p.resolve()
            if resolved in seen or p.name in self.SKIP_REPO_NAMES:
                return
            seen.add(resolved)
            repos.append(p)

        for top in sorted(self.arch_path.iterdir()):
            if not top.is_dir() or top.name.startswith(".") or top.name in skip_top:
                continue
            if (top / ".git").exists():
                _add(top)

            try:
                for sub in sorted(top.iterdir()):
                    if not sub.is_dir() or sub.name.startswith(".") or sub.name in SKIP_DIRS:
                        continue
                    if (sub / ".git").exists():
                        _add(sub)
                    # two levels (phantom-ray/phantom-stack/services/*)
                    try:
                        for subsub in sorted(sub.iterdir()):
                            if not subsub.is_dir() or subsub.name.startswith(".") or subsub.name in SKIP_DIRS:
                                continue
                            if (subsub / ".git").exists():
                                _add(subsub)
                    except (PermissionError, OSError):
                        pass
            except (PermissionError, OSError):
                pass

        return repos

    # ------------------------------------------------------------------
    # Bulk / single collection
    # ------------------------------------------------------------------
    def collect_all(self) -> List[RepoMetricsSnapshot]:
        repos = self.discover_repos()
        logger.info("MetricsCollector: discovered %d repos", len(repos))
        results: List[RepoMetricsSnapshot] = []
        for repo_path in repos:
            try:
                snapshot = self.collect_repo(repo_path)
                results.append(snapshot)
                logger.info("  ✓ %s  LoC=%d  health=%.0f", snapshot.name, snapshot.total_loc, snapshot.health_score)
            except Exception as e:
                logger.error("  ✗ %s: %s", repo_path.name, e)
        self._save_snapshot(results)
        return results

    def collect_repo(self, repo_path: Path) -> RepoMetricsSnapshot:
        snapshot = RepoMetricsSnapshot(
            name=repo_path.name,
            path=str(repo_path),
            collected_at=datetime.now(timezone.utc).isoformat(),
        )
        self._collect_code_metrics(repo_path, snapshot)
        self._collect_git_metrics(repo_path, snapshot)
        self._collect_dependencies(repo_path, snapshot)
        self._collect_security(repo_path, snapshot)
        self._collect_quality(repo_path, snapshot)
        snapshot.health_score = self._calculate_health(snapshot)
        snapshot.status = self._determine_status(snapshot)
        return snapshot

    # ------------------------------------------------------------------
    # Code metrics (filesystem)
    # ------------------------------------------------------------------
    def _collect_code_metrics(self, repo_path: Path, snapshot: RepoMetricsSnapshot) -> None:
        lang_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"files": 0, "lines": 0})
        for file_path in self._iter_files(repo_path):
            if snapshot.total_files >= MAX_FILES_PER_REPO:
                break
            snapshot.total_files += 1
            ext = file_path.suffix.lower()
            if ext not in EXT_TO_LANG:
                continue
            lang = EXT_TO_LANG[ext]
            lang_stats[lang]["files"] += 1
            try:
                lines = len(file_path.read_text(errors="ignore").splitlines())
                lang_stats[lang]["lines"] += lines
                snapshot.total_loc += lines
            except (OSError, UnicodeDecodeError):
                pass

        snapshot.languages = dict(lang_stats)
        if lang_stats:
            snapshot.primary_language = max(lang_stats, key=lambda k: lang_stats[k]["lines"])

    def _iter_files(self, path: Path, depth: int = 0) -> Iterator[Path]:
        if depth > 7:
            return
        try:
            for item in path.iterdir():
                if item.name.startswith(".") or item.name in SKIP_DIRS:
                    continue
                if item.is_file():
                    try:
                        if item.stat().st_size < 5_000_000:  # skip files > 5 MB
                            yield item
                    except OSError:
                        pass
                elif item.is_dir():
                    yield from self._iter_files(item, depth + 1)
        except PermissionError:
            pass

    # ------------------------------------------------------------------
    # Git metrics
    # ------------------------------------------------------------------
    def _collect_git_metrics(self, repo_path: Path, snapshot: RepoMetricsSnapshot) -> None:
        if not (repo_path / ".git").exists():
            snapshot.git = {"error": "not a git repo"}
            return

        git: Dict[str, Any] = {}
        git["total_commits"] = self._git_int(repo_path, ["rev-list", "--count", "HEAD"])
        git["commits_30d"] = self._git_int(repo_path, ["rev-list", "--count", "--after=30 days ago", "HEAD"])
        git["commits_90d"] = self._git_int(repo_path, ["rev-list", "--count", "--after=90 days ago", "HEAD"])

        # contributors
        shortlog = self._git_output(repo_path, ["shortlog", "-sn", "--no-merges"])
        git["contributors"] = len([ln for ln in shortlog.splitlines() if ln.strip()])

        # branches / tags
        git["branches"] = len([ln for ln in self._git_output(repo_path, ["branch", "--list"]).splitlines() if ln.strip()])
        git["tags"] = len([ln for ln in self._git_output(repo_path, ["tag", "--list"]).splitlines() if ln.strip()])

        # last commit info
        last = self._git_output(repo_path, ["log", "-1", "--format=%H|%an|%ai|%s"])
        if last and "|" in last:
            parts = last.strip().split("|", 3)
            if len(parts) >= 4:
                git["last_commit_hash"] = parts[0][:12]
                git["last_commit_author"] = parts[1]
                git["last_commit_date"] = parts[2]
                git["last_commit_message"] = parts[3][:120]

        # top contributors
        git["top_contributors"] = []
        for line in shortlog.splitlines()[:5]:
            m = re.match(r"\s*(\d+)\s+(.+)", line.strip())
            if m:
                git["top_contributors"].append({"name": m.group(2).strip(), "commits": int(m.group(1))})

        snapshot.git = git

    # ------------------------------------------------------------------
    # Dependencies
    # ------------------------------------------------------------------
    def _collect_dependencies(self, repo_path: Path, snapshot: RepoMetricsSnapshot) -> None:
        deps: List[str] = []

        # pyproject.toml (Poetry)
        pyproject = repo_path / "pyproject.toml"
        if pyproject.exists():
            try:
                data = tomllib.loads(pyproject.read_text())
                for name in data.get("tool", {}).get("poetry", {}).get("dependencies", {}):
                    if name != "python":
                        deps.append(f"py:{name}")
            except Exception:
                pass

        # package.json
        pkg = repo_path / "package.json"
        if pkg.exists():
            try:
                data = json.loads(pkg.read_text())
                for name in data.get("dependencies", {}):
                    deps.append(f"npm:{name}")
                for name in data.get("devDependencies", {}):
                    deps.append(f"npm-dev:{name}")
            except Exception:
                pass

        # Cargo.toml
        cargo = repo_path / "Cargo.toml"
        if cargo.exists():
            try:
                content = cargo.read_text()
                in_deps = False
                for line in content.splitlines():
                    stripped = line.strip()
                    if stripped == "[dependencies]":
                        in_deps = True
                        continue
                    if stripped.startswith("[") and in_deps:
                        break
                    if in_deps:
                        m = re.match(r'^([\w-]+)\s*=', stripped)
                        if m:
                            deps.append(f"cargo:{m.group(1)}")
            except Exception:
                pass

        # go.mod
        gomod = repo_path / "go.mod"
        if gomod.exists():
            try:
                in_require = False
                for line in gomod.read_text().splitlines():
                    stripped = line.strip()
                    if stripped.startswith("require"):
                        in_require = True
                        continue
                    if in_require and stripped == ")":
                        in_require = False
                        continue
                    if in_require:
                        m = re.match(r"([\w./\-]+)\s+v", stripped)
                        if m:
                            deps.append(f"go:{m.group(1)}")
            except Exception:
                pass

        snapshot.dependencies = deps
        snapshot.dep_count = len(deps)

    # ------------------------------------------------------------------
    # Security scan
    # ------------------------------------------------------------------
    def _collect_security(self, repo_path: Path, snapshot: RepoMetricsSnapshot) -> None:
        findings: List[Dict[str, Any]] = []
        code_exts = set(EXT_TO_LANG.keys()) - {".json", ".yaml", ".yml", ".toml", ".md"}
        scanned = 0

        for file_path in self._iter_files(repo_path):
            if scanned >= 15_000:
                break
            if file_path.suffix.lower() not in code_exts:
                continue
            scanned += 1
            try:
                content = file_path.read_text(errors="ignore")
                seen_in_file: set = set()
                for pname, pat in SECURITY_PATTERNS.items():
                    if pname in seen_in_file:
                        continue
                    m = pat.search(content)
                    if m:
                        line_num = content[: m.start()].count("\n") + 1
                        findings.append({
                            "type": pname,
                            "file": str(file_path.relative_to(repo_path)),
                            "line": line_num,
                        })
                        seen_in_file.add(pname)
            except (OSError, UnicodeDecodeError):
                continue

        snapshot.security_findings = findings
        snapshot.security_score = max(0.0, 100.0 - len(findings) * 10)

    # ------------------------------------------------------------------
    # Quality indicators
    # ------------------------------------------------------------------
    def _collect_quality(self, repo_path: Path, snapshot: RepoMetricsSnapshot) -> None:
        snapshot.has_readme = any((repo_path / f).exists() for f in ["README.md", "README.rst", "README"])
        snapshot.has_docs = (repo_path / "docs").exists()
        snapshot.has_flake = (repo_path / "flake.nix").exists()
        snapshot.has_ci = (
            (repo_path / ".github" / "workflows").exists()
            or (repo_path / ".gitlab-ci.yml").exists()
            or (repo_path / "Jenkinsfile").exists()
        )

        tests_dir = None
        if (repo_path / "tests").exists():
            tests_dir = repo_path / "tests"
        elif (repo_path / "test").exists():
            tests_dir = repo_path / "test"

        snapshot.has_tests = tests_dir is not None
        if tests_dir:
            count = 0
            for f in tests_dir.rglob("*"):
                if f.is_file() and not any(p in SKIP_DIRS for p in f.relative_to(repo_path).parts):
                    count += 1
                    if count >= 5000:
                        break
            snapshot.test_files = count

    # ------------------------------------------------------------------
    # Health / status
    # ------------------------------------------------------------------
    def _calculate_health(self, snapshot: RepoMetricsSnapshot) -> float:
        # Activity (WEIGHT_ACTIVITY)
        c30 = snapshot.git.get("commits_30d", 0)
        c90 = snapshot.git.get("commits_90d", 0)
        if c30 > 0:
            activity = min(100.0, c30 * ACTIVITY_30D_MULTIPLIER + ACTIVITY_30D_BASELINE)
        elif c90 > 0:
            activity = min(100.0, c90 * ACTIVITY_90D_MULTIPLIER + ACTIVITY_90D_BASELINE)
        else:
            activity = 0.0

        # Documentation (WEIGHT_DOCS)
        doc = 0.0
        if snapshot.has_readme:
            doc += DOC_README_POINTS
        if snapshot.has_docs:
            doc += DOC_DOCS_DIR_POINTS
        if snapshot.total_loc > DOC_LOC_THRESHOLD:
            doc += DOC_LOC_POINTS
        doc = min(100.0, doc)

        # Testing (WEIGHT_TESTING)
        if not snapshot.has_tests:
            test_score = 0.0
        elif snapshot.test_files > TEST_FILES_HIGH:
            test_score = TEST_SCORE_HIGH
        elif snapshot.test_files > TEST_FILES_MID:
            test_score = TEST_SCORE_MID
        else:
            test_score = TEST_SCORE_LOW

        ci_score = 100.0 if snapshot.has_ci else 0.0
        return round(
            activity * WEIGHT_ACTIVITY
            + doc * WEIGHT_DOCS
            + test_score * WEIGHT_TESTING
            + ci_score * WEIGHT_CI
            + snapshot.security_score * WEIGHT_SECURITY,
            1,
        )

    @staticmethod
    def _determine_status(snapshot: RepoMetricsSnapshot) -> str:
        total = snapshot.git.get("total_commits", 0)
        if total == 0:
            return "empty"
        if snapshot.git.get("commits_30d", 0) > 0:
            return "active"
        if snapshot.git.get("commits_90d", 0) > 0:
            return "maintenance"
        return "archived"

    # ------------------------------------------------------------------
    # Git helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _git_output(repo_path: Path, args: List[str]) -> str:
        try:
            r = subprocess.run(
                ["git", *args], cwd=repo_path,
                capture_output=True, text=True, timeout=15,
            )
            return r.stdout if r.returncode == 0 else ""
        except (subprocess.TimeoutExpired, OSError):
            return ""

    @classmethod
    def _git_int(cls, repo_path: Path, args: List[str]) -> int:
        try:
            return int(cls._git_output(repo_path, args).strip())
        except ValueError:
            return 0

    def get_head_hash(self, repo_path: Path) -> str:
        return self._git_output(repo_path, ["rev-parse", "HEAD"]).strip()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _save_snapshot(self, snapshots: List[RepoMetricsSnapshot]) -> None:
        data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repo_count": len(snapshots),
            "repos": [snap.to_dict() for snap in snapshots],
        }
        (self.metrics_dir / "metrics_snapshot.json").write_text(json.dumps(data, indent=2))
        logger.info("Saved metrics snapshot: %d repos", len(snapshots))

    def load_snapshot(self) -> Optional[Dict[str, Any]]:
        p = self.metrics_dir / "metrics_snapshot.json"
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text())
        except Exception:
            return None
