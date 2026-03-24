"""
Intelligence Analyzer

Analyzes collected intelligence to:
- Identify patterns and trends
- Detect anomalies
- Generate insights
- Calculate health scores
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter
import logging

from .core import (
    CerebroIntelligence,
    IntelligenceItem,
    IntelligenceType,
    ThreatLevel,
    Project,
    ProjectStatus,
)

logger = logging.getLogger("cerebro.analyzer")


class IntelligenceAnalyzer:
    """Analyzes intelligence to extract insights."""

    def __init__(self, cerebro: CerebroIntelligence):
        self.cerebro = cerebro

    def analyze_project(self, project: Project) -> Dict[str, Any]:
        """Perform comprehensive analysis of a project."""
        analysis = {
            "project": project.name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health_score": 0.0,
            "status": ProjectStatus.UNKNOWN.value,
            "insights": [],
            "recommendations": [],
            "metrics": {},
        }

        # Calculate health score
        health_score, health_factors = self._calculate_health_score(project)
        analysis["health_score"] = health_score
        analysis["metrics"]["health_factors"] = health_factors

        # Determine status
        analysis["status"] = self._determine_status(project, health_score).value

        # Generate insights
        analysis["insights"] = self._generate_insights(project)

        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(
            project, health_factors
        )

        return analysis

    def _calculate_health_score(self, project: Project) -> Tuple[float, Dict[str, float]]:
        """
        Calculate project health score (0-100).

        Factors:
        - Recent activity (30%)
        - Documentation (20%)
        - Test coverage (20%)
        - CI/CD presence (15%)
        - Security (15%)
        """
        factors = {
            "activity": 0.0,
            "documentation": 0.0,
            "testing": 0.0,
            "ci_cd": 0.0,
            "security": 0.0,
        }

        # Get project intelligence
        intel_items = self.cerebro.query_intelligence(
            query="",  # Get all
            projects=[project.name],
            limit=1000,
        )

        # Activity score (based on recent commits)
        git_items = [i for i in intel_items if "git" in i.tags]
        if git_items:
            # Check if there are recent commits (within 30 days)
            recent_commits = [
                i for i in git_items
                if i.timestamp > datetime.now(timezone.utc) - timedelta(days=30)
            ]
            factors["activity"] = min(100, len(recent_commits) * 10)

        # Documentation score
        doc_items = [i for i in intel_items if "documentation" in i.tags or "readme" in i.tags]
        adr_items = [i for i in intel_items if "adr" in i.tags]
        factors["documentation"] = min(100, (len(doc_items) * 15) + (len(adr_items) * 20))

        # Testing score
        test_items = [i for i in intel_items if "testing" in i.tags]
        factors["testing"] = 80 if test_items else 0

        # CI/CD score
        ci_items = [i for i in intel_items if "ci" in i.tags or "devops" in i.tags]
        factors["ci_cd"] = 100 if ci_items else 0

        # Security score (starts at 100, decreases with issues)
        security_issues = [i for i in intel_items if i.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]]
        factors["security"] = max(0, 100 - len(security_issues) * 20)

        # Calculate weighted score
        weights = {
            "activity": 0.30,
            "documentation": 0.20,
            "testing": 0.20,
            "ci_cd": 0.15,
            "security": 0.15,
        }

        total_score = sum(factors[k] * weights[k] for k in factors)
        return round(total_score, 1), factors

    def _determine_status(self, project: Project, health_score: float) -> ProjectStatus:
        """Determine project status based on analysis."""
        if health_score >= 70:
            return ProjectStatus.ACTIVE
        elif health_score >= 40:
            return ProjectStatus.MAINTENANCE
        elif health_score >= 20:
            return ProjectStatus.DEPRECATED
        else:
            return ProjectStatus.ARCHIVED

    def _generate_insights(self, project: Project) -> List[str]:
        """Generate insights about the project."""
        insights = []

        intel_items = self.cerebro.query_intelligence(
            query="",
            projects=[project.name],
            limit=500,
        )

        # Language insights
        structure_items = [i for i in intel_items if "structure" in i.tags]
        for item in structure_items:
            langs = item.metadata.get("languages", [])
            if langs:
                insights.append(f"Primary languages: {', '.join(langs)}")

        # ADR insights
        adr_items = [i for i in intel_items if "adr" in i.tags]
        if adr_items:
            insights.append(f"Has {len(adr_items)} architectural decision records")

        # Security insights
        critical_items = [i for i in intel_items if i.threat_level == ThreatLevel.CRITICAL]
        if critical_items:
            insights.append(f"ALERT: {len(critical_items)} critical issues detected")

        return insights

    def _generate_recommendations(
        self, project: Project, health_factors: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations to improve project health."""
        recommendations = []

        if health_factors["documentation"] < 50:
            recommendations.append("Add or improve documentation (README, guides)")

        if health_factors["testing"] < 50:
            recommendations.append("Add or improve test coverage")

        if health_factors["ci_cd"] < 50:
            recommendations.append("Set up CI/CD pipeline")

        if health_factors["activity"] < 30:
            recommendations.append("Project appears inactive - consider archiving or updating")

        if health_factors["security"] < 70:
            recommendations.append("Address security issues detected in commits")

        return recommendations

    def analyze_ecosystem(self) -> Dict[str, Any]:
        """Analyze the entire ecosystem."""
        projects = self.cerebro.list_projects()

        ecosystem_analysis = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_projects": len(projects),
            "health_distribution": {
                "healthy": 0,      # 70+
                "needs_attention": 0,  # 40-69
                "at_risk": 0,      # 20-39
                "critical": 0,     # <20
            },
            "language_distribution": Counter(),
            "top_issues": [],
            "recommendations": [],
        }

        for project in projects:
            # Analyze each project
            analysis = self.analyze_project(project)
            score = analysis["health_score"]

            if score >= 70:
                ecosystem_analysis["health_distribution"]["healthy"] += 1
            elif score >= 40:
                ecosystem_analysis["health_distribution"]["needs_attention"] += 1
            elif score >= 20:
                ecosystem_analysis["health_distribution"]["at_risk"] += 1
            else:
                ecosystem_analysis["health_distribution"]["critical"] += 1

            # Update project health
            project.health_score = score
            project.status = ProjectStatus(analysis["status"])

        # Calculate ecosystem health
        if projects:
            ecosystem_analysis["ecosystem_health"] = sum(
                p.health_score for p in projects
            ) / len(projects)
        else:
            ecosystem_analysis["ecosystem_health"] = 0

        return ecosystem_analysis

    def find_dependencies_graph(self) -> Dict[str, List[str]]:
        """Build a dependency graph between projects."""
        graph: Dict[str, List[str]] = {}
        projects = self.cerebro.list_projects()

        for project in projects:
            graph[project.name] = []

            # Check flake.nix for Nix dependencies
            flake_path = project.path / "flake.nix"
            if flake_path.exists():
                try:
                    content = flake_path.read_text()
                    for other_project in projects:
                        if other_project.name != project.name:
                            if other_project.name in content:
                                graph[project.name].append(other_project.name)
                except Exception:
                    pass

        return graph
