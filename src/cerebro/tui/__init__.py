"""
Cerebro TUI - Text User Interface for Cerebro Intelligence System.

Built with Textual for rich, interactive terminal experience.
"""

__all__ = ["CerebroApp"]


def get_app():
    """Lazy import of CerebroApp to avoid loading textual at module import time."""
    from .app import CerebroApp
    return CerebroApp
