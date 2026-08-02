"""
CEREBRO Intelligence System

The brain of the ecosystem - inspired by intelligence agencies.

Components:
- SIGINT: Signals Intelligence (logs, metrics, events)
- HUMINT: Human Intelligence (ADRs, documentation, decisions)
- OSINT: Open Source Intelligence (code analysis, configs)
- TECHINT: Technical Intelligence (dependencies, architecture)

This module provides centralized intelligence gathering, analysis,
and dissemination for the entire ~/arch ecosystem.
"""

from .analyzer import IntelligenceAnalyzer
from .briefing import BriefingGenerator
from .collectors import (
    HumanIntelCollector,
    OpenSourceCollector,
    SignalCollector,
    TechIntelCollector,
)
from .core import CerebroIntelligence

__all__ = [
    "BriefingGenerator",
    "CerebroIntelligence",
    "HumanIntelCollector",
    "IntelligenceAnalyzer",
    "OpenSourceCollector",
    "SignalCollector",
    "TechIntelCollector",
]
