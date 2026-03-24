"""
CEREBRO API

FastAPI-based REST API for the Cerebro Intelligence System.
Provides endpoints for:
- Project registry
- Intelligence queries
- Briefings
- System status
- Real-time updates (WebSocket)
"""

from .server import create_app, app

__all__ = ["create_app", "app"]
