"""
Intelligence Collectors

Specialized collectors for different types of intelligence:
- SIGINT: Signals (logs, metrics, events)
- HUMINT: Human (ADRs, documentation, decisions)
- OSINT: Open Source (code analysis, configs)
- TECHINT: Technical (dependencies, architecture)
"""

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from .core import (
    IntelligenceItem,
    IntelligenceType,
    ThreatLevel,
    Project,
    ProjectStatus,
)

logger = logging.getLogger("cerebro.collectors")


class BaseCollector:
    """Base class for intelligence collectors."""

    intel_type: IntelligenceType = IntelligenceType.OSINT

    def __init__(self, cerebro: "CerebroIntelligence"):
        self.cerebro = cerebro

    def collect(self, project: Project) -> List[IntelligenceItem]:
        """Collect intelligence from a project. Override in subclasses."""
        raise NotImplementedError

    def create_item(
        self,
        source: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        threat_level: ThreatLevel = ThreatLevel.INFO,
        tags: Optional[List[str]] = None,
        related_projects: Optional[List[str]] = None,
    ) -> IntelligenceItem:
        """Helper to create an intelligence item."""
        return IntelligenceItem(
            id=self.cerebro.generate_id(f"{source}:{title}:{content[:100]}"),
            type=self.intel_type,
            source=source,
            title=title,
            content=content,
            metadata=metadata or {},
            threat_level=threat_level,
            tags=tags or [],
            related_projects=related_projects or [],
        )


class SignalCollector(BaseCollector):
    """
    SIGINT Collector - Signals Intelligence

    Collects:
    - Git commit history
    - CI/CD logs
    - Build status
    - Runtime metrics
    """

    intel_type = IntelligenceType.SIGINT

    def collect(self, project: Project) -> List[IntelligenceItem]:
        """Collect signal intelligence from a project."""
        items = []

        # Collect git history
        git_items = self._collect_git_signals(project)
        items.extend(git_items)

        # Collect CI status
        ci_items = self._collect_ci_status(project)
        items.extend(ci_items)

        return items

    def _collect_git_signals(self, project: Project) -> List[IntelligenceItem]:
        """Collect signals from git history."""
        items = []
        git_dir = project.path / ".git"

        if not git_dir.exists():
            return items

        try:
            # Get recent commits
            result = subprocess.run(
                ["git", "log", "--oneline", "-n", "10", "--format=%H|%s|%ai|%an"],
                cwd=project.path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    parts = line.split("|")
                    if len(parts) >= 4:
                        commit_hash, message, date, author = parts[:4]

                        # Detect threat level from commit message
                        threat_level = ThreatLevel.INFO
                        if any(kw in message.lower() for kw in ["fix", "bug", "error"]):
                            threat_level = ThreatLevel.LOW
                        if any(kw in message.lower() for kw in ["security", "vuln", "cve"]):
                            threat_level = ThreatLevel.HIGH
                        if any(kw in message.lower() for kw in ["critical", "urgent", "hotfix"]):
                            threat_level = ThreatLevel.CRITICAL

                        items.append(self.create_item(
                            source=f"git:{project.name}",
                            title=f"Commit: {message[:50]}",
                            content=f"Commit {commit_hash[:8]} by {author}: {message}",
                            metadata={
                                "commit_hash": commit_hash,
                                "author": author,
                                "date": date,
                            },
                            threat_level=threat_level,
                            tags=["git", "commit"],
                            related_projects=[project.name],
                        ))

        except subprocess.TimeoutExpired:
            logger.warning(f"Git command timed out for {project.name}")
        except Exception as e:
            logger.error(f"Error collecting git signals from {project.name}: {e}")

        return items

    def _collect_ci_status(self, project: Project) -> List[IntelligenceItem]:
        """Collect CI/CD status."""
        items = []

        # Check for CI config files
        ci_files = [
            ".gitlab-ci.yml",
            ".github/workflows",
            "Jenkinsfile",
            ".circleci/config.yml",
        ]

        for ci_file in ci_files:
            ci_path = project.path / ci_file
            if ci_path.exists():
                items.append(self.create_item(
                    source=f"ci:{project.name}",
                    title=f"CI/CD detected: {ci_file}",
                    content=f"Project {project.name} has CI/CD configuration: {ci_file}",
                    metadata={"ci_type": ci_file},
                    tags=["ci", "devops"],
                    related_projects=[project.name],
                ))

        return items


class HumanIntelCollector(BaseCollector):
    """
    HUMINT Collector - Human Intelligence

    Collects:
    - ADRs (Architectural Decision Records)
    - Documentation
    - README files
    - Comments and decisions
    """

    intel_type = IntelligenceType.HUMINT

    def collect(self, project: Project) -> List[IntelligenceItem]:
        """Collect human intelligence from a project."""
        items = []

        # Collect ADRs
        adr_items = self._collect_adrs(project)
        items.extend(adr_items)

        # Collect documentation
        doc_items = self._collect_docs(project)
        items.extend(doc_items)

        # Collect README
        readme_items = self._collect_readme(project)
        items.extend(readme_items)

        return items

    def _collect_adrs(self, project: Project) -> List[IntelligenceItem]:
        """Collect ADRs from adr-ledger or project ADR directories."""
        items = []

        # Check for ADR directories
        adr_dirs = [
            project.path / "adr",
            project.path / "docs" / "adr",
            project.path / "docs" / "architecture",
        ]

        for adr_dir in adr_dirs:
            if not adr_dir.exists():
                continue

            for adr_file in adr_dir.rglob("*.md"):
                try:
                    content = adr_file.read_text()

                    # Extract title from first heading
                    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                    title = title_match.group(1) if title_match else adr_file.stem

                    # Extract ADR ID if present
                    adr_id_match = re.search(r"ADR[-_]?(\d+)", adr_file.name, re.IGNORECASE)
                    adr_id = adr_id_match.group(0) if adr_id_match else None

                    items.append(self.create_item(
                        source=f"adr:{project.name}",
                        title=f"ADR: {title[:60]}",
                        content=content[:2000],  # Limit content size
                        metadata={
                            "file": str(adr_file),
                            "adr_id": adr_id,
                        },
                        threat_level=ThreatLevel.INFO,
                        tags=["adr", "architecture", "decision"],
                        related_projects=[project.name],
                    ))

                except Exception as e:
                    logger.warning(f"Error reading ADR {adr_file}: {e}")

        return items

    def _collect_docs(self, project: Project) -> List[IntelligenceItem]:
        """Collect documentation files."""
        items = []
        docs_dir = project.path / "docs"

        if not docs_dir.exists():
            return items

        # Collect important docs
        important_patterns = [
            "ARCHITECTURE*.md",
            "DESIGN*.md",
            "API*.md",
            "GUIDE*.md",
            "ROADMAP*.md",
        ]

        for pattern in important_patterns:
            for doc_file in docs_dir.rglob(pattern):
                try:
                    content = doc_file.read_text()
                    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                    title = title_match.group(1) if title_match else doc_file.stem

                    items.append(self.create_item(
                        source=f"docs:{project.name}",
                        title=f"Doc: {title[:60]}",
                        content=content[:2000],
                        metadata={"file": str(doc_file)},
                        tags=["documentation"],
                        related_projects=[project.name],
                    ))
                except Exception as e:
                    logger.warning(f"Error reading doc {doc_file}: {e}")

        return items

    def _collect_readme(self, project: Project) -> List[IntelligenceItem]:
        """Collect README file."""
        items = []
        readme_files = ["README.md", "README.rst", "README.txt", "README"]

        for readme_name in readme_files:
            readme_path = project.path / readme_name
            if readme_path.exists():
                try:
                    content = readme_path.read_text()

                    # Extract description (usually first paragraph after title)
                    desc_match = re.search(r"^#.*?\n\n(.+?)(?:\n\n|\n#)", content, re.DOTALL)
                    description = desc_match.group(1).strip() if desc_match else content[:500]

                    items.append(self.create_item(
                        source=f"readme:{project.name}",
                        title=f"README: {project.name}",
                        content=content[:3000],
                        metadata={
                            "file": str(readme_path),
                            "description": description[:200],
                        },
                        tags=["readme", "overview"],
                        related_projects=[project.name],
                    ))
                    break  # Only need one README
                except Exception as e:
                    logger.warning(f"Error reading README {readme_path}: {e}")

        return items


class OpenSourceCollector(BaseCollector):
    """
    OSINT Collector - Open Source Intelligence

    Collects:
    - Source code analysis
    - Configuration files
    - API definitions
    - Schema files
    """

    intel_type = IntelligenceType.OSINT

    def collect(self, project: Project) -> List[IntelligenceItem]:
        """Collect open source intelligence from a project."""
        items = []

        # Collect code structure
        structure_items = self._collect_code_structure(project)
        items.extend(structure_items)

        # Collect configurations
        config_items = self._collect_configs(project)
        items.extend(config_items)

        # Collect API definitions
        api_items = self._collect_api_definitions(project)
        items.extend(api_items)

        return items

    def _collect_code_structure(self, project: Project) -> List[IntelligenceItem]:
        """Analyze code structure."""
        items = []

        # Count files by extension
        extensions: Dict[str, int] = {}
        for file_path in project.path.rglob("*"):
            if file_path.is_file() and not any(
                part.startswith(".") for part in file_path.parts
            ):
                ext = file_path.suffix.lower()
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1

        # Determine primary languages
        lang_map = {
            ".py": "Python",
            ".rs": "Rust",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".js": "JavaScript",
            ".jsx": "JavaScript",
            ".go": "Go",
            ".nix": "Nix",
            ".sol": "Solidity",
            ".java": "Java",
            ".cpp": "C++",
            ".c": "C",
        }

        languages = []
        for ext, count in sorted(extensions.items(), key=lambda x: -x[1])[:5]:
            if ext in lang_map:
                languages.append(lang_map[ext])

        if languages:
            items.append(self.create_item(
                source=f"structure:{project.name}",
                title=f"Code Structure: {project.name}",
                content=f"Primary languages: {', '.join(languages)}. File counts: {json.dumps(dict(list(extensions.items())[:10]))}",
                metadata={
                    "languages": languages,
                    "file_counts": dict(list(extensions.items())[:20]),
                    "total_files": sum(extensions.values()),
                },
                tags=["structure", "languages"],
                related_projects=[project.name],
            ))

        return items

    def _collect_configs(self, project: Project) -> List[IntelligenceItem]:
        """Collect configuration files."""
        items = []

        config_files = [
            ("flake.nix", "Nix Flake"),
            ("pyproject.toml", "Python Project"),
            ("Cargo.toml", "Rust Project"),
            ("package.json", "Node.js Project"),
            ("go.mod", "Go Module"),
            ("docker-compose.yml", "Docker Compose"),
            ("Dockerfile", "Docker"),
            (".env.example", "Environment Config"),
        ]

        for config_name, config_type in config_files:
            config_path = project.path / config_name
            if config_path.exists():
                try:
                    content = config_path.read_text()

                    items.append(self.create_item(
                        source=f"config:{project.name}",
                        title=f"Config: {config_type}",
                        content=content[:1500],
                        metadata={
                            "file": config_name,
                            "config_type": config_type,
                        },
                        tags=["config", config_type.lower().replace(" ", "-")],
                        related_projects=[project.name],
                    ))
                except Exception as e:
                    logger.warning(f"Error reading config {config_path}: {e}")

        return items

    def _collect_api_definitions(self, project: Project) -> List[IntelligenceItem]:
        """Collect API definitions."""
        items = []

        api_patterns = [
            ("**/openapi*.yaml", "OpenAPI"),
            ("**/openapi*.json", "OpenAPI"),
            ("**/swagger*.yaml", "Swagger"),
            ("**/swagger*.json", "Swagger"),
            ("**/*.proto", "Protobuf"),
            ("**/schema*.graphql", "GraphQL"),
        ]

        for pattern, api_type in api_patterns:
            for api_file in project.path.glob(pattern):
                if ".git" in str(api_file):
                    continue
                try:
                    content = api_file.read_text()
                    items.append(self.create_item(
                        source=f"api:{project.name}",
                        title=f"API: {api_type} - {api_file.name}",
                        content=content[:2000],
                        metadata={
                            "file": str(api_file),
                            "api_type": api_type,
                        },
                        tags=["api", api_type.lower()],
                        related_projects=[project.name],
                    ))
                except Exception as e:
                    logger.warning(f"Error reading API file {api_file}: {e}")

        return items


class TechIntelCollector(BaseCollector):
    """
    TECHINT Collector - Technical Intelligence

    Collects:
    - Dependencies analysis
    - Security vulnerabilities
    - Architecture patterns
    - Test coverage
    """

    intel_type = IntelligenceType.TECHINT

    def collect(self, project: Project) -> List[IntelligenceItem]:
        """Collect technical intelligence from a project."""
        items = []

        # Collect dependencies
        dep_items = self._collect_dependencies(project)
        items.extend(dep_items)

        # Collect test information
        test_items = self._collect_test_info(project)
        items.extend(test_items)

        return items

    def _collect_dependencies(self, project: Project) -> List[IntelligenceItem]:
        """Analyze project dependencies."""
        items = []
        dependencies = []

        # Python dependencies
        pyproject = project.path / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib
                content = pyproject.read_text()
                data = tomllib.loads(content)
                deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
                dependencies.extend([f"py:{k}" for k in deps.keys() if k != "python"])
            except Exception:
                pass

        # Node dependencies
        package_json = project.path / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                deps = data.get("dependencies", {})
                dependencies.extend([f"npm:{k}" for k in deps.keys()])
            except Exception:
                pass

        # Rust dependencies
        cargo_toml = project.path / "Cargo.toml"
        if cargo_toml.exists():
            try:
                content = cargo_toml.read_text()
                dep_match = re.findall(r'^\s*(\w[\w-]*)\s*=', content, re.MULTILINE)
                dependencies.extend([f"cargo:{d}" for d in dep_match[:20]])
            except Exception:
                pass

        if dependencies:
            items.append(self.create_item(
                source=f"deps:{project.name}",
                title=f"Dependencies: {project.name}",
                content=f"Found {len(dependencies)} dependencies: {', '.join(dependencies[:20])}",
                metadata={
                    "dependencies": dependencies,
                    "count": len(dependencies),
                },
                tags=["dependencies", "security"],
                related_projects=[project.name],
            ))

        return items

    def _collect_test_info(self, project: Project) -> List[IntelligenceItem]:
        """Collect test information."""
        items = []

        # Check for test directories/files
        test_patterns = [
            "tests/",
            "test/",
            "spec/",
            "*_test.py",
            "test_*.py",
            "*.test.ts",
            "*.spec.ts",
        ]

        test_files = []
        for pattern in test_patterns:
            if "/" in pattern:
                test_dir = project.path / pattern.rstrip("/")
                if test_dir.exists():
                    test_files.extend(list(test_dir.rglob("*")))
            else:
                test_files.extend(list(project.path.rglob(pattern)))

        if test_files:
            items.append(self.create_item(
                source=f"tests:{project.name}",
                title=f"Tests: {project.name}",
                content=f"Found {len(test_files)} test files",
                metadata={
                    "test_count": len(test_files),
                    "has_tests": True,
                },
                tags=["testing", "quality"],
                related_projects=[project.name],
            ))

        return items
