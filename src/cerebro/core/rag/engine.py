import json
import os
from pathlib import Path
from typing import Any

from cerebro.core.rag.embeddings import EmbeddingSystem
from cerebro.interfaces.llm import LLMProvider
from cerebro.interfaces.vector_store import VectorStoreProvider
from cerebro.providers.chroma.chroma_vector_store import ChromaVectorStoreProvider
from cerebro.providers.llamacpp import LlamaCppProvider
from cerebro.providers.openai_compatible import OpenAICompatibleProvider


class RigorousRAGEngine:
    """
    High-Precision RAG Engine (CEREBRO).

    Uses dependency injection with pluggable LLM and Vector Store providers.
    Defaults to a fully local stack: llama.cpp + ChromaDB.
    """

    LLM_PROVIDER_ALIASES = {
        "llamacpp": "llamacpp",
        "llama.cpp": "llamacpp",
        "local-llm": "llamacpp",
        "openai-compatible": "openai-compatible",
        "openai-compatible-api": "openai-compatible",
        "local-openai": "openai-compatible",
        "vertex-ai": "vertex-ai",
        "vertexai": "vertex-ai",
        "gcp-vertex-ai": "vertex-ai",
    }

    def __init__(
        self,
        llm_provider: LLMProvider | None = None,
        vector_store_provider: VectorStoreProvider | None = None,
        data_store_id: str | None = None,
        location: str = "global",
        persist_directory: str = "./data/vector_db",
    ):
        """
        Initialize RigorousRAGEngine with pluggable providers.

        Args:
            llm_provider: LLMProvider instance (defaults to local provider)
            vector_store_provider: VectorStoreProvider instance
            data_store_id: Discovery Engine data store ID for Vertex mode
            location: GCP location for Vertex mode
            persist_directory: Directory for vector store persistence
        """
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = location
        self.data_store_id = data_store_id or os.getenv("DATA_STORE_ID")
        self.persist_directory = persist_directory
        self.default_provider_name = os.getenv("CEREBRO_LLM_PROVIDER", "llamacpp").strip().lower()

        if llm_provider is None:
            self.llm_provider = self._build_default_llm_provider()
        else:
            self.llm_provider = llm_provider

        if vector_store_provider is None:
            self.vector_store_provider = ChromaVectorStoreProvider(
                persist_directory=persist_directory,
            )
        else:
            self.vector_store_provider = vector_store_provider

        # Use the dedicated EmbeddingSystem (Jina code-aware → MPNET → MiniLM) for
        # local paths. Vertex AI path delegates embeddings to the LLM provider.
        if not self._uses_vertex_backend():
            self._embedding_system: EmbeddingSystem | None = EmbeddingSystem(strategy="code")
        else:
            self._embedding_system = None

    def _build_default_llm_provider(self) -> LLMProvider:
        """
        Build the default LLM provider from environment configuration.

        Supported canonical values for CEREBRO_LLM_PROVIDER:
        - llamacpp (default)
        - openai-compatible
        - vertex-ai
        """
        provider_name = self._resolve_llm_provider_alias(self.default_provider_name)

        if provider_name == "llamacpp":
            return LlamaCppProvider()

        if provider_name == "openai-compatible":
            return OpenAICompatibleProvider()

        if provider_name == "vertex-ai":
            from cerebro.providers.gcp.vertex_ai_llm import VertexAILLMProvider

            return VertexAILLMProvider(
                project_id=self.project_id,
                location=self.location,
                data_store_id=self.data_store_id,
            )

        raise ValueError(
            f"Unsupported CEREBRO_LLM_PROVIDER value: {provider_name!r}. "
            "Expected one of: llamacpp, openai-compatible, vertex-ai."
        )

    @classmethod
    def supported_llm_provider_aliases(cls) -> dict[str, str]:
        return dict(cls.LLM_PROVIDER_ALIASES)

    @classmethod
    def _resolve_llm_provider_alias(cls, provider_name: str) -> str:
        resolved = cls.LLM_PROVIDER_ALIASES.get(provider_name)
        if resolved:
            return resolved

        supported = ", ".join(
            f"{alias}->{canonical}" for alias, canonical in sorted(cls.LLM_PROVIDER_ALIASES.items())
        )
        raise ValueError(
            f"Unsupported CEREBRO_LLM_PROVIDER value: {provider_name!r}. "
            f"Supported aliases: {supported}."
        )

    def _uses_vertex_backend(self) -> bool:
        return self.llm_provider.__class__.__name__ == "VertexAILLMProvider"

    def _load_documents(self, jsonl_path: str) -> list[dict[str, Any]]:
        path = Path(jsonl_path)
        if not path.exists():
            raise FileNotFoundError(f"Artifacts not found: {jsonl_path}")

        documents: list[dict[str, Any]] = []
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                raw = json.loads(stripped)
                documents.append(self._normalize_document(raw, line_number))
        return documents

    def _normalize_document(self, raw: dict[str, Any], line_number: int) -> dict[str, Any]:
        payload = raw.get("jsonData", raw)
        if isinstance(payload, str):
            payload = json.loads(payload)
        elif not isinstance(payload, dict):
            payload = {}

        title = str(payload.get("title") or raw.get("title") or f"document-{line_number}")
        content = str(payload.get("content") or raw.get("content") or raw.get("text") or "")
        repo = str(payload.get("repo") or raw.get("repo") or "unknown")
        source = str(payload.get("source") or raw.get("source") or f"{repo}/{title}")
        document_id = str(raw.get("id") or payload.get("id") or f"{repo}:{title}:{line_number}")

        metadata: dict[str, Any] = {
            "title": title,
            "repo": repo,
            "source": source,
        }
        for key, value in payload.items():
            if key in {"content", "text", "id"}:
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                metadata[key] = value
            else:
                metadata[key] = json.dumps(value, ensure_ascii=True)

        return {
            "id": document_id,
            "content": content,
            "title": title,
            "repo": repo,
            "source": source,
            **metadata,
        }

    def _ingest_local(self, jsonl_path: str) -> int:
        documents = self._load_documents(jsonl_path)
        if not documents:
            return 0

        texts = [document["content"] for document in documents]
        if self._embedding_system is not None:
            embeddings = self._embedding_system.embed(texts).vectors
        else:
            embeddings = self.llm_provider.embed_batch(texts)
        return self.vector_store_provider.add_documents(documents, embeddings)

    def _ingest_vertex(self, jsonl_path: str) -> int:
        if not self.project_id or not self.data_store_id:
            raise ValueError("GCP_PROJECT_ID and DATA_STORE_ID must be configured for Vertex ingestion.")

        try:
            from google.api_core import exceptions
            from google.cloud import storage
        except ImportError as exc:
            raise ImportError("Vertex ingestion requires google-cloud-storage and google-api-core.") from exc

        path = Path(jsonl_path)
        if not path.exists():
            raise FileNotFoundError(f"Artifacts not found: {jsonl_path}")

        bucket_name = f"{self.project_id}-cerebro-ingest"
        storage_client = storage.Client(project=self.project_id)

        try:
            bucket = storage_client.get_bucket(bucket_name)
        except exceptions.NotFound:
            bucket = storage_client.create_bucket(bucket_name)

        blob = bucket.blob(f"ingest/{path.name}")
        blob.upload_from_filename(str(path))

        gcs_uri = f"gs://{bucket_name}/ingest/{path.name}"
        operation_name = self.llm_provider.import_documents(gcs_uri)
        print(f"Vertex import started: {operation_name}")

        with path.open(encoding="utf-8") as handle:
            return sum(1 for _ in handle)

    def ingest(self, jsonl_path: str) -> int:
        """
        Ingest artifacts into the active backend.

        Local providers embed documents and store them in ChromaDB.
        Vertex AI remains available as an explicit option.
        """
        if self._uses_vertex_backend():
            return self._ingest_vertex(jsonl_path)
        return self._ingest_local(jsonl_path)

    def _has_local_documents(self) -> bool:
        try:
            return self.vector_store_provider.get_document_count() > 0
        except Exception:
            return False

    def _retrieve_local_context(self, query: str, k: int) -> list[dict[str, Any]]:
        if self._embedding_system is not None:
            query_embedding = self._embedding_system.embed_query(query)
        else:
            query_embedding = self.llm_provider.embed(query)
        return self.vector_store_provider.search(query_embedding, top_k=k)

    def _extract_citations(self, matches: list[dict[str, Any]]) -> list[str]:
        citations: list[str] = []
        for match in matches:
            metadata = match.get("metadata", {})
            source = (
                metadata.get("source")
                or match.get("source")
                or metadata.get("title")
                or match.get("id")
                or "N/A"
            )
            citations.append(str(source))
        return citations

    def query_with_metrics(self, query: str, k: int = 5) -> dict[str, Any]:
        """
        Execute a grounded query against the active backend.
        """
        try:
            matches: list[dict[str, Any]] = []
            if self._has_local_documents():
                matches = self._retrieve_local_context(query, k)

            context = [match.get("content", "") for match in matches if match.get("content")]
            result = self.llm_provider.grounded_generate(
                query=query,
                context=context,
                top_k=k,
            )

            citations = self._extract_citations(matches) if matches else result.get("citations", [])
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
                    "snippets": result.get("snippets", context[:k]),
                    "cost_estimate_usd": result.get("cost_estimate", 0.0),
                },
            }
        except Exception as e:
            return {
                "answer": f"Error querying RAG engine: {e!s}",
                "error": True,
                "metrics": {"hit_rate_k": "ERR", "avg_confidence": 0.0, "top_source": "N/A"},
            }
