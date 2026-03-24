import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.cloud import storage
from google.api_core import exceptions

from cerebro.interfaces.llm import LLMProvider
from cerebro.interfaces.vector_store import VectorStoreProvider
from cerebro.providers.gcp.vertex_ai_llm import VertexAILLMProvider
from cerebro.providers.chroma.chroma_vector_store import ChromaVectorStoreProvider


class RigorousRAGEngine:
    """
    High-Precision RAG Engine (CEREBRO).

    Programmatic GenAI App Builder credit utilization via Discovery Engine.

    Uses dependency injection with pluggable LLM and Vector Store providers.
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        vector_store_provider: Optional[VectorStoreProvider] = None,
        data_store_id: Optional[str] = None,
        location: str = "global",
        persist_directory: str = "./data/vector_db"
    ):
        """
        Initialize RigorousRAGEngine with pluggable providers.
        
        Args:
            llm_provider: LLMProvider instance (defaults to VertexAILLMProvider)
            vector_store_provider: VectorStoreProvider instance (defaults to ChromaVectorStoreProvider)
            data_store_id: Discovery Engine data store ID
            location: GCP location
            persist_directory: Directory for vector store persistence
        """
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = location
        self.data_store_id = data_store_id or os.getenv("DATA_STORE_ID")
        self.persist_directory = persist_directory
        
        # Initialize providers with defaults if not provided
        if llm_provider is None:
            self.llm_provider = VertexAILLMProvider(
                project_id=self.project_id,
                location=self.location,
                data_store_id=self.data_store_id
            )
        else:
            self.llm_provider = llm_provider

        if vector_store_provider is None:
            self.vector_store_provider = ChromaVectorStoreProvider(
                persist_directory=persist_directory
            )
        else:
            self.vector_store_provider = vector_store_provider

    def ingest(self, jsonl_path: str) -> int:
        """
        Ingest via Discovery Engine (consumes GenAI App Builder credits).

        Flow: Local JSONL -> GCS -> Discovery Engine Import
        """
        if not self.project_id or not self.data_store_id:
            raise ValueError("GCP_PROJECT_ID and DATA_STORE_ID must be configured.")

        path = Path(jsonl_path)
        if not path.exists():
            raise FileNotFoundError(f"Artifacts not found: {jsonl_path}")

        print("\n🚀 Starting programmatic ingestion...")

        # 1. Upload to GCS (Staging)
        bucket_name = f"{self.project_id}-phantom-ingest"
        storage_client = storage.Client(project=self.project_id)

        try:
            bucket = storage_client.get_bucket(bucket_name)
        except exceptions.NotFound:
            print(f"🔨 Creating staging bucket: gs://{bucket_name}")
            bucket = storage_client.create_bucket(bucket_name)

        blob = bucket.blob(f"ingest/{path.name}")
        print(f"📤 Uploading {path.name} to gs://{bucket_name}/ingest/...")
        blob.upload_from_filename(str(path))

        gcs_uri = f"gs://{bucket_name}/ingest/{path.name}"

        # 2. Use LLM provider to import documents
        print(f"🔄 Requesting import to Data Store: {self.data_store_id}")
        operation_name = self.llm_provider.import_documents(gcs_uri)

        print(f"⏳ Operation started: {operation_name}")
        print("✅ Google is processing your documents in the background.")
        print("💡 Check status at: https://console.cloud.google.com/gen-app-builder/data-stores")

        # Returns the number of lines in the file
        with open(path, 'r') as f:
            return sum(1 for _ in f)

    def query_with_metrics(self, query: str, k: int = 5) -> Dict[str, Any]:
        """
        Execute Grounded Generation via Discovery Engine (consumes GenAI credits).
        """
        try:
            # Use LLM provider for grounded generation
            result = self.llm_provider.grounded_generate(
                query=query,
                context=[],  # Context comes from data store
                top_k=k
            )

            citations = result.get("citations", [])
            confidence = result.get("confidence", 0.0)
            retrieved = len(citations)
            hit_rate = f"{min(retrieved, k)}/{k} ({int(min(retrieved, k) / k * 100)}%)" if k > 0 else "0%"

            return {
                "answer": result.get("answer", "Could not generate a summary from the retrieved documents."),
                "error": False,
                "metrics": {
                    "avg_confidence": confidence,
                    "hit_rate_k": hit_rate,
                    "retrieved_docs": retrieved,
                    "top_source": citations[0] if citations else "N/A",
                    "citations": citations,
                    "snippets": result.get("snippets", []),
                    "cost_estimate_usd": result.get("cost_estimate", 0.0),
                },
            }
        except Exception as e:
            return {
                "answer": f"Error querying Discovery Engine: {str(e)}",
                "error": True,
                "metrics": {"hit_rate_k": "ERR", "avg_confidence": 0.0, "top_source": "N/A"},
            }
