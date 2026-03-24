"""
Dashboard API Server — serves the React dashboard at localhost:8000.

Reads real data from MetricsCollector snapshots (zero extra tokens).
Run:  cerebro dashboard-api   (or directly: uvicorn phantom.dashboard_server:app)
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from cerebro.core.metrics_collector import MetricsCollector

app = FastAPI(title="Cerebro Dashboard API", version="0.1.0")

_cors_origins = os.getenv("CEREBRO_CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_collector = MetricsCollector()


def _load_snapshot() -> dict | None:
    """Load the latest persisted metrics snapshot, or None."""
    return _collector.load_snapshot()


def _repo_to_project(repo: dict) -> dict:
    """Map a RepoMetricsSnapshot dict → Project shape the frontend expects."""
    langs = list(repo.get("languages", {}).keys())
    git = repo.get("git", {})
    return {
        "name": repo["name"],
        "path": repo.get("path", ""),
        "description": f"{repo.get('primary_language', '—')} · {repo.get('total_loc', 0):,} LoC",
        "languages": langs,
        "status": repo.get("status", "unknown"),
        "health_score": repo.get("health_score", 0.0),
        "last_commit": git.get("last_commit_date"),
        "last_indexed": repo.get("collected_at"),
        "metadata": {
            "total_files": repo.get("total_files", 0),
            "dep_count": repo.get("dep_count", 0),
            "security_score": repo.get("security_score", 100.0),
            "has_tests": repo.get("has_tests", False),
            "has_ci": repo.get("has_ci", False),
        },
    }


# ---------------------------------------------------------------------------
# Health / Status
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/status")
def status():
    snapshot = _load_snapshot()
    repos = snapshot.get("repos", []) if snapshot else []
    active = sum(1 for r in repos if r.get("status") == "active")
    avg_health = sum(r.get("health_score", 0) for r in repos) / len(repos) if repos else 0.0
    return {
        "total_projects": len(repos),
        "active_projects": active,
        "health_score": round(avg_health, 1),
        "total_intelligence": 0,
        "alerts_count": sum(len(r.get("security_findings", [])) for r in repos),
        "last_scan": snapshot.get("generated_at") if snapshot else None,
    }


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
@app.get("/projects")
def list_projects(
    status: str | None = Query(None),
    language: str | None = Query(None),
    sort_by: str = Query("health_score"),
    order: str = Query("desc"),
):
    snapshot = _load_snapshot()
    if not snapshot:
        return []

    projects = [_repo_to_project(r) for r in snapshot.get("repos", [])]

    if status:
        projects = [p for p in projects if p["status"] == status]
    if language:
        projects = [p for p in projects if language.lower() in [l.lower() for l in p["languages"]]]

    reverse = order == "desc"
    if sort_by == "health_score":
        projects.sort(key=lambda p: p["health_score"], reverse=reverse)
    elif sort_by == "name":
        projects.sort(key=lambda p: p["name"], reverse=reverse)

    return projects


@app.get("/projects/{name}")
def get_project(name: str):
    snapshot = _load_snapshot()
    if not snapshot:
        raise HTTPException(status_code=404, detail="No snapshot available")

    repo = next((r for r in snapshot.get("repos", []) if r["name"] == name), None)
    if not repo:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")
    return _repo_to_project(repo)


# ---------------------------------------------------------------------------
# Metrics (pass-through from snapshot)
# ---------------------------------------------------------------------------
@app.get("/metrics")
def get_metrics():
    snapshot = _load_snapshot()
    if not snapshot:
        return {"generated_at": "", "repo_count": 0, "repos": []}
    return snapshot


@app.get("/metrics/{name}")
def get_repo_metrics(name: str):
    snapshot = _load_snapshot()
    if not snapshot:
        raise HTTPException(status_code=404)

    repo = next((r for r in snapshot.get("repos", []) if r["name"] == name), None)
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repo '{name}' not found")
    return repo


@app.post("/metrics/scan")
def trigger_metrics_scan():
    """Trigger a fresh scan synchronously (blocks until done)."""
    results = _collector.collect_all()
    return {"status": "ok", "repo_count": len(results)}


@app.get("/metrics/watcher")
def watcher_status():
    return {
        "running": False,
        "tracked_repos": len(_collector.discover_repos()),
        "last_update": None,
        "changes_detected": 0,
        "poll_interval": 5,
    }


# ---------------------------------------------------------------------------
# Alerts (derived from security findings)
# ---------------------------------------------------------------------------
@app.get("/alerts")
def get_alerts():
    snapshot = _load_snapshot()
    if not snapshot:
        return []

    alerts = []
    for repo in snapshot.get("repos", []):
        for finding in repo.get("security_findings", []):
            alerts.append({
                "id": f"{repo['name']}-{finding['type']}-{finding['line']}",
                "type": finding["type"],
                "project": repo["name"],
                "message": f"{finding['file']}:{finding['line']}",
                "score": repo.get("security_score", 100.0),
            })
    return alerts


# ---------------------------------------------------------------------------
# Intelligence (stubs — no real data until RAG is connected)
# ---------------------------------------------------------------------------
@app.get("/intelligence/stats")
def intelligence_stats():
    return {
        "total_items": 0,
        "by_type": {"sigint": 0, "humint": 0, "osint": 0, "techint": 0},
        "last_indexed": None,
    }


@app.post("/intelligence/query")
def intelligence_query():
    return {"results": []}


# ---------------------------------------------------------------------------
# Briefings (derived from snapshot)
# ---------------------------------------------------------------------------
def _build_briefing(briefing_type: str) -> dict:
    snapshot = _load_snapshot()
    repos = snapshot.get("repos", []) if snapshot else []

    active = [r for r in repos if r.get("status") == "active"]
    avg_health = sum(r.get("health_score", 0) for r in repos) / len(repos) if repos else 0.0

    alerts = []
    for repo in repos:
        for finding in repo.get("security_findings", []):
            alerts.append({
                "type": finding["type"],
                "project": repo["name"],
                "message": f"{finding['file']}:{finding['line']}",
            })

    return {
        "type": briefing_type,
        "classification": "INTERNAL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "headline": f"{len(repos)} repos tracked · {len(active)} active · avg health {avg_health:.0f}%",
        "ecosystem_status": {
            "total_projects": len(repos),
            "active_projects": len(active),
            "health_score": round(avg_health, 1),
        },
        "alerts": alerts[:10],
        "project_summaries": [
            {
                "name": r["name"],
                "health_score": r.get("health_score", 0),
                "status": r.get("status", "unknown"),
                "insights": [
                    f"{r.get('primary_language', '—')} · {r.get('total_loc', 0):,} LoC",
                    f"{r.get('dep_count', 0)} deps · {len(r.get('security_findings', []))} findings",
                ],
            }
            for r in sorted(repos, key=lambda x: x.get("health_score", 0), reverse=True)[:8]
        ],
    }


@app.get("/briefing/daily")
def daily_briefing():
    return _build_briefing("daily")


@app.get("/briefing/executive")
def executive_briefing():
    return _build_briefing("executive")


# ---------------------------------------------------------------------------
# Graph (dependency edges between repos — stub)
# ---------------------------------------------------------------------------
@app.get("/graph/dependencies")
def dependency_graph():
    snapshot = _load_snapshot()
    repos = snapshot.get("repos", []) if snapshot else []
    nodes = [{"id": r["name"], "label": r["name"]} for r in repos]
    return {"nodes": nodes, "edges": []}


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------
@app.post("/actions/summarize/{project_name}")
def summarize_project(project_name: str):
    snapshot = _load_snapshot()
    repos = snapshot.get("repos", []) if snapshot else []
    repo = next((r for r in repos if r["name"] == project_name), None)
    if not repo:
        raise HTTPException(status_code=404)
    lines = [
        f"**{repo['name']}** — {repo.get('status', 'unknown')}",
        f"Health: {repo.get('health_score', 0)}% · LoC: {repo.get('total_loc', 0):,}",
        f"Primary language: {repo.get('primary_language', '—')}",
        f"Dependencies: {repo.get('dep_count', 0)}",
        f"Security score: {repo.get('security_score', 100)}%",
    ]
    return {"summary": "\n".join(lines)}
