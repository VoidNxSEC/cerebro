"""
Vertex AI LLM Provider

Implements LLMProvider interface for Google Cloud Vertex AI.
Handles embeddings, text generation, and grounded generation with citations.
"""

import os
import time
from typing import Any, Dict, List, Optional

from google.cloud import discoveryengine_v1beta as discoveryengine
from google.api_core import exceptions
from google.auth import default

from phantom.interfaces.llm import LLMProvider
from phantom.core.gcp.search import VertexAISearch, GroundedResponse


class VertexAILLMProvider(LLMProvider):
    """
    Vertex AI LLM Provider
    
    Implements embeddings and grounded generation using Google Cloud Vertex AI
    and Discovery Engine services.
    """

    # Exponential backoff configuration for rate limits
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1.0
    MAX_BACKOFF = 32.0

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "global",
        data_store_id: Optional[str] = None,
    ):
        """
        Initialize Vertex AI LLM Provider.
        
        Args:
            project_id: GCP project ID (auto-detected if None)
            location: GCP location (default: global)
            data_store_id: Discovery Engine data store ID
        """
        if project_id is None:
            _, project_id = default()

        self.project_id = project_id
        self.location = location
        self.data_store_id = data_store_id or os.getenv("DATA_STORE_ID")

        # Initialize Vertex AI Search client for grounded generation
        if self.data_store_id:
            self.search_client = VertexAISearch(
                project_id=self.project_id,
                location=self.location,
                data_store_id=self.data_store_id
            )
        else:
            self.search_client = None

        # Initialize Discovery Engine client for document import
        client_options = None
        if location != "global":
            client_options = {"api_endpoint": f"{location}-discoveryengine.googleapis.com"}

        self.discovery_client = discoveryengine.DocumentServiceClient(
            client_options=client_options
        )

    def embed(self, text: str) -> List[float]:
        """
        Generate an embedding vector for the given text.
        
        Args:
            text: The text to embed
            
        Returns:
            A list of floats representing the embedding vector
        """
        # For now, use batch embedding with single item
        embeddings = self.embed_batch([text], batch_size=1)
        return embeddings[0] if embeddings else []

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 20
    ) -> List[List[float]]:
        """
        Generate embedding vectors for a batch of texts with exponential backoff.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process in each batch
            
        Returns:
            A list of embedding vectors
        """
        try:
            from langchain_google_vertexai import VertexAIEmbeddings
        except ImportError:
            raise ImportError(
                "langchain-google-vertexai is required for embeddings. "
                "Install with: pip install langchain-google-vertexai"
            )

        embeddings_model = VertexAIEmbeddings(
            model_name="text-embedding-004",
            project=self.project_id,
        )

        all_embeddings = []
        
        # Process in batches with exponential backoff
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            
            retries = 0
            backoff = self.INITIAL_BACKOFF
            
            while retries < self.MAX_RETRIES:
                try:
                    batch_embeddings = embeddings_model.embed_documents(batch)
                    all_embeddings.extend(batch_embeddings)
                    break
                except exceptions.ResourceExhausted:
                    if retries < self.MAX_RETRIES - 1:
                        print(f"⏳ Rate limited. Waiting {backoff}s before retry...")
                        time.sleep(backoff)
                        backoff = min(backoff * 2, self.MAX_BACKOFF)
                        retries += 1
                    else:
                        raise
                except Exception as e:
                    print(f"❌ Embedding error: {e}")
                    raise

        return all_embeddings

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text based on the given prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text
        """
        try:
            from langchain_google_vertexai import VertexAI
        except ImportError:
            raise ImportError(
                "langchain-google-vertexai is required for text generation. "
                "Install with: pip install langchain-google-vertexai"
            )

        llm = VertexAI(
            model_name="gemini-pro",
            project=self.project_id,
            **kwargs
        )

        return llm.invoke(prompt)

    def grounded_generate(
        self,
        query: str,
        context: List[str],
        top_k: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text grounded in provided context with citations.
        
        Uses Discovery Engine's grounded generation capability to ensure
        responses are grounded in the provided context.
        
        Args:
            query: The user query
            context: List of context documents (not used directly, uses data store)
            top_k: Number of top results to consider
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dictionary containing:
            - 'answer': The generated answer
            - 'citations': List of cited sources
            - 'confidence': Confidence score
            - 'cost_estimate': Estimated cost in USD
        """
        if not self.search_client:
            return {
                "answer": "❌ Error: DATA_STORE_ID not configured. Cannot perform grounded generation.",
                "citations": [],
                "confidence": 0.0,
                "cost_estimate": 0.0,
            }

        try:
            response: GroundedResponse = self.search_client.grounded_search(
                query,
                top_k=top_k
            )

            return {
                "answer": response.summary or "No answer could be generated from the available context.",
                "citations": response.citations,
                "snippets": response.snippets,
                "confidence": 1.0 if response.summary else 0.0,
                "cost_estimate": response.cost_estimate,
            }
        except Exception as e:
            return {
                "answer": f"❌ Error in grounded generation: {str(e)}",
                "citations": [],
                "confidence": 0.0,
                "cost_estimate": 0.0,
            }

    def health_check(self) -> bool:
        """
        Check if the provider is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Test Discovery Engine API connectivity
            if self.data_store_id:
                parent = (
                    f"projects/{self.project_id}/locations/{self.location}/"
                    f"collections/default_collection"
                )
                self.discovery_client.list_data_stores(parent=parent)
            
            return True
        except Exception as e:
            print(f"❌ Vertex AI health check failed: {e}")
            return False

    def import_documents(self, gcs_uri: str) -> str:
        """
        Import documents from GCS into the Discovery Engine data store.
        
        Args:
            gcs_uri: GCS URI of the JSONL file to import
            
        Returns:
            Operation name for tracking the import
        """
        if not self.data_store_id:
            raise ValueError("DATA_STORE_ID must be configured for document import")

        parent = (
            f"projects/{self.project_id}/locations/{self.location}/"
            f"collections/default_collection/dataStores/{self.data_store_id}/"
            f"branches/default_branch"
        )

        request = discoveryengine.ImportDocumentsRequest(
            parent=parent,
            gcs_source=discoveryengine.GcsSource(
                input_uris=[gcs_uri],
                data_schema="document"
            ),
            reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL
        )

        operation = self.discovery_client.import_documents(request=request)
        return operation.operation.name
