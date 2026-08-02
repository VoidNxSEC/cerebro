"""
CEREBRO Project Registry

Automatically scans and indexes all projects in ~/arch.
Maintains a registry of projects with metadata, health status, and relationships.
"""

from .indexer import KnowledgeIndexer
from .scanner import ProjectScanner

__all__ = [
    "KnowledgeIndexer",
    "ProjectScanner",
]
