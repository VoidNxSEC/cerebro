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

from .server import app, create_app

__all__ = ["app", "create_app"]
