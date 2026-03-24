"""
GCP (Google Cloud Platform) Providers

Implementations for Google Cloud services:
- Vertex AI for LLM and embeddings
- Discovery Engine for grounded generation
"""

from .vertex_ai_llm import VertexAILLMProvider

__all__ = ["VertexAILLMProvider"]
