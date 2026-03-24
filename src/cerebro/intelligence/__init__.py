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

from .core import CerebroIntelligence
from .collectors import (
    SignalCollector,
    HumanIntelCollector,
    OpenSourceCollector,
    TechIntelCollector,
)
from .analyzer import IntelligenceAnalyzer
from .briefing import BriefingGenerator

__all__ = [
    "CerebroIntelligence",
    "SignalCollector",
    "HumanIntelCollector",
    "OpenSourceCollector",
    "TechIntelCollector",
    "IntelligenceAnalyzer",
    "BriefingGenerator",
]
