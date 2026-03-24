"""
Project Scanner

Scans ~/arch directory to discover and register all projects.
Detects project types, languages, and collects initial metadata.
"""

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import json
import logging

from cerebro.intelligence.core import (
    CerebroIntelligence,
    Project,
    ProjectStatus,
)
from cerebro.intelligence.collectors import (
    SignalCollector,
    HumanIntelCollector,
    OpenSourceCollector,
    TechIntelCollector,
)

logger = logging.getLogger("cerebro.scanner")


# Directories to ignore during scanning
IGNORED_DIRS = {
    ".git",
    ".github",
    ".gitlab",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "target",
    "dist",
    "build",
    ".cache",
    ".nix-profile",
    "result",
}

# Files that indicate a project root
PROJECT_MARKERS = [
    "flake.nix",        # Nix flake
    "Cargo.toml",       # Rust
    "package.json",     # Node.js
    "pyproject.toml",   # Python
    "go.mod",           # Go
    "pom.xml",          # Java Maven
    "build.gradle",     # Java Gradle
    "Makefile",         # Generic
    "justfile",         # Just task runner
    "README.md",        # Documentation
    ".git",             # Git repo
]


class ProjectScanner:
    """
    Scans and discovers projects in the ecosystem.

    Automatically detects:
    - Project boundaries
    - Languages used
    - Build systems
    - Configuration files
    """

    def __init__(
        self,
        cerebro: CerebroIntelligence,
        arch_path: str = os.getenv("CEREBRO_ARCH_PATH", str(Path.home() / "arch")),
    ):
        self.cerebro = cerebro
        self.arch_path = Path(arch_path)

        # Initialize collectors
        self.collectors = [
            SignalCollector(cerebro),
            HumanIntelCollector(cerebro),
            OpenSourceCollector(cerebro),
            TechIntelCollector(cerebro),
        ]

    def scan(self, full_scan: bool = False) -> List[Project]:
        """
        Scan the arch directory for projects.

        Args:
            full_scan: If True, re-scan all projects. If False, only scan new ones.

        Returns:
            List of discovered projects.
        """
        logger.info(f"Starting scan of {self.arch_path}")
        discovered_projects = []

        if not self.arch_path.exists():
            logger.warning(f"Arch path does not exist: {self.arch_path}")
            return discovered_projects

        # Scan top-level directories
        for item in self.arch_path.iterdir():
            if not item.is_dir():
                continue

            if item.name in IGNORED_DIRS or item.name.startswith("."):
                continue

            # Check if it's a project
            if self._is_project(item):
                project = self._scan_project(item)
                if project:
                    discovered_projects.append(project)
                    self.cerebro.register_project(project)
                    logger.info(f"Discovered project: {project.name}")

        logger.info(f"Scan complete. Found {len(discovered_projects)} projects.")
        return discovered_projects

    def _is_project(self, path: Path) -> bool:
        """Check if a directory is a project root."""
        for marker in PROJECT_MARKERS:
            if (path / marker).exists():
                return True
        return False

    def _scan_project(self, path: Path) -> Optional[Project]:
        """Scan a single project and extract metadata."""
        try:
            project = Project(
                name=path.name,
                path=path,
            )

            # Detect languages
            project.languages = self._detect_languages(path)

            # Get description from README
            project.description = self._extract_description(path)

            # Get last commit time
            project.last_commit = self._get_last_commit_time(path)

            # Calculate initial health score
            project.health_score = self._calculate_initial_health(path)

            # Determine status
            project.status = self._determine_status(project)

            # Set indexed time
            project.last_indexed = datetime.now(timezone.utc)

            # Collect metadata
            project.metadata = self._collect_metadata(path)

            return project

        except Exception as e:
            logger.error(f"Error scanning project {path.name}: {e}")
            return None

    def _detect_languages(self, path: Path) -> List[str]:
        """Detect programming languages used in the project."""
        languages = set()

        # Check for language-specific files
        language_indicators = {
            "*.py": "Python",
            "*.rs": "Rust",
            "*.ts": "TypeScript",
            "*.tsx": "TypeScript",
            "*.js": "JavaScript",
            "*.jsx": "JavaScript",
            "*.go": "Go",
            "*.nix": "Nix",
            "*.sol": "Solidity",
            "*.java": "Java",
            "*.cpp": "C++",
            "*.c": "C",
            "*.zig": "Zig",
            "*.svelte": "Svelte",
            "*.vue": "Vue",
        }

        for pattern, language in language_indicators.items():
            files = list(path.rglob(pattern))
            # Filter out ignored directories
            files = [f for f in files if not any(
                ignored in f.parts for ignored in IGNORED_DIRS
            )]
            if files:
                languages.add(language)

        # Check for config files
        if (path / "Cargo.toml").exists():
            languages.add("Rust")
        if (path / "package.json").exists():
            languages.add("JavaScript")
        if (path / "pyproject.toml").exists() or (path / "setup.py").exists():
            languages.add("Python")
        if (path / "go.mod").exists():
            languages.add("Go")
        if (path / "flake.nix").exists():
            languages.add("Nix")

        return list(languages)

    def _extract_description(self, path: Path) -> str:
        """Extract project description from README."""
        readme_files = ["README.md", "README.rst", "README.txt", "README"]

        for readme_name in readme_files:
            readme_path = path / readme_name
            if readme_path.exists():
                try:
                    content = readme_path.read_text()
                    # Extract first paragraph after title
                    lines = content.split("\n")
                    description_lines = []
                    in_description = False

                    for line in lines:
                        # Skip title lines
                        if line.startswith("#"):
                            in_description = True
                            continue
                        # Skip empty lines at start
                        if in_description and line.strip():
                            description_lines.append(line.strip())
                            if len(" ".join(description_lines)) > 200:
                                break

                    return " ".join(description_lines)[:300]
                except Exception:
                    pass

        return ""

    def _get_last_commit_time(self, path: Path) -> Optional[datetime]:
        """Get the timestamp of the last git commit."""
        if not (path / ".git").exists():
            return None

        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ct"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0 and result.stdout.strip():
                timestamp = int(result.stdout.strip())
                return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except Exception:
            pass

        return None

    def _calculate_initial_health(self, path: Path) -> float:
        """Calculate initial health score for a project."""
        score = 50.0  # Start at 50%

        # Has README? +10
        if any((path / f).exists() for f in ["README.md", "README.rst", "README"]):
            score += 10

        # Has tests? +15
        if (path / "tests").exists() or (path / "test").exists():
            score += 15

        # Has CI? +10
        if (path / ".github" / "workflows").exists() or (path / ".gitlab-ci.yml").exists():
            score += 10

        # Has flake.nix? +5 (reproducible)
        if (path / "flake.nix").exists():
            score += 5

        # Has docs? +10
        if (path / "docs").exists():
            score += 10

        return min(100.0, score)

    def _determine_status(self, project: Project) -> ProjectStatus:
        """Determine project status based on activity."""
        if not project.last_commit:
            return ProjectStatus.UNKNOWN

        days_since_commit = (
            datetime.now(timezone.utc) - project.last_commit
        ).days

        if days_since_commit < 30:
            return ProjectStatus.ACTIVE
        elif days_since_commit < 90:
            return ProjectStatus.MAINTENANCE
        elif days_since_commit < 365:
            return ProjectStatus.DEPRECATED
        else:
            return ProjectStatus.ARCHIVED

    def _collect_metadata(self, path: Path) -> Dict[str, Any]:
        """Collect additional metadata about the project."""
        metadata = {}

        # Check for Nix flake
        flake_path = path / "flake.nix"
        if flake_path.exists():
            metadata["has_flake"] = True

        # Check for Docker
        if (path / "Dockerfile").exists() or (path / "docker-compose.yml").exists():
            metadata["has_docker"] = True

        # Check for Justfile
        if (path / "justfile").exists() or (path / "Justfile").exists():
            metadata["has_justfile"] = True

        # Count files
        try:
            file_count = sum(1 for _ in path.rglob("*") if _.is_file())
            metadata["file_count"] = file_count
        except Exception:
            metadata["file_count"] = 0

        return metadata

    def collect_intelligence(self, project: Project) -> int:
        """Run all collectors on a project."""
        total_items = 0

        for collector in self.collectors:
            try:
                items = collector.collect(project)
                for item in items:
                    self.cerebro.add_intelligence(item)
                    total_items += 1
            except Exception as e:
                logger.error(f"Collector {collector.__class__.__name__} failed: {e}")

        logger.info(f"Collected {total_items} intelligence items from {project.name}")
        return total_items

    def full_scan_with_intelligence(self) -> Dict[str, Any]:
        """
        Perform a full scan with intelligence collection.

        Returns scan statistics.
        """
        stats = {
            "projects_found": 0,
            "intelligence_collected": 0,
            "errors": 0,
            "duration_seconds": 0,
        }

        start_time = datetime.now(timezone.utc)

        # Scan for projects
        projects = self.scan(full_scan=True)
        stats["projects_found"] = len(projects)

        # Collect intelligence from each project
        for project in projects:
            try:
                items = self.collect_intelligence(project)
                stats["intelligence_collected"] += items
            except Exception as e:
                logger.error(f"Failed to collect intel from {project.name}: {e}")
                stats["errors"] += 1

        # Save state
        self.cerebro.save()

        end_time = datetime.now(timezone.utc)
        stats["duration_seconds"] = (end_time - start_time).total_seconds()

        logger.info(
            f"Full scan complete: {stats['projects_found']} projects, "
            f"{stats['intelligence_collected']} intel items, "
            f"{stats['errors']} errors, "
            f"{stats['duration_seconds']:.1f}s"
        )

        return stats
