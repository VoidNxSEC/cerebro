"""Tests for the Dashboard API Server.

Uses FastAPI TestClient with a mocked MetricsCollector to avoid
real filesystem access.
"""

from unittest.mock import MagicMock, patch

import pytest

try:
    from fastapi.testclient import TestClient
except (ImportError, RuntimeError):
    pytest.skip("httpx required for FastAPI TestClient", allow_module_level=True)


# ---------------------------------------------------------------------------
# Sample snapshot data used across tests
# ---------------------------------------------------------------------------
SAMPLE_SNAPSHOT = {
    "generated_at": "2026-02-14T10:00:00+00:00",
    "repo_count": 2,
    "repos": [
        {
            "name": "alpha",
            "path": "/arch/alpha",
            "total_files": 50,
            "total_loc": 3000,
            "primary_language": "Python",
            "languages": {"Python": {"files": 40, "lines": 2500}, "Shell": {"files": 10, "lines": 500}},
            "git": {"last_commit_date": "2026-02-13T08:00:00", "total_commits": 120, "commits_30d": 5, "commits_90d": 20},
            "dep_count": 8,
            "security_findings": [
                {"type": "hardcoded_secret", "file": "config.py", "line": 12},
            ],
            "security_score": 90.0,
            "has_tests": True,
            "has_ci": True,
            "health_score": 85.0,
            "status": "active",
            "collected_at": "2026-02-14T10:00:00",
        },
        {
            "name": "beta",
            "path": "/arch/beta",
            "total_files": 20,
            "total_loc": 800,
            "primary_language": "Rust",
            "languages": {"Rust": {"files": 15, "lines": 700}},
            "git": {"last_commit_date": "2025-11-01T10:00:00", "total_commits": 30, "commits_30d": 0, "commits_90d": 0},
            "dep_count": 3,
            "security_findings": [],
            "security_score": 100.0,
            "has_tests": False,
            "has_ci": False,
            "health_score": 30.0,
            "status": "archived",
            "collected_at": "2026-02-14T10:00:00",
        },
    ],
}


@pytest.fixture
def client():
    """Create a TestClient with mocked MetricsCollector."""
    with patch("cerebro.dashboard_server._collector") as mock_coll:
        mock_coll.load_snapshot.return_value = SAMPLE_SNAPSHOT
        mock_coll.discover_repos.return_value = [MagicMock()] * 2
        mock_coll.collect_all.return_value = [MagicMock(), MagicMock()]

        from cerebro.dashboard_server import app
        with TestClient(app) as c:
            yield c


@pytest.fixture
def empty_client():
    """TestClient where load_snapshot returns None (no data)."""
    with patch("cerebro.dashboard_server._collector") as mock_coll:
        mock_coll.load_snapshot.return_value = None
        mock_coll.discover_repos.return_value = []

        from cerebro.dashboard_server import app
        with TestClient(app) as c:
            yield c


# ---------------------------------------------------------------------------
# Health / Status
# ---------------------------------------------------------------------------
class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    def test_status(self, client):
        r = client.get("/status")
        assert r.status_code == 200
        data = r.json()
        assert data["total_projects"] == 2
        assert data["active_projects"] == 1
        assert data["health_score"] > 0

    def test_status_empty(self, empty_client):
        r = empty_client.get("/status")
        assert r.status_code == 200
        data = r.json()
        assert data["total_projects"] == 0


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
class TestProjects:
    def test_list_projects(self, client):
        r = client.get("/projects")
        assert r.status_code == 200
        projects = r.json()
        assert len(projects) == 2

    def test_list_projects_filter_status(self, client):
        r = client.get("/projects", params={"status": "active"})
        projects = r.json()
        assert len(projects) == 1
        assert projects[0]["name"] == "alpha"

    def test_list_projects_filter_language(self, client):
        r = client.get("/projects", params={"language": "rust"})
        projects = r.json()
        assert len(projects) == 1
        assert projects[0]["name"] == "beta"

    def test_list_projects_sort_by_name(self, client):
        r = client.get("/projects", params={"sort_by": "name", "order": "asc"})
        projects = r.json()
        assert projects[0]["name"] == "alpha"

    def test_list_projects_empty(self, empty_client):
        r = empty_client.get("/projects")
        assert r.json() == []

    def test_get_project(self, client):
        r = client.get("/projects/alpha")
        assert r.status_code == 200
        assert r.json()["name"] == "alpha"

    def test_get_project_not_found(self, client):
        r = client.get("/projects/nonexistent")
        assert r.status_code == 404

    def test_get_project_no_snapshot(self, empty_client):
        r = empty_client.get("/projects/anything")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
class TestMetrics:
    def test_get_metrics(self, client):
        r = client.get("/metrics")
        assert r.status_code == 200
        data = r.json()
        assert data["repo_count"] == 2

    def test_get_metrics_empty(self, empty_client):
        r = empty_client.get("/metrics")
        data = r.json()
        assert data["repo_count"] == 0

    def test_get_repo_metrics(self, client):
        r = client.get("/metrics/alpha")
        assert r.status_code == 200
        assert r.json()["name"] == "alpha"

    def test_get_repo_metrics_not_found(self, client):
        r = client.get("/metrics/nonexistent")
        assert r.status_code == 404

    def test_trigger_scan(self, client):
        r = client.post("/metrics/scan")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_watcher_status(self, client):
        r = client.get("/metrics/watcher")
        assert r.status_code == 200
        data = r.json()
        assert "running" in data
        assert "tracked_repos" in data


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------
class TestAlerts:
    def test_get_alerts(self, client):
        r = client.get("/alerts")
        assert r.status_code == 200
        alerts = r.json()
        assert len(alerts) >= 1
        assert alerts[0]["project"] == "alpha"
        assert alerts[0]["type"] == "hardcoded_secret"

    def test_no_alerts_empty(self, empty_client):
        r = empty_client.get("/alerts")
        assert r.json() == []


# ---------------------------------------------------------------------------
# Intelligence (stubs)
# ---------------------------------------------------------------------------
class TestIntelligence:
    def test_intelligence_stats(self, client):
        r = client.get("/intelligence/stats")
        assert r.status_code == 200
        assert r.json()["total_items"] == 0

    def test_intelligence_query(self, client):
        r = client.post("/intelligence/query")
        assert r.status_code == 200
        assert r.json()["results"] == []


# ---------------------------------------------------------------------------
# Briefings
# ---------------------------------------------------------------------------
class TestBriefings:
    def test_daily_briefing(self, client):
        r = client.get("/briefing/daily")
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "daily"
        assert "headline" in data
        assert data["ecosystem_status"]["total_projects"] == 2

    def test_executive_briefing(self, client):
        r = client.get("/briefing/executive")
        assert r.status_code == 200
        assert r.json()["type"] == "executive"


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
class TestGraph:
    def test_dependency_graph(self, client):
        r = client.get("/graph/dependencies")
        assert r.status_code == 200
        data = r.json()
        assert len(data["nodes"]) == 2
        assert data["edges"] == []


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------
class TestActions:
    def test_summarize_project(self, client):
        r = client.post("/actions/summarize/alpha")
        assert r.status_code == 200
        assert "alpha" in r.json()["summary"].lower()

    def test_summarize_project_not_found(self, client):
        r = client.post("/actions/summarize/nonexistent")
        assert r.status_code == 404
