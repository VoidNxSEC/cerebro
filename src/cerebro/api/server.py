"""
CEREBRO API Server

FastAPI server providing REST endpoints and WebSocket support
for the Cerebro Intelligence System.
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from cerebro.core.metrics_collector import MetricsCollector
from cerebro.core.watcher import RepoWatcher
from cerebro.intelligence.analyzer import IntelligenceAnalyzer
from cerebro.intelligence.briefing import BriefingGenerator, BriefingType
from cerebro.intelligence.core import (
    CerebroIntelligence,
    IntelligenceType,
    ThreatLevel,
)
from cerebro.providers.llamacpp import LlamaCppProvider
from cerebro.registry.indexer import KnowledgeIndexer
from cerebro.registry.scanner import ProjectScanner

logger = logging.getLogger("cerebro.api")

# Global instances
cerebro: CerebroIntelligence | None = None
scanner: ProjectScanner | None = None
indexer: KnowledgeIndexer | None = None
analyzer: IntelligenceAnalyzer | None = None
briefing_gen: BriefingGenerator | None = None
metrics_collector: MetricsCollector | None = None
repo_watcher: RepoWatcher | None = None
llama: LlamaCppProvider | None = None

# WebSocket connections and subscriptions
active_connections: list[WebSocket] = []


class SubscriptionManager:
    """Manages WebSocket subscriptions to different topics."""

    def __init__(self):
        self.subscriptions: dict[WebSocket, set[str]] = {}

    async def subscribe(self, ws: WebSocket, topic: str):
        """Subscribe a WebSocket connection to a topic."""
        if ws not in self.subscriptions:
            self.subscriptions[ws] = set()
        self.subscriptions[ws].add(topic)
        logger.info(f"WebSocket subscribed to topic: {topic}")

    async def unsubscribe(self, ws: WebSocket, topic: str):
        """Unsubscribe from a topic."""
        if ws in self.subscriptions:
            self.subscriptions[ws].discard(topic)

    def remove_connection(self, ws: WebSocket):
        """Remove all subscriptions for a connection."""
        if ws in self.subscriptions:
            del self.subscriptions[ws]

    async def broadcast_to_topic(self, topic: str, message: dict):
        """Broadcast message to all subscribers of a topic."""
        for ws, topics in list(self.subscriptions.items()):
            if topic in topics:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to WebSocket: {e}")


subscription_manager = SubscriptionManager()


# ==================== Pydantic Models ====================

class QueryRequest(BaseModel):
    """Request for intelligence query."""
    query: str = Field(..., min_length=1, max_length=1000)
    types: list[str] | None = None
    projects: list[str] | None = None
    limit: int = Field(default=10, ge=1, le=100)
    semantic: bool = Field(default=True, description="Use semantic search")


class QueryResponse(BaseModel):
    """Response for intelligence query."""
    query: str
    results: list[dict[str, Any]]
    total: int
    search_type: str


class ProjectResponse(BaseModel):
    """Response for project info."""
    name: str
    path: str
    description: str
    languages: list[str]
    status: str
    health_score: float
    last_commit: str | None
    last_indexed: str | None
    metadata: dict[str, Any]


class EcosystemStatus(BaseModel):
    """Ecosystem status response."""
    total_projects: int
    active_projects: int
    health_score: float
    total_intelligence: int
    alerts_count: int
    last_scan: str | None


class BriefingRequest(BaseModel):
    """Request for briefing generation."""
    type: str = Field(default="daily")
    project: str | None = None
    format: str = Field(default="json")  # json or markdown


class ScanRequest(BaseModel):
    """Request for ecosystem scan."""
    full_scan: bool = Field(default=False)
    collect_intelligence: bool = Field(default=True)


# ==================== Lifespan ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    global cerebro, scanner, indexer, analyzer, briefing_gen, metrics_collector, repo_watcher, llama

    # Configuration
    arch_path = os.getenv("CEREBRO_ARCH_PATH", "/home/kernelcore/master")
    data_dir = os.getenv("CEREBRO_DATA_DIR", "./data/intelligence")

    logger.info("Initializing Cerebro Intelligence System...")
    logger.info(f"Arch path: {arch_path}")
    logger.info(f"Data dir: {data_dir}")

    # Initialize components
    cerebro = CerebroIntelligence(
        arch_path=arch_path,
        data_dir=data_dir,
    )

    scanner = ProjectScanner(cerebro, arch_path)
    indexer = KnowledgeIndexer(cerebro, cache_dir=f"{data_dir}/embeddings")
    analyzer = IntelligenceAnalyzer(cerebro)
    briefing_gen = BriefingGenerator(cerebro)

    logger.info("Cerebro Intelligence System initialized")

    # Local LLM (llama.cpp on port 8081)
    llama = LlamaCppProvider()
    if llama.health_check():
        logger.info(f"LlamaCpp server online at {llama.base_url}")
    else:
        logger.warning(f"LlamaCpp server not reachable at {llama.base_url} — AI features degraded")

    # Initial project scan (background — does not block startup)
    asyncio.ensure_future(_initial_project_scan())

    # ---------- metrics collector + watcher ----------
    metrics_collector = MetricsCollector(arch_path=arch_path)
    if not metrics_collector.load_snapshot():
        logger.info("No metrics snapshot — running initial scan in background")
        asyncio.ensure_future(_initial_metrics_scan())
    else:
        logger.info("Loaded existing metrics snapshot")

    async def _on_repo_change(data: dict):
        await broadcast(data)
        await subscription_manager.broadcast_to_topic("metrics", data)

    repo_watcher = RepoWatcher(arch_path=arch_path, poll_interval=10, on_change=_on_repo_change)
    await repo_watcher.start()

    yield

    # Cleanup
    if repo_watcher:
        await repo_watcher.stop()
    if cerebro:
        cerebro.shutdown()
    logger.info("Cerebro Intelligence System shutdown")


# ==================== Create App ====================

def create_app() -> FastAPI:
    """Create the FastAPI application."""
    app = FastAPI(
        title="CEREBRO Intelligence API",
        description="Central Intelligence System for ~/arch ecosystem",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()


# ==================== Health & Status ====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "cerebro-intelligence",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/status", response_model=EcosystemStatus)
async def get_status():
    """Get ecosystem status."""
    if not cerebro:
        raise HTTPException(status_code=503, detail="Service not initialized")

    status = cerebro.get_ecosystem_status()
    alerts = cerebro.get_alerts()

    return EcosystemStatus(
        total_projects=status.total_projects,
        active_projects=status.active_projects,
        health_score=cerebro.calculate_health_score(),
        total_intelligence=status.total_intelligence,
        alerts_count=len(alerts),
        last_scan=status.last_scan.isoformat() if status.last_scan else None,
    )


# ==================== Projects ====================

@app.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    status: str | None = Query(None, description="Filter by status"),
    language: str | None = Query(None, description="Filter by language"),
    sort_by: str = Query("health_score", description="Sort field"),
    order: str = Query("desc", description="Sort order (asc/desc)"),
):
    """List all projects."""
    if not cerebro:
        raise HTTPException(status_code=503, detail="Service not initialized")

    projects = cerebro.list_projects()

    # Filter by status
    if status:
        projects = [p for p in projects if p.status.value == status]

    # Filter by language
    if language:
        projects = [p for p in projects if language in p.languages]

    # Sort
    reverse = order == "desc"
    if sort_by == "health_score":
        projects.sort(key=lambda p: p.health_score, reverse=reverse)
    elif sort_by == "name":
        projects.sort(key=lambda p: p.name, reverse=reverse)
    elif sort_by == "last_commit":
        projects.sort(
            key=lambda p: p.last_commit or datetime.min.replace(tzinfo=UTC),
            reverse=reverse
        )

    return [
        ProjectResponse(
            name=p.name,
            path=str(p.path),
            description=p.description,
            languages=p.languages,
            status=p.status.value,
            health_score=p.health_score,
            last_commit=p.last_commit.isoformat() if p.last_commit else None,
            last_indexed=p.last_indexed.isoformat() if p.last_indexed else None,
            metadata=p.metadata,
        )
        for p in projects
    ]


@app.get("/projects/{project_name}")
async def get_project(project_name: str):
    """Get detailed project information."""
    if not cerebro or not analyzer:
        raise HTTPException(status_code=503, detail="Service not initialized")

    project = cerebro.get_project(project_name)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    # Run analysis
    analysis = analyzer.analyze_project(project)

    return {
        "project": ProjectResponse(
            name=project.name,
            path=str(project.path),
            description=project.description,
            languages=project.languages,
            status=project.status.value,
            health_score=project.health_score,
            last_commit=project.last_commit.isoformat() if project.last_commit else None,
            last_indexed=project.last_indexed.isoformat() if project.last_indexed else None,
            metadata=project.metadata,
        ),
        "analysis": analysis,
    }


# ==================== Intelligence ====================

@app.post("/intelligence/query", response_model=QueryResponse)
async def query_intelligence(request: QueryRequest):
    """Query the intelligence database."""
    if not cerebro or not indexer:
        raise HTTPException(status_code=503, detail="Service not initialized")

    # Convert type strings to enums
    types = None
    if request.types:
        types = [IntelligenceType(t) for t in request.types]

    if request.semantic:
        # Use semantic search
        results = indexer.semantic_query(
            query=request.query,
            top_k=request.limit,
        )
        search_type = "semantic"
    else:
        # Use keyword search
        items = cerebro.query_intelligence(
            query=request.query,
            types=types,
            projects=request.projects,
            limit=request.limit,
        )
        results = [item.to_dict() for item in items]
        search_type = "keyword"

    return QueryResponse(
        query=request.query,
        results=results,
        total=len(results),
        search_type=search_type,
    )


@app.get("/intelligence/stats")
async def get_intelligence_stats():
    """Get intelligence statistics."""
    if not cerebro or not indexer:
        raise HTTPException(status_code=503, detail="Service not initialized")

    intel_by_type = {}
    for intel_type in IntelligenceType:
        count = sum(
            1 for i in cerebro._intelligence.values()
            if i.type == intel_type
        )
        intel_by_type[intel_type.value] = count

    intel_by_threat = {}
    for threat_level in ThreatLevel:
        count = sum(
            1 for i in cerebro._intelligence.values()
            if i.threat_level == threat_level
        )
        intel_by_threat[threat_level.value] = count

    return {
        "total": len(cerebro._intelligence),
        "by_type": intel_by_type,
        "by_threat_level": intel_by_threat,
        "indexer_stats": indexer.get_stats(),
    }


# ==================== Briefings ====================

@app.post("/briefing")
async def generate_briefing(request: BriefingRequest):
    """Generate an intelligence briefing."""
    if not briefing_gen:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        briefing_type = BriefingType(request.type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid briefing type: {request.type}. Valid types: {[t.value for t in BriefingType]}"
        )

    briefing = briefing_gen.generate(briefing_type, request.project)

    if request.format == "markdown":
        return JSONResponse(
            content={"markdown": briefing_gen.to_markdown(briefing)},
            media_type="application/json",
        )

    return briefing


@app.get("/briefing/daily")
async def get_daily_briefing():
    """Get the daily briefing."""
    if not briefing_gen:
        raise HTTPException(status_code=503, detail="Service not initialized")

    return briefing_gen.generate(BriefingType.DAILY)


@app.get("/briefing/executive")
async def get_executive_briefing():
    """Get the executive summary."""
    if not briefing_gen:
        raise HTTPException(status_code=503, detail="Service not initialized")

    return briefing_gen.generate(BriefingType.EXECUTIVE)


# ==================== Scanning ====================

@app.post("/actions/scan")
async def trigger_scan(request: ScanRequest):
    """Trigger an ecosystem scan."""
    if not scanner or not indexer:
        raise HTTPException(status_code=503, detail="Service not initialized")

    if request.collect_intelligence:
        stats = scanner.full_scan_with_intelligence()
    else:
        projects = scanner.scan(full_scan=request.full_scan)
        stats = {"projects_found": len(projects)}

    # Index new intelligence
    indexed = indexer.index_all()
    stats["indexed_items"] = indexed

    # Broadcast update to WebSocket clients
    await broadcast({
        "type": "scan_complete",
        "stats": stats,
    })

    # Also broadcast to subscribers
    await subscription_manager.broadcast_to_topic("projects", {
        "type": "scan_complete",
        "stats": stats,
    })

    return stats


# ==================== Alerts ====================

@app.get("/alerts")
async def get_alerts():
    """Get current alerts."""
    if not cerebro:
        raise HTTPException(status_code=503, detail="Service not initialized")

    return cerebro.get_alerts()


# ==================== Dependencies Graph ====================

@app.get("/graph/dependencies")
async def get_dependency_graph():
    """Get project dependency graph."""
    if not analyzer:
        raise HTTPException(status_code=503, detail="Service not initialized")

    graph = analyzer.find_dependencies_graph()

    # Convert to nodes and edges for visualization
    nodes = [{"id": name, "label": name} for name in graph.keys()]
    edges = []
    for source, targets in graph.items():
        for target in targets:
            edges.append({"source": source, "target": target})

    return {
        "nodes": nodes,
        "edges": edges,
    }


# ==================== WebSocket ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        # Send initial status
        if cerebro:
            status = cerebro.get_ecosystem_status()
            await websocket.send_json({
                "type": "status",
                "data": status.to_dict(),
            })

        # Keep connection alive and handle messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")

            # Handle different message types
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "subscribe":
                # Subscribe to topics: "alerts", "projects", "intelligence", "logs"
                topic = message.get("topic")
                if topic:
                    await subscription_manager.subscribe(websocket, topic)
                    await websocket.send_json({
                        "type": "subscribed",
                        "topic": topic
                    })

            elif msg_type == "unsubscribe":
                topic = message.get("topic")
                if topic:
                    await subscription_manager.unsubscribe(websocket, topic)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "topic": topic
                    })

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        subscription_manager.remove_connection(websocket)


async def broadcast(message: dict[str, Any]):
    """Broadcast message to all connected WebSocket clients."""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception:
            pass


# ==================== AI Features ====================

@app.get("/ai/health")
async def ai_health():
    """Check local LLM (llama.cpp) availability."""
    if not llama:
        return {"available": False, "url": None}
    healthy = llama.health_check()
    return {
        "available": healthy,
        "url": llama.base_url,
        "model": llama.model,
    }


@app.post("/actions/summarize/{project_name}")
async def summarize_project(project_name: str):
    """Generate AI summary for a project using local LLM when available."""
    if not cerebro:
        raise HTTPException(status_code=503, detail="Service not initialized")

    project = cerebro.get_project(project_name)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    intel_items = cerebro.query_intelligence(
        query="",
        projects=[project_name],
        limit=20,
    )

    # Use local LLM if available
    if llama and llama.health_check():
        context_lines = [item.content for item in intel_items[:10] if item.content]
        context = "\n".join(context_lines) if context_lines else "No intelligence collected yet."
        prompt = (
            f"Write a concise technical summary for the project '{project_name}'.\n\n"
            f"Project info:\n"
            f"- Description: {project.description or 'N/A'}\n"
            f"- Languages: {', '.join(project.languages) or 'N/A'}\n"
            f"- Health score: {project.health_score:.0f}%\n"
            f"- Status: {project.status.value}\n\n"
            f"Intelligence context:\n{context}\n\n"
            f"Summary (2-3 sentences):"
        )
        loop = asyncio.get_running_loop()
        summary = await loop.run_in_executor(None, llama.generate, prompt)
        return {"summary": summary, "source": "llamacpp"}

    # Fallback: static summary
    lines = [
        f"**{project_name}** — {project.description or 'No description'}",
        f"Languages: {', '.join(project.languages) or 'N/A'}",
        f"Health score: {project.health_score:.0f}%  |  Status: {project.status.value}",
        f"Intelligence items: {len(intel_items)}",
    ]
    if project.health_score < 50:
        lines.append("Recommendation: improve documentation and test coverage.")
    return {"summary": "\n".join(lines), "source": "static"}


# ==================== Metrics ====================


async def _initial_project_scan():
    """Background task: discover projects on first startup."""
    if scanner:
        loop = asyncio.get_running_loop()
        projects = await loop.run_in_executor(None, scanner.scan)
        logger.info(f"Initial project scan complete: {len(projects)} projects found")


async def _initial_metrics_scan():
    """Background task: run first metrics scan without blocking startup."""
    if metrics_collector:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, metrics_collector.collect_all)
        logger.info("Initial metrics scan complete")


@app.get("/metrics")
async def get_all_metrics():
    """Latest metrics snapshot (all repos)."""
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics not initialised")
    snap = metrics_collector.load_snapshot()
    if not snap:
        raise HTTPException(status_code=404, detail="No snapshot — POST /metrics/scan first")
    return snap


@app.get("/metrics/watcher")
async def get_watcher_status():
    """Real-time watcher status."""
    if not repo_watcher:
        return {"running": False, "tracked_repos": 0, "last_update": None, "changes_detected": 0, "poll_interval": 0}
    return {
        "running": repo_watcher.is_running,
        "tracked_repos": repo_watcher.tracked_count,
        "last_update": repo_watcher.last_update,
        "changes_detected": repo_watcher.changes_detected,
        "poll_interval": repo_watcher.poll_interval,
    }


@app.post("/metrics/scan")
async def trigger_metrics_scan():
    """Trigger a full zero-token metrics re-scan."""
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics not initialised")
    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, metrics_collector.collect_all)
    await broadcast({"type": "metrics_scan_complete", "repo_count": len(results), "timestamp": datetime.now(UTC).isoformat()})
    await subscription_manager.broadcast_to_topic("metrics", {"type": "metrics_scan_complete", "repo_count": len(results)})
    return {"status": "complete", "repo_count": len(results)}


@app.get("/metrics/{repo_name}")
async def get_repo_metrics(repo_name: str):
    """Metrics for a single repo."""
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics not initialised")
    snap = metrics_collector.load_snapshot()
    if not snap:
        raise HTTPException(status_code=404, detail="No snapshot")
    for repo in snap.get("repos", []):
        if repo["name"] == repo_name:
            return repo
    raise HTTPException(status_code=404, detail=f"Repo not found: {repo_name}")


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "cerebro.api.server:app",
        host="0.0.0.0",
        port=8009,
        reload=True,
    )
