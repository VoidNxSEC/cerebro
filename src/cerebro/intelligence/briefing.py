"""
Briefing Generator

Generates intelligence briefings in various formats:
- Daily briefings
- Project reports
- Threat assessments
- Executive summaries
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum
import json
import logging

from .core import (
    CerebroIntelligence,
    IntelligenceItem,
    IntelligenceType,
    ThreatLevel,
    Project,
)
from .analyzer import IntelligenceAnalyzer

logger = logging.getLogger("cerebro.briefing")


class BriefingType(str, Enum):
    """Types of intelligence briefings."""
    DAILY = "daily"
    WEEKLY = "weekly"
    THREAT = "threat"
    PROJECT = "project"
    EXECUTIVE = "executive"


class BriefingGenerator:
    """Generates intelligence briefings."""

    def __init__(self, cerebro: CerebroIntelligence):
        self.cerebro = cerebro
        self.analyzer = IntelligenceAnalyzer(cerebro)

    def generate(
        self,
        briefing_type: BriefingType = BriefingType.DAILY,
        project_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a briefing of the specified type."""
        generators = {
            BriefingType.DAILY: self._generate_daily,
            BriefingType.WEEKLY: self._generate_weekly,
            BriefingType.THREAT: self._generate_threat,
            BriefingType.PROJECT: lambda: self._generate_project(project_name),
            BriefingType.EXECUTIVE: self._generate_executive,
        }

        generator = generators.get(briefing_type, self._generate_daily)
        return generator()

    def _generate_daily(self) -> Dict[str, Any]:
        """Generate daily intelligence briefing."""
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)

        briefing = {
            "type": BriefingType.DAILY.value,
            "classification": "INTERNAL",
            "timestamp": now.isoformat(),
            "period": {
                "start": yesterday.isoformat(),
                "end": now.isoformat(),
            },
            "summary": "",
            "ecosystem_status": {},
            "key_developments": [],
            "alerts": [],
            "action_items": [],
        }

        # Get ecosystem status
        status = self.cerebro.get_ecosystem_status()
        briefing["ecosystem_status"] = {
            "total_projects": status.total_projects,
            "active_projects": status.active_projects,
            "health_score": self.cerebro.calculate_health_score(),
        }

        # Get recent intelligence
        all_intel = list(self.cerebro._intelligence.values())
        recent_intel = [
            i for i in all_intel
            if i.timestamp >= yesterday
        ]

        # Key developments (commits, new docs, etc.)
        for item in recent_intel[:10]:
            briefing["key_developments"].append({
                "type": item.type.value,
                "title": item.title,
                "source": item.source,
                "threat_level": item.threat_level.value,
            })

        # Alerts
        briefing["alerts"] = self.cerebro.get_alerts()

        # Generate summary
        briefing["summary"] = self._generate_summary(briefing)

        return briefing

    def _generate_weekly(self) -> Dict[str, Any]:
        """Generate weekly intelligence briefing."""
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        # Run ecosystem analysis
        ecosystem_analysis = self.analyzer.analyze_ecosystem()

        briefing = {
            "type": BriefingType.WEEKLY.value,
            "classification": "INTERNAL",
            "timestamp": now.isoformat(),
            "period": {
                "start": week_ago.isoformat(),
                "end": now.isoformat(),
            },
            "ecosystem_analysis": ecosystem_analysis,
            "project_summaries": [],
            "trends": [],
            "recommendations": [],
        }

        # Generate project summaries
        for project in self.cerebro.list_projects()[:10]:
            analysis = self.analyzer.analyze_project(project)
            briefing["project_summaries"].append({
                "name": project.name,
                "health_score": analysis["health_score"],
                "status": analysis["status"],
                "insights": analysis["insights"][:3],
            })

        # Sort by health score (lowest first - need attention)
        briefing["project_summaries"].sort(key=lambda x: x["health_score"])

        return briefing

    def _generate_threat(self) -> Dict[str, Any]:
        """Generate threat assessment briefing."""
        now = datetime.now(timezone.utc)

        briefing = {
            "type": BriefingType.THREAT.value,
            "classification": "CONFIDENTIAL",
            "timestamp": now.isoformat(),
            "threat_level": ThreatLevel.INFO.value,
            "critical_threats": [],
            "high_threats": [],
            "medium_threats": [],
            "mitigations": [],
        }

        # Categorize threats
        for item in self.cerebro._intelligence.values():
            threat_data = {
                "id": item.id,
                "title": item.title,
                "source": item.source,
                "related_projects": item.related_projects,
            }

            if item.threat_level == ThreatLevel.CRITICAL:
                briefing["critical_threats"].append(threat_data)
            elif item.threat_level == ThreatLevel.HIGH:
                briefing["high_threats"].append(threat_data)
            elif item.threat_level == ThreatLevel.MEDIUM:
                briefing["medium_threats"].append(threat_data)

        # Set overall threat level
        if briefing["critical_threats"]:
            briefing["threat_level"] = ThreatLevel.CRITICAL.value
        elif briefing["high_threats"]:
            briefing["threat_level"] = ThreatLevel.HIGH.value
        elif briefing["medium_threats"]:
            briefing["threat_level"] = ThreatLevel.MEDIUM.value

        return briefing

    def _generate_project(self, project_name: Optional[str]) -> Dict[str, Any]:
        """Generate project-specific briefing."""
        if not project_name:
            return {"error": "Project name required"}

        project = self.cerebro.get_project(project_name)
        if not project:
            return {"error": f"Project not found: {project_name}"}

        now = datetime.now(timezone.utc)
        analysis = self.analyzer.analyze_project(project)

        briefing = {
            "type": BriefingType.PROJECT.value,
            "classification": "INTERNAL",
            "timestamp": now.isoformat(),
            "project": {
                "name": project.name,
                "path": str(project.path),
                "languages": project.languages,
                "status": analysis["status"],
                "health_score": analysis["health_score"],
            },
            "analysis": analysis,
            "intelligence": [],
        }

        # Get project-specific intelligence
        intel_items = self.cerebro.query_intelligence(
            query="",
            projects=[project_name],
            limit=50,
        )

        for item in intel_items:
            briefing["intelligence"].append({
                "type": item.type.value,
                "title": item.title,
                "threat_level": item.threat_level.value,
                "tags": item.tags,
            })

        return briefing

    def _generate_executive(self) -> Dict[str, Any]:
        """Generate executive summary briefing."""
        now = datetime.now(timezone.utc)
        ecosystem_analysis = self.analyzer.analyze_ecosystem()

        briefing = {
            "type": BriefingType.EXECUTIVE.value,
            "classification": "INTERNAL",
            "timestamp": now.isoformat(),
            "headline": "",
            "key_metrics": {},
            "risk_assessment": {},
            "strategic_recommendations": [],
        }

        # Key metrics
        briefing["key_metrics"] = {
            "total_projects": ecosystem_analysis["total_projects"],
            "ecosystem_health": ecosystem_analysis.get("ecosystem_health", 0),
            "healthy_projects": ecosystem_analysis["health_distribution"]["healthy"],
            "projects_at_risk": ecosystem_analysis["health_distribution"]["at_risk"],
        }

        # Risk assessment
        total = ecosystem_analysis["total_projects"]
        if total > 0:
            risk_percentage = (
                ecosystem_analysis["health_distribution"]["at_risk"] +
                ecosystem_analysis["health_distribution"]["critical"]
            ) / total * 100
        else:
            risk_percentage = 0

        briefing["risk_assessment"] = {
            "overall_risk": "HIGH" if risk_percentage > 30 else "MEDIUM" if risk_percentage > 10 else "LOW",
            "risk_percentage": round(risk_percentage, 1),
        }

        # Strategic recommendations
        if ecosystem_analysis["health_distribution"]["critical"] > 0:
            briefing["strategic_recommendations"].append(
                "URGENT: Address critical projects requiring immediate attention"
            )
        if ecosystem_analysis["health_distribution"]["at_risk"] > 3:
            briefing["strategic_recommendations"].append(
                "Multiple projects at risk - consider resource reallocation"
            )

        # Generate headline
        health = briefing["key_metrics"]["ecosystem_health"]
        if health >= 70:
            briefing["headline"] = "Ecosystem Status: HEALTHY"
        elif health >= 50:
            briefing["headline"] = "Ecosystem Status: NEEDS ATTENTION"
        else:
            briefing["headline"] = "Ecosystem Status: AT RISK"

        return briefing

    def _generate_summary(self, briefing: Dict[str, Any]) -> str:
        """Generate a text summary for the briefing."""
        status = briefing.get("ecosystem_status", {})
        total = status.get("total_projects", 0)
        active = status.get("active_projects", 0)
        health = status.get("health_score", 0)
        alerts = len(briefing.get("alerts", []))
        developments = len(briefing.get("key_developments", []))

        return (
            f"Daily briefing for ~/arch ecosystem. "
            f"{total} projects tracked ({active} active). "
            f"Ecosystem health: {health:.1f}%. "
            f"{developments} key developments, {alerts} alerts."
        )

    def to_markdown(self, briefing: Dict[str, Any]) -> str:
        """Convert briefing to Markdown format."""
        lines = []
        briefing_type = briefing.get("type", "unknown")

        # Header
        lines.append(f"# CEREBRO Intelligence Briefing")
        lines.append(f"**Type:** {briefing_type.upper()}")
        lines.append(f"**Classification:** {briefing.get('classification', 'INTERNAL')}")
        lines.append(f"**Generated:** {briefing.get('timestamp', 'N/A')}")
        lines.append("")

        # Summary
        if "summary" in briefing:
            lines.append("## Summary")
            lines.append(briefing["summary"])
            lines.append("")

        # Headline (executive)
        if "headline" in briefing:
            lines.append(f"## {briefing['headline']}")
            lines.append("")

        # Ecosystem Status
        if "ecosystem_status" in briefing:
            lines.append("## Ecosystem Status")
            status = briefing["ecosystem_status"]
            lines.append(f"- Total Projects: {status.get('total_projects', 0)}")
            lines.append(f"- Active Projects: {status.get('active_projects', 0)}")
            lines.append(f"- Health Score: {status.get('health_score', 0):.1f}%")
            lines.append("")

        # Key Developments
        if briefing.get("key_developments"):
            lines.append("## Key Developments")
            for dev in briefing["key_developments"][:10]:
                level_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢",
                    "info": "🔵",
                }.get(dev.get("threat_level", "info"), "🔵")
                lines.append(f"- {level_emoji} **{dev['title']}** ({dev['source']})")
            lines.append("")

        # Alerts
        if briefing.get("alerts"):
            lines.append("## Alerts")
            for alert in briefing["alerts"]:
                lines.append(f"- ⚠️ {alert.get('message', str(alert))}")
            lines.append("")

        # Project Summaries
        if briefing.get("project_summaries"):
            lines.append("## Project Summaries")
            for proj in briefing["project_summaries"]:
                health = proj.get("health_score", 0)
                emoji = "✅" if health >= 70 else "⚠️" if health >= 40 else "❌"
                lines.append(f"### {emoji} {proj['name']}")
                lines.append(f"- Health: {health}%")
                lines.append(f"- Status: {proj.get('status', 'unknown')}")
                if proj.get("insights"):
                    lines.append("- Insights:")
                    for insight in proj["insights"]:
                        lines.append(f"  - {insight}")
                lines.append("")

        return "\n".join(lines)

    def to_json(self, briefing: Dict[str, Any]) -> str:
        """Convert briefing to JSON format."""
        return json.dumps(briefing, indent=2, default=str)
