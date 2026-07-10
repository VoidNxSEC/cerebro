"""
LLMProvider Interface

Defines the abstract base class for Language Model providers.
Implementations should handle:
- Embeddings generation
- Text generation/completion
- Grounded generation with citations
"""

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """
    Abstract base class for Language Model providers.
    
    Implementations must provide methods for:
    - Generating embeddings from text
    - Generating text completions
    - Grounded generation with source citations
    """

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """
        Generate an embedding vector for the given text.
        
        Args:
            text: The text to embed
            
        Returns:
            A list of floats representing the embedding vector
        """

    @abstractmethod
    def embed_batch(self, texts: list[str], batch_size: int = 20) -> list[list[float]]:
        """
        Generate embedding vectors for a batch of texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process in each batch
            
        Returns:
            A list of embedding vectors
        """

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text based on the given prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text
        """

    @abstractmethod
    def grounded_generate(
        self,
        query: str,
        context: list[str],
        top_k: int = 5,
        **kwargs
    ) -> dict[str, Any]:
        """
        Generate text grounded in provided context with citations.
        
        Args:
            query: The user query
            context: List of context documents to ground the response in
            top_k: Number of top results to consider
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dictionary containing:
            - 'answer': The generated answer
            - 'citations': List of cited sources
            - 'confidence': Confidence score
            - 'cost_estimate': Estimated cost in USD
        """

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the provider is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
