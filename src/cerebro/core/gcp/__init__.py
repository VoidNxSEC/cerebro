"""
Cerebro GCP integrations.

Optional Google Cloud adapters live here so the local-first core can remain
vendor-agnostic.
"""

from .auth import get_credentials, get_project_id, validate_setup
from .billing import BillingAuditor
from .datastores import DataStoreManager
from .dialogflow import DialogflowCXManager
from .search import VertexAISearch

__all__ = [
    "BillingAuditor",
    "DataStoreManager",
    "DialogflowCXManager",
    "VertexAISearch",
    "get_credentials",
    "get_project_id",
    "validate_setup",
]
