"""
CEREBRO Project Registry

Automatically scans and indexes all projects in ~/arch.
Maintains a registry of projects with metadata, health status, and relationships.
"""

from .scanner import ProjectScanner
from .indexer import KnowledgeIndexer

__all__ = [
    "ProjectScanner",
    "KnowledgeIndexer",
]
