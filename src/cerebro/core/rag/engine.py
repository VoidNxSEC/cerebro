import json
import logging
import os
import re
from pathlib import Path
from typing import Any, ClassVar
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from cerebro.core.rag.embeddings import EmbeddingSystem
from cerebro.interfaces.llm import LLMProvider
from cerebro.interfaces.vector_store import VectorSearchResult, VectorStoreProvider
from cerebro.providers.llamacpp import LlamaCppProvider
from cerebro.providers.openai_compatible import OpenAICompatibleProvider
from cerebro.providers.vector_store_factory import (
    build_vector_store_provider,
    supported_vector_store_aliases,
)
from cerebro.settings import get_settings

logger = logging.getLogger("cerebro.engine")


class DocumentSchema(BaseModel):
    id: str
    title: str = Field(..., max_length=255)
    content: str = Field(..., max_length=32000) # Limite rígido de contexto
    repo: str
    source: str
    
    @field_validator('content')
    def block_prompt_injection_signatures(cls, v):
        # 1. Regex de heurística rápida contra injeções comuns
        suspicious_patterns = [
            r"(?i)ignore all previous instructions",
            r"(?i)system prompt:",
            r"<\|im_start\|>", # Tentativa de quebrar tokens do LLM
            r"\[INST\]"
        ]
        for pattern in suspicious_patterns:
            if re.search(pattern, v):
                raise ValueError(f"Payload suspeito detectado (Prompt Injection signature)")
        
        # 2. Sanitização léxica (remover null bytes e caracteres de controle não imprimíveis)
        v = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', v)
        return v.strip()


class RigorousRAGEngine:
    """
    High-Precision RAG Engine (CEREBRO).

    Uses dependency injection with pluggable LLM and Vector Store providers.
    Defaults to a fully local stack: llama.cpp + ChromaDB.
    """

    LLM_PROVIDER_ALIASES: ClassVar[dict[str, str]] = {
        "llamacpp": "llamacpp",
        "llama.cpp": "llamacpp",
        "local-llm": "llamacpp",
        "openai-compatible": "openai-compatible",
        "openai-compatible-api": "openai-compatible",
        "local-openai": "openai-compatible",
        "vertex-ai": "vertex-ai",
        "vertexai": "vertex-ai",
        "gcp-vertex-ai": "vertex-ai",
        "anthropic": "anthropic",
        "claude": "anthropic",
        "groq": "groq",
        "gemini": "gemini",
        "google-gemini": "gemini",
        "azure": "azure",
        "azure-openai": "azure",
    }
    LLM_PROVIDER_CLASS_NAMES: ClassVar[dict[str, str]] = {
        "LlamaCppProvider": "llamacpp",
        "OpenAICompatibleProvider": "openai-compatible",
        "VertexAILLMProvider": "vertex-ai",
        "AnthropicProvider": "anthropic",
        "GroqProvider": "groq",
        "GeminiProvider": "gemini",
        "AzureOpenAIProvider": "azure",
    }

    def __init__(
        self,
        llm_provider: LLMProvider | None = None,
        vector_store_provider: VectorStoreProvider | None = None,
        data_store_id: str | None = None,
        location: str = "global",
        persist_directory: str | None = None,
        vector_store_namespace: str | None = None,
        vector_store_collection_name: str | None = None,
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
        settings = get_settings()

        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = location
        self.data_store_id = data_store_id or os.getenv("DATA_STORE_ID")
        self.persist_directory = (
            persist_directory or settings.vector_store_persist_directory
        )
        self.vector_store_namespace = (
            vector_store_namespace or settings.vector_store_namespace
        )
        self.vector_store_collection_name = (
            vector_store_collection_name or settings.vector_store_collection_name
        )
        self.default_provider_name = os.getenv("CEREBRO_LLM_PROVIDER", "llamacpp").strip().lower()

        if llm_provider is None:
            self.llm_provider = self._build_default_llm_provider()
        else:
            self.llm_provider = llm_provider

        if vector_store_provider is None:
            self.vector_store_provider = build_vector_store_provider(
                persist_directory=self.persist_directory,
                collection_name=self.vector_store_collection_name,
                namespace=self.vector_store_namespace,
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

        if provider_name == "anthropic":
            from cerebro.providers.anthropic import AnthropicProvider

            return AnthropicProvider()

        if provider_name == "groq":
            from cerebro.providers.groq import GroqProvider

            return GroqProvider()

        if provider_name == "gemini":
            from cerebro.providers.gemini import GeminiProvider

            return GeminiProvider()

        if provider_name == "azure":
            from cerebro.providers.azure import AzureOpenAIProvider

            return AzureOpenAIProvider()

        raise ValueError(
            f"Unsupported CEREBRO_LLM_PROVIDER value: {provider_name!r}. "
            "Expected one of: llamacpp, openai-compatible, vertex-ai, anthropic, groq, gemini, azure."
        )

    @classmethod
    def supported_llm_provider_aliases(cls) -> dict[str, str]:
        return dict(cls.LLM_PROVIDER_ALIASES)

    @staticmethod
    def supported_vector_store_provider_aliases() -> dict[str, str]:
        return supported_vector_store_aliases()

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

    def _get_llm_provider_name(self) -> str:
        return self.LLM_PROVIDER_CLASS_NAMES.get(
            self.llm_provider.__class__.__name__,
            self.llm_provider.__class__.__name__,
        )

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
                doc = self._normalize_document(raw, line_number)
                if doc is not None:
                    documents.append(doc)
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

        try:
            # Passa pela barreira do Pydantic
            clean_doc = DocumentSchema(
                id=document_id,
                title=title,
                content=content,
                repo=repo,
                source=source
            )
            # Monta o retorno seguro
            return clean_doc.model_dump() | metadata 
        except ValueError as e:
            logger.warning(f"Documento rejeitado no Ingest ({source}): {e}")
            return None # Dropa o documento

    def _ingest_local(self, jsonl_path: str) -> int:
        documents = self._load_documents(jsonl_path)
        if not documents:
            return 0

        self.vector_store_provider.initialize_schema()
        texts = [document["content"] for document in documents]
        embeddings = self._embed_document_texts(texts)
        return self.vector_store_provider.upsert_documents(
            documents,
            embeddings,
            namespace=self.vector_store_namespace,
        )

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

    def initialize_runtime(self) -> dict[str, Any]:
        """Initialize backend-specific runtime structures for the active vector store."""

        return self.vector_store_provider.initialize_schema()

    def run_smoke_test(
        self,
        *,
        write_check: bool = True,
        query_text: str = "cerebro smoke test",
    ) -> dict[str, Any]:
        """Run a lightweight write/read/delete validation against the active backend."""

        smoke_namespace = self.vector_store_namespace or "__cerebro_smoke__"
        steps: list[dict[str, Any]] = []
        smoke_doc_id: str | None = None
        smoke_source = f"cerebro://smoke/{uuid4().hex}"
        query_hits = 0
        error: str | None = None

        try:
            init_details = self.initialize_runtime()
            steps.append(
                {
                    "name": "initialize",
                    "ok": True,
                    "detail": f"backend={init_details.get('backend', self.vector_store_provider.backend_name)}",
                }
            )
        except Exception as exc:
            return {
                "healthy": False,
                "backend": self.vector_store_provider.backend_name,
                "namespace": smoke_namespace,
                "write_check": write_check,
                "query_hits": 0,
                "steps": [
                    {
                        "name": "initialize",
                        "ok": False,
                        "detail": str(exc),
                    }
                ],
                "error": str(exc),
            }

        provider_status = self.vector_store_provider.health_status()
        steps.append(
            {
                "name": "health",
                "ok": provider_status.healthy,
                "detail": provider_status.backend,
            }
        )

        try:
            document_count = self._get_local_document_count()
            steps.append(
                {
                    "name": "count",
                    "ok": True,
                    "detail": str(document_count),
                }
            )
        except Exception as exc:
            document_count = None
            error = str(exc)
            steps.append(
                {
                    "name": "count",
                    "ok": False,
                    "detail": str(exc),
                }
            )

        if write_check:
            try:
                smoke_doc_id = f"__cerebro_smoke__:{uuid4().hex}"
                smoke_content = (
                    "Cerebro smoke test document. "
                    "This payload validates write, read, and cleanup paths."
                )
                smoke_embedding = self._embed_document_texts([smoke_content])[0]
                self.vector_store_provider.upsert_documents(
                    [
                        {
                            "id": smoke_doc_id,
                            "title": "Cerebro Smoke Test",
                            "content": smoke_content,
                            "source": smoke_source,
                            "type": "smoke",
                            "namespace": smoke_namespace,
                        }
                    ],
                    [smoke_embedding],
                    namespace=smoke_namespace,
                )
                steps.append(
                    {
                        "name": "write",
                        "ok": True,
                        "detail": smoke_doc_id,
                    }
                )

                smoke_results = self.vector_store_provider.search(
                    self._embed_query_text(query_text),
                    top_k=3,
                    namespace=smoke_namespace,
                )
                query_hits = len(smoke_results)
                matched = any(result.id == smoke_doc_id for result in smoke_results)
                steps.append(
                    {
                        "name": "query",
                        "ok": matched,
                        "detail": f"hits={query_hits}",
                    }
                )
            except Exception as exc:
                error = str(exc)
                steps.append(
                    {
                        "name": "write_read_cycle",
                        "ok": False,
                        "detail": str(exc),
                    }
                )
            finally:
                if smoke_doc_id is not None:
                    try:
                        deleted = self.vector_store_provider.delete_documents(
                            [smoke_doc_id],
                            namespace=smoke_namespace,
                        )
                        steps.append(
                            {
                                "name": "cleanup",
                                "ok": deleted >= 1,
                                "detail": f"deleted={deleted}",
                            }
                        )
                    except Exception as exc:
                        error = error or str(exc)
                        steps.append(
                            {
                                "name": "cleanup",
                                "ok": False,
                                "detail": str(exc),
                            }
                        )

        healthy = all(step["ok"] for step in steps)
        return {
            "healthy": healthy,
            "backend": self.vector_store_provider.backend_name,
            "namespace": smoke_namespace,
            "write_check": write_check,
            "document_count": document_count,
            "query_hits": query_hits,
            "steps": steps,
            "error": error,
        }

    def migrate_documents(
        self,
        source_provider: VectorStoreProvider,
        *,
        source_namespace: str | None = None,
        batch_size: int = 200,
        clear_destination: bool = False,
    ) -> dict[str, Any]:
        """Copy stored documents and embeddings from a source backend into the active backend."""

        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero.")

        self.initialize_runtime()
        destination_count_before = self._get_local_document_count()
        source_count = source_provider.get_document_count(namespace=source_namespace)

        if clear_destination:
            self.vector_store_provider.clear(namespace=self.vector_store_namespace)

        migrated_count = 0
        batches = 0
        offset = 0
        while True:
            exported_batch = source_provider.export_documents(
                namespace=source_namespace,
                limit=batch_size,
                offset=offset,
            )
            if not exported_batch:
                break

            migrated_count += self.vector_store_provider.upsert_documents(
                [document.to_document() for document in exported_batch],
                [document.embedding for document in exported_batch],
                namespace=self.vector_store_namespace,
            )
            offset += len(exported_batch)
            batches += 1

        destination_count_after = self._get_local_document_count()
        return {
            "source_backend": source_provider.backend_name,
            "destination_backend": self.vector_store_provider.backend_name,
            "source_namespace": source_namespace,
            "destination_namespace": self.vector_store_namespace,
            "source_count": source_count,
            "migrated_count": migrated_count,
            "destination_count_before": destination_count_before,
            "destination_count_after": destination_count_after,
            "batch_size": batch_size,
            "batches": batches,
            "cleared_destination": clear_destination,
        }

    def _get_local_document_count(self) -> int:
        return self.vector_store_provider.get_document_count(
            namespace=self.vector_store_namespace,
        )

    def _retrieve_local_context(self, query: str, k: int) -> list[VectorSearchResult]:
        query_embedding = self._embed_query_text(query)
        raw_results = self.vector_store_provider.search(
            query_embedding,
            top_k=k,
            namespace=self.vector_store_namespace,
        )
        return [self._normalize_match(match) for match in raw_results]

    def _embed_document_texts(self, texts: list[str]) -> list[list[float]]:
        if self._embedding_system is not None:
            return self._embedding_system.embed(texts).vectors
        return self.llm_provider.embed_batch(texts)

    def _embed_query_text(self, query: str) -> list[float]:
        if self._embedding_system is not None:
            return self._embedding_system.embed_query(query)
        return self.llm_provider.embed(query)

    def _extract_citations(self, matches: list[VectorSearchResult]) -> list[str]:
        citations: list[str] = []
        for match in matches:
            metadata = match.metadata
            source = (
                match.source
                or metadata.get("source")
                or match.title
                or metadata.get("title")
                or match.id
                or "N/A"
            )
            citations.append(str(source))
        return citations

    def _normalize_match(self, match: VectorSearchResult | dict[str, Any]) -> VectorSearchResult:
        if isinstance(match, VectorSearchResult):
            return match

        metadata = dict(match.get("metadata", {}))
        return VectorSearchResult(
            id=str(match.get("id", metadata.get("id", ""))),
            content=str(match.get("content", match.get("text", ""))),
            metadata=metadata,
            score=float(match.get("score", match.get("similarity", 0.0))),
            distance=match.get("distance"),
            namespace=metadata.get("namespace"),
            title=match.get("title") or metadata.get("title"),
            source=match.get("source") or metadata.get("source"),
        )

    def _no_context_response(self, k: int, reason: str) -> dict[str, Any]:
        return {
            "answer": "No relevant information found in the indexed corpus.",
            "error": False,
            "metrics": {
                "avg_confidence": 0.0,
                "hit_rate_k": f"0/{k} (0%)" if k > 0 else "0%",
                "retrieved_docs": 0,
                "top_source": "N/A",
                "citations": [],
                "snippets": [],
                "cost_estimate_usd": 0.0,
                "grounded": False,
                "reason": reason,
                "vector_store_backend": self.vector_store_provider.backend_name,
            },
        }

    def get_runtime_status(self) -> dict[str, Any]:
        """Return structured runtime status for observability surfaces."""

        mode = "vertex-ai" if self._uses_vertex_backend() else "local"
        provider_status = self.vector_store_provider.health_status()
        backend_details = dict(provider_status.details)
        collection_name = backend_details.get("collection_name") or self.vector_store_collection_name
        namespace = backend_details.get("default_namespace") or self.vector_store_namespace
        document_count: int | None = None
        error: str | None = None

        if not self._uses_vertex_backend():
            try:
                document_count = self._get_local_document_count()
            except Exception as exc:
                provider_status = provider_status.__class__(
                    healthy=False,
                    backend=provider_status.backend,
                    details=backend_details,
                )
                error = str(exc)

        return {
            "healthy": provider_status.healthy,
            "mode": mode,
            "backend": provider_status.backend,
            "llm_provider": self._get_llm_provider_name(),
            "namespace": namespace,
            "collection_name": collection_name,
            "document_count": document_count,
            "details": backend_details,
            "error": error,
        }

    def query_with_metrics(self, query: str, k: int = 5) -> dict[str, Any]:
        """
        Execute a grounded query against the active backend.
        """
        try:
            matches: list[VectorSearchResult] = []
            if self._uses_vertex_backend():
                result = self.llm_provider.grounded_generate(
                    query=query,
                    context=[],
                    top_k=k,
                )
                citations = result.get("citations", [])
                retrieved = len(citations)
                hit_rate = (
                    f"{min(retrieved, k)}/{k} ({int(min(retrieved, k) / k * 100)}%)"
                    if k > 0
                    else "0%"
                )
                return {
                    "answer": result.get(
                        "answer",
                        "Could not generate a summary from the retrieved documents.",
                    ),
                    "error": False,
                    "metrics": {
                        "avg_confidence": result.get("confidence", 0.0),
                        "hit_rate_k": hit_rate,
                        "retrieved_docs": retrieved,
                        "top_source": citations[0] if citations else "N/A",
                        "citations": citations,
                        "snippets": result.get("snippets", []),
                        "cost_estimate_usd": result.get("cost_estimate", 0.0),
                        "grounded": bool(citations),
                        "vector_store_backend": self.vector_store_provider.backend_name,
                    },
                }

            document_count = self._get_local_document_count()
            if document_count <= 0:
                return self._no_context_response(
                    k,
                    "No indexed documents available for the active vector store.",
                )

            matches = self._retrieve_local_context(query, k)

            context = [match.content for match in matches if match.content]
            if not context:
                return self._no_context_response(
                    k,
                    "Retrieval returned no usable document content.",
                )
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
                    "grounded": bool(context),
                    "vector_store_backend": self.vector_store_provider.backend_name,
                },
            }
        except Exception as e:
            return {
                "answer": f"Error querying RAG engine: {e!s}",
                "error": True,
                "metrics": {
                    "hit_rate_k": "ERR",
                    "avg_confidence": 0.0,
                    "top_source": "N/A",
                    "grounded": False,
                    "vector_store_backend": self.vector_store_provider.backend_name,
                },
            }


def get_rag_runtime_status_snapshot() -> dict[str, Any]:
    """Build a best-effort RAG runtime status payload for API and CLI surfaces."""

    settings = get_settings()

    try:
        return RigorousRAGEngine().get_runtime_status()
    except Exception as exc:
        return {
            "healthy": False,
            "mode": "unavailable",
            "backend": settings.vector_store_provider.strip().lower(),
            "llm_provider": os.getenv("CEREBRO_LLM_PROVIDER", "llamacpp").strip().lower(),
            "namespace": settings.vector_store_namespace,
            "collection_name": settings.vector_store_collection_name,
            "document_count": None,
            "details": {},
            "error": str(exc),
        }
