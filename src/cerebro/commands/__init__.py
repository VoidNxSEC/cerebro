"""
Cerebro Commands - Phase 2 CLI Integration

Migrated command modules from standalone scripts.
"""

try:
    from .gcp import gcp_app
except ImportError:
    gcp_app = None  # type: ignore[assignment]

try:
    from .strategy import strategy_app
except ImportError:
    strategy_app = None  # type: ignore[assignment]

try:
    from .content import content_app
except ImportError:
    content_app = None  # type: ignore[assignment]

try:
    from .testing import testing_app
except ImportError:
    testing_app = None  # type: ignore[assignment]

__all__ = [
    "gcp_app",
    "strategy_app",
    "content_app",
    "testing_app",
]
