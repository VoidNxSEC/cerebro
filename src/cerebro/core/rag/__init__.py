"""
Phantom Core RAG - Retrieval-Augmented Generation server
"""

# Server is imported dynamically to avoid heavy dependencies
from . import server

__all__ = ["server"]
