"""
Pytest configuration for integration tests.

This conftest imports all shared fixtures and utilities so they're available
to all integration test modules.
"""

from __future__ import annotations

# Import all fixtures from the shared integration conftest
# This makes them available to all test files in this directory
from conftest_integration import (
    INTEGRATION,
    integration_namespace,
    requires_backend,
    sample_documents_fixture,
    sample_embeddings_fixture,
    skip_if_no_connection,
)

__all__ = [
    "INTEGRATION",
    "integration_namespace",
    "requires_backend",
    "sample_documents_fixture",
    "sample_embeddings_fixture",
    "skip_if_no_connection",
]
