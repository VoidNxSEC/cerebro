"""
Phantom Core GCP - Unified Google Cloud Platform integrations
"""

from .auth import get_credentials, get_project_id, validate_setup
from .datastores import DataStoreManager
from .search import VertexAISearch
from .billing import BillingAuditor
from .dialogflow import DialogflowCXManager

__all__ = [
    "get_credentials",
    "get_project_id",
    "validate_setup",
    "DataStoreManager",
    "VertexAISearch",
    "BillingAuditor",
    "DialogflowCXManager",
]
