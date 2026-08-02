"""
GCP (Google Cloud Platform) Providers

Implementations for Google Cloud services:
- Vertex AI for LLM and embeddings
- Discovery Engine for grounded generation
"""

try:
    from .vertex_ai_llm import VertexAILLMProvider

    __all__ = ["VertexAILLMProvider"]
except ImportError:
    # google-cloud-discoveryengine is a Poetry dep; gracefully skip when not installed
    __all__ = []
