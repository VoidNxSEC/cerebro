"""
Credit Burner Module

Programmatically consume GCP promotional credits through validated APIs
with complete financial auditing.
"""

from .loadtest import run_loadtest
from .audit import audit_credits

__all__ = ["run_loadtest", "audit_credits"]
