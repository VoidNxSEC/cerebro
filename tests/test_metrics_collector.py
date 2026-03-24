"""Tests for MetricsCollector — zero-token repository analysis engine."""

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cerebro.core.metrics_collector import (
    MetricsCollector,
    RepoMetricsSnapshot,
    LANG_EXTENSIONS,
    EXT_TO_LANG,
    SKIP_DIRS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def tmp_arch(tmp_path):
    """Create a minimal arch directory with one git repo."""
    repo = tmp_path / "my-project"
    repo.mkdir()
    (repo / ".git").mkdir()

    # Add some source files
    (repo / "main.py").write_text("print('hello world')\n# line 2\n")
    (repo / "lib.py").write_text("def foo():\n    pass\n")
    (repo / "README.md").write_text("# My Project\n")

    # Add tests dir
    tests = repo / "tests"
    tests.mkdir()
    (tests / "test_main.py").write_text("def test_ok(): pass\n")

    return tmp_path


@pytest.fixture
def collector(tmp_arch):
    """MetricsCollector pointed at tmp_arch."""
    return MetricsCollector(arch_path=str(tmp_arch))


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------
class TestDiscoverRepos:
    def test_discovers_git_repos(self, collector, tmp_arch):
        repos = collector.discover_repos()
        names = [r.name for r in repos]
        assert "my-project" in names

    def test_skips_non_git_dirs(self, collector, tmp_arch):
        (tmp_arch / "not-a-repo").mkdir()
        repos = collector.discover_repos()
        names = [r.name for r in repos]
        assert "not-a-repo" not in names

    def test_skips_dotdirs(self, collector, tmp_arch):
        hidden = tmp_arch / ".hidden-repo"
        hidden.mkdir()
        (hidden / ".git").mkdir()
        repos = collector.discover_repos()
        names = [r.name for r in repos]
        assert ".hidden-repo" not in names

    def test_empty_arch(self, tmp_path):
        c = MetricsCollector(arch_path=str(tmp_path))
        repos = c.discover_repos()
        assert repos == []


# ---------------------------------------------------------------------------
# Code metrics
# ---------------------------------------------------------------------------
class TestCollectCodeMetrics:
    def test_counts_files_and_loc(self, collector, tmp_arch):
        repo_path = tmp_arch / "my-project"
        snap = RepoMetricsSnapshot(name="my-project", path=str(repo_path))
        collector._collect_code_metrics(repo_path, snap)

        assert snap.total_files >= 2  # main.py + lib.py (+ possibly README)
        assert snap.total_loc >= 4  # at least the Python lines

    def test_detects_primary_language(self, collector, tmp_arch):
        repo_path = tmp_arch / "my-project"
        snap = RepoMetricsSnapshot(name="my-project", path=str(repo_path))
        collector._collect_code_metrics(repo_path, snap)

        assert snap.primary_language == "Python"

    def test_language_extension_mapping(self):
        assert EXT_TO_LANG[".py"] == "Python"
        assert EXT_TO_LANG[".rs"] == "Rust"
        assert EXT_TO_LANG[".ts"] == "TypeScript"
        assert EXT_TO_LANG[".go"] == "Go"


# ---------------------------------------------------------------------------
# Git metrics
# ---------------------------------------------------------------------------
class TestCollectGitMetrics:
    def test_non_git_repo(self, collector, tmp_path):
        plain = tmp_path / "plain"
        plain.mkdir()
        snap = RepoMetricsSnapshot(name="plain", path=str(plain))
        collector._collect_git_metrics(plain, snap)
        assert snap.git.get("error") == "not a git repo"

    def test_git_output_timeout(self, tmp_arch):
        """_git_output returns empty string on timeout."""
        repo_path = tmp_arch / "my-project"
        with patch("cerebro.core.metrics_collector.subprocess.run", side_effect=subprocess.TimeoutExpired("git", 15)):
            result = MetricsCollector._git_output(repo_path, ["log"])
            assert result == ""

    def test_git_int_fallback(self, tmp_arch):
        """_git_int returns 0 on non-numeric output."""
        repo_path = tmp_arch / "my-project"
        with patch.object(MetricsCollector, "_git_output", return_value="not-a-number"):
            result = MetricsCollector._git_int(repo_path, ["rev-list", "--count", "HEAD"])
            assert result == 0


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------
class TestCollectDependencies:
    def test_parses_pyproject(self, collector, tmp_arch):
        repo_path = tmp_arch / "my-project"
        (repo_path / "pyproject.toml").write_text(
            '[tool.poetry.dependencies]\npython = "^3.11"\ntyper = "^0.9"\nrich = "^13.0"\n'
        )
        snap = RepoMetricsSnapshot(name="my-project", path=str(repo_path))
        collector._collect_dependencies(repo_path, snap)

        assert "py:typer" in snap.dependencies
        assert "py:rich" in snap.dependencies
        assert snap.dep_count >= 2

    def test_parses_package_json(self, collector, tmp_arch):
        repo_path = tmp_arch / "my-project"
        (repo_path / "package.json").write_text(
            json.dumps({"dependencies": {"react": "^18.0"}, "devDependencies": {"vite": "^5.0"}})
        )
        snap = RepoMetricsSnapshot(name="my-project", path=str(repo_path))
        collector._collect_dependencies(repo_path, snap)

        assert "npm:react" in snap.dependencies
        assert "npm-dev:vite" in snap.dependencies

    def test_no_dep_files(self, collector, tmp_arch):
        repo_path = tmp_arch / "my-project"
        snap = RepoMetricsSnapshot(name="my-project", path=str(repo_path))
        collector._collect_dependencies(repo_path, snap)
        assert snap.dep_count == 0


# ---------------------------------------------------------------------------
# Security scan
# ---------------------------------------------------------------------------
class TestCollectSecurity:
    def test_detects_hardcoded_secret(self, collector, tmp_arch):
        repo_path = tmp_arch / "my-project"
        (repo_path / "config.py").write_text('API_KEY = "sk_live_abcdef1234567890abcdef"\n')
        snap = RepoMetricsSnapshot(name="my-project", path=str(repo_path))
        collector._collect_security(repo_path, snap)

        types = [f["type"] for f in snap.security_findings]
        assert "hardcoded_secret" in types
        assert snap.security_score < 100.0

    def test_clean_repo(self, collector, tmp_arch):
        repo_path = tmp_arch / "my-project"
        snap = RepoMetricsSnapshot(name="my-project", path=str(repo_path))
        collector._collect_security(repo_path, snap)
        assert snap.security_score == 100.0


# ---------------------------------------------------------------------------
# Quality indicators
# ---------------------------------------------------------------------------
class TestCollectQuality:
    def test_detects_readme(self, collector, tmp_arch):
        repo_path = tmp_arch / "my-project"
        snap = RepoMetricsSnapshot(name="my-project", path=str(repo_path))
        collector._collect_quality(repo_path, snap)
        assert snap.has_readme is True

    def test_detects_tests(self, collector, tmp_arch):
        repo_path = tmp_arch / "my-project"
        snap = RepoMetricsSnapshot(name="my-project", path=str(repo_path))
        collector._collect_quality(repo_path, snap)
        assert snap.has_tests is True
        assert snap.test_files >= 1


# ---------------------------------------------------------------------------
# Health score
# ---------------------------------------------------------------------------
class TestHealthScore:
    def test_health_calculation(self, collector):
        snap = RepoMetricsSnapshot(
            name="test",
            path="/tmp/test",
            has_readme=True,
            has_docs=True,
            has_tests=True,
            test_files=25,
            has_ci=True,
            security_score=100.0,
            git={"commits_30d": 10, "commits_90d": 20},
        )
        score = collector._calculate_health(snap)
        assert 50 <= score <= 100

    def test_empty_repo_low_health(self, collector):
        snap = RepoMetricsSnapshot(name="empty", path="/tmp/empty", security_score=0.0)
        score = collector._calculate_health(snap)
        assert score == 0.0


# ---------------------------------------------------------------------------
# Status determination
# ---------------------------------------------------------------------------
class TestDetermineStatus:
    def test_active(self):
        snap = RepoMetricsSnapshot(name="x", path="/x", git={"total_commits": 50, "commits_30d": 5, "commits_90d": 10})
        assert MetricsCollector._determine_status(snap) == "active"

    def test_maintenance(self):
        snap = RepoMetricsSnapshot(name="x", path="/x", git={"total_commits": 50, "commits_30d": 0, "commits_90d": 3})
        assert MetricsCollector._determine_status(snap) == "maintenance"

    def test_archived(self):
        snap = RepoMetricsSnapshot(name="x", path="/x", git={"total_commits": 50, "commits_30d": 0, "commits_90d": 0})
        assert MetricsCollector._determine_status(snap) == "archived"

    def test_empty(self):
        snap = RepoMetricsSnapshot(name="x", path="/x", git={"total_commits": 0})
        assert MetricsCollector._determine_status(snap) == "empty"


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
class TestPersistence:
    def test_save_and_load_snapshot(self, collector, tmp_arch):
        snapshots = [
            RepoMetricsSnapshot(name="proj-a", path="/a", total_loc=100),
            RepoMetricsSnapshot(name="proj-b", path="/b", total_loc=200),
        ]
        collector._save_snapshot(snapshots)

        loaded = collector.load_snapshot()
        assert loaded is not None
        assert loaded["repo_count"] == 2
        assert loaded["repos"][0]["name"] == "proj-a"

    def test_load_missing_snapshot(self, tmp_path):
        c = MetricsCollector(arch_path=str(tmp_path))
        assert c.load_snapshot() is None


# ---------------------------------------------------------------------------
# RepoMetricsSnapshot
# ---------------------------------------------------------------------------
class TestRepoMetricsSnapshot:
    def test_to_dict(self):
        snap = RepoMetricsSnapshot(name="test", path="/test", total_loc=42)
        d = snap.to_dict()
        assert d["name"] == "test"
        assert d["total_loc"] == 42
        assert isinstance(d, dict)
