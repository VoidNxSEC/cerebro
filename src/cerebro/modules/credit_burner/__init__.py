"""
Credit Burner Module

Programmatically consume GCP promotional credits through validated APIs
with complete financial auditing.
"""

from .audit import audit_credits
from .loadtest import run_loadtest

__all__ = ["audit_credits", "run_loadtest"]
