"""
CEREBRO Intelligence Core

The central nervous system of the ecosystem.
Coordinates all intelligence gathering, analysis, and dissemination.
"""

import asyncio
import json
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger("cerebro.intelligence")


class IntelligenceType(str, Enum):
    """Types of intelligence gathered by Cerebro."""
    SIGINT = "sigint"      # Signals: logs, metrics, events
    HUMINT = "humint"      # Human: ADRs, docs, decisions
    OSINT = "osint"        # Open Source: code, configs
    TECHINT = "techint"    # Technical: deps, architecture


class ThreatLevel(str, Enum):
    """Threat/Priority levels for intelligence items."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ProjectStatus(str, Enum):
    """Status of a project in the ecosystem."""
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


@dataclass
class IntelligenceItem:
    """A single piece of intelligence."""
    id: str
    type: IntelligenceType
    source: str
    title: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    threat_level: ThreatLevel = ThreatLevel.INFO
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = field(default_factory=list)
    related_projects: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["type"] = self.type.value
        data["threat_level"] = self.threat_level.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntelligenceItem":
        """Create from dictionary."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["type"] = IntelligenceType(data["type"])
        data["threat_level"] = ThreatLevel(data["threat_level"])
        return cls(**data)


@dataclass
class Project:
    """A project in the ~/arch ecosystem."""
    name: str
    path: Path
    description: str = ""
    languages: List[str] = field(default_factory=list)
    status: ProjectStatus = ProjectStatus.UNKNOWN
    health_score: float = 0.0
    last_commit: Optional[datetime] = None
    last_indexed: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    intelligence_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "path": str(self.path),
            "description": self.description,
            "languages": self.languages,
            "status": self.status.value,
            "health_score": self.health_score,
            "last_commit": self.last_commit.isoformat() if self.last_commit else None,
            "last_indexed": self.last_indexed.isoformat() if self.last_indexed else None,
            "dependencies": self.dependencies,
            "dependents": self.dependents,
            "metadata": self.metadata,
            "intelligence_count": self.intelligence_count,
        }


@dataclass
class EcosystemStatus:
    """Overall status of the ecosystem."""
    total_projects: int = 0
    active_projects: int = 0
    total_intelligence: int = 0
    health_score: float = 0.0
    last_scan: Optional[datetime] = None
    alerts: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_projects": self.total_projects,
            "active_projects": self.active_projects,
            "total_intelligence": self.total_intelligence,
            "health_score": self.health_score,
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "alerts": self.alerts,
        }


class CerebroIntelligence:
    """
    The Central Intelligence System.

    Cerebro acts as the brain of the entire ~/arch ecosystem,
    gathering, analyzing, and serving intelligence from all projects.
    """

    def __init__(
        self,
        arch_path: str = os.getenv("CEREBRO_ARCH_PATH", str(Path.home() / "master" / "cerebro")),
        nixos_path: str = "/etc/nixos",
        data_dir: str = os.getenv(
            "CEREBRO_DATA_DIR",
            str(Path.home() / "master" / "cerebro" / "data" / "intelligence"),
        ),
    ):
        self.arch_path = Path(arch_path)
        self.nixos_path = Path(nixos_path)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # In-memory stores
        self._projects: Dict[str, Project] = {}
        self._intelligence: Dict[str, IntelligenceItem] = {}
        self._ecosystem_status = EcosystemStatus()

        # Vector store for semantic search
        self._embeddings: Dict[str, List[float]] = {}

        # Load persisted data
        self._load_state()

        logger.info(f"Cerebro Intelligence initialized. Arch: {self.arch_path}")

    def _load_state(self) -> None:
        """Load persisted state from disk."""
        state_file = self.data_dir / "cerebro_state.json"
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                    # Restore projects
                    for name, proj_data in state.get("projects", {}).items():
                        proj_data["path"] = Path(proj_data["path"])
                        proj_data["status"] = ProjectStatus(proj_data["status"])
                        if proj_data.get("last_commit"):
                            proj_data["last_commit"] = datetime.fromisoformat(proj_data["last_commit"])
                        if proj_data.get("last_indexed"):
                            proj_data["last_indexed"] = datetime.fromisoformat(proj_data["last_indexed"])
                        self._projects[name] = Project(**proj_data)
                    logger.info(f"Loaded {len(self._projects)} projects from state")
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")

    def _save_state(self) -> None:
        """Persist state to disk."""
        state_file = self.data_dir / "cerebro_state.json"
        state = {
            "projects": {name: proj.to_dict() for name, proj in self._projects.items()},
            "ecosystem_status": self._ecosystem_status.to_dict(),
            "last_saved": datetime.now(timezone.utc).isoformat(),
        }
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)
        logger.info("State saved to disk")

    def generate_id(self, content: str) -> str:
        """Generate a unique ID for an intelligence item."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    # ==================== Project Management ====================

    def register_project(self, project: Project) -> None:
        """Register a project in the intelligence system."""
        self._projects[project.name] = project
        self._ecosystem_status.total_projects = len(self._projects)
        self._ecosystem_status.active_projects = sum(
            1 for p in self._projects.values()
            if p.status == ProjectStatus.ACTIVE
        )
        logger.info(f"Registered project: {project.name}")

    def get_project(self, name: str) -> Optional[Project]:
        """Get a project by name."""
        return self._projects.get(name)

    def list_projects(self) -> List[Project]:
        """List all registered projects."""
        return list(self._projects.values())

    def get_project_count(self) -> int:
        """Get total number of projects."""
        return len(self._projects)

    # ==================== Intelligence Management ====================

    def add_intelligence(self, item: IntelligenceItem) -> str:
        """Add an intelligence item to the system."""
        if not item.id:
            item.id = self.generate_id(item.content)
        self._intelligence[item.id] = item
        self._ecosystem_status.total_intelligence = len(self._intelligence)

        # Update related projects
        for proj_name in item.related_projects:
            if proj_name in self._projects:
                self._projects[proj_name].intelligence_count += 1

        logger.debug(f"Added intelligence: {item.id} ({item.type.value})")
        return item.id

    def get_intelligence(self, item_id: str) -> Optional[IntelligenceItem]:
        """Get an intelligence item by ID."""
        return self._intelligence.get(item_id)

    def query_intelligence(
        self,
        query: str,
        types: Optional[List[IntelligenceType]] = None,
        projects: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[IntelligenceItem]:
        """
        Query intelligence items.

        For now, simple keyword matching.
        TODO: Implement semantic search with embeddings.
        """
        results = []
        query_lower = query.lower()

        for item in self._intelligence.values():
            # Filter by type
            if types and item.type not in types:
                continue

            # Filter by project
            if projects and not any(p in item.related_projects for p in projects):
                continue

            # Simple keyword match (to be replaced with semantic search)
            if query_lower in item.content.lower() or query_lower in item.title.lower():
                results.append(item)

        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:limit]

    # ==================== Ecosystem Status ====================

    def get_ecosystem_status(self) -> EcosystemStatus:
        """Get the current ecosystem status."""
        return self._ecosystem_status

    def calculate_health_score(self) -> float:
        """Calculate overall ecosystem health score (0-100)."""
        if not self._projects:
            return 0.0

        total_score = sum(p.health_score for p in self._projects.values())
        return total_score / len(self._projects)

    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current alerts from the ecosystem."""
        alerts = []

        # Check for projects with low health
        for proj in self._projects.values():
            if proj.health_score < 50:
                alerts.append({
                    "type": "low_health",
                    "project": proj.name,
                    "score": proj.health_score,
                    "message": f"Project {proj.name} has low health score: {proj.health_score}",
                })

        # Check for critical intelligence
        for item in self._intelligence.values():
            if item.threat_level == ThreatLevel.CRITICAL:
                alerts.append({
                    "type": "critical_intel",
                    "id": item.id,
                    "title": item.title,
                    "message": f"Critical intelligence: {item.title}",
                })

        return alerts

    # ==================== Briefing ====================

    def generate_briefing(self) -> Dict[str, Any]:
        """Generate an intelligence briefing for the ecosystem."""
        now = datetime.now(timezone.utc)

        return {
            "timestamp": now.isoformat(),
            "classification": "INTERNAL",
            "ecosystem": {
                "total_projects": self._ecosystem_status.total_projects,
                "active_projects": self._ecosystem_status.active_projects,
                "health_score": self.calculate_health_score(),
            },
            "intelligence": {
                "total_items": len(self._intelligence),
                "by_type": {
                    t.value: sum(1 for i in self._intelligence.values() if i.type == t)
                    for t in IntelligenceType
                },
                "critical_count": sum(
                    1 for i in self._intelligence.values()
                    if i.threat_level == ThreatLevel.CRITICAL
                ),
            },
            "alerts": self.get_alerts(),
            "top_projects": [
                p.to_dict() for p in sorted(
                    self._projects.values(),
                    key=lambda x: x.health_score,
                    reverse=True
                )[:5]
            ],
        }

    # ==================== Persistence ====================

    def save(self) -> None:
        """Save current state to disk."""
        self._save_state()

    def shutdown(self) -> None:
        """Graceful shutdown."""
        self.save()
        logger.info("Cerebro Intelligence shutdown complete")
