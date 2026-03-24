"""
Phantom Core - Framework core modules
"""

__version__ = "2.0.0"

from . import utils

try:
    from . import gcp
except ImportError:
    gcp = None  # type: ignore[assignment]

try:
    from . import extraction
except ImportError:
    extraction = None  # type: ignore[assignment]

try:
    from . import rag
except ImportError:
    rag = None  # type: ignore[assignment]

__all__ = ["gcp", "extraction", "rag", "utils"]
