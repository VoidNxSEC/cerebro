"""
cerebro.core.rag.chunker
─────────────────────────
Chunking estratégico com hierarquia parent_id.

O AST já extrai por função/classe — aqui adicionamos:
  1. parent_id linkando function → class → file
  2. ChunkStrategy por tipo de artefato
  3. Sliding window para docstrings/README longos

Isso resolve o "context expansion during retrieval":
quando você retrieva uma função, você pode puxar a classe pai
sem re-embedar — o link já está no metadata.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator


class ChunkStrategy(Enum):
    FUNCTION    = "function"    # Extração AST por função — granularidade cirúrgica
    CLASS       = "class"       # Extração AST por classe
    MODULE      = "module"      # Arquivo inteiro (pequenos)
    SLIDING     = "sliding"     # Docstrings longas, README
    SEMANTIC    = "semantic"    # Parágrafos coerentes (NLP-based)
    DEPENDENCY  = "dependency"  # Grafo de imports — phase 2


@dataclass
class Chunk:
    """
    Unidade atômica do RAG pipeline.

    parent_id cria uma árvore:
        file_chunk (MODULE)
          └─ class_chunk (CLASS)
               └─ method_chunk (FUNCTION)  ← você retrieva aqui
                    └─ mais específico...

    Isso permite context expansion: dado um FUNCTION chunk,
    você pode enriquecer o contexto puxando seu parent CLASS
    sem nova query ao vector store.
    """
    content: str
    metadata: dict
    chunk_type: ChunkStrategy

    # Gerado automaticamente se não fornecido
    id: str = field(default="")
    parent_id: str | None = None
    children_ids: list[str] = field(default_factory=list)

    # Embedding preenchido pelo EmbeddingSystem
    embedding: list[float] | None = None

    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()

    def _generate_id(self) -> str:
        """ID determinístico baseado em conteúdo + metadata."""
        key = f"{self.metadata.get('repo', '')}:{self.metadata.get('file', '')}:{self.content[:100]}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    @property
    def token_estimate(self) -> int:
        """Estimativa rápida de tokens sem tokenizer (4 chars ≈ 1 token)."""
        return len(self.content) // 4

    @property
    def is_code(self) -> bool:
        return self.chunk_type in (
            ChunkStrategy.FUNCTION,
            ChunkStrategy.CLASS,
            ChunkStrategy.MODULE,
            ChunkStrategy.DEPENDENCY,
        )

    def to_dict(self) -> dict:
        """Serialização para ChromaDB metadata."""
        return {
            "id":           self.id,
            "content":      self.content,
            "chunk_type":   self.chunk_type.value,
            "parent_id":    self.parent_id or "",
            "repo":         self.metadata.get("repo", ""),
            "file":         self.metadata.get("file", ""),
            "language":     self.metadata.get("language", ""),
            "line_start":   self.metadata.get("line_start", 0),
            "line_end":     self.metadata.get("line_end", 0),
            "has_docstring": bool(self.metadata.get("docstring")),
            "complexity":   self.metadata.get("complexity", 0),
            "token_estimate": self.token_estimate,
        }


# ─── Chunkers por estratégia ─────────────────────────────────────────────────

class ASTChunker:
    """
    Wraps o output do HermeticAnalyzer (JSONL artifacts) em Chunks.
    Não re-faz o parsing — só estrutura o que já foi extraído.
    """

    def from_artifact(self, artifact: dict, repo: str) -> list[Chunk]:
        """
        artifact: dict de uma linha do artifacts.jsonl
        Formato esperado: {"type": "function"|"class", "name": ..., "content": ..., ...}
        """
        chunks = []
        artifact_type = artifact.get("type", "function")

        if artifact_type == "class":
            class_chunk = self._make_class_chunk(artifact, repo)
            chunks.append(class_chunk)

            # Métodos da classe como filhos
            for method in artifact.get("methods", []):
                method_chunk = self._make_function_chunk(method, repo, parent_id=class_chunk.id)
                class_chunk.children_ids.append(method_chunk.id)
                chunks.append(method_chunk)

        elif artifact_type == "function":
            chunks.append(self._make_function_chunk(artifact, repo))

        return chunks

    def _make_class_chunk(self, artifact: dict, repo: str) -> Chunk:
        content = self._build_class_content(artifact)
        return Chunk(
            content=content,
            chunk_type=ChunkStrategy.CLASS,
            metadata={
                "repo":       repo,
                "file":       artifact.get("file", ""),
                "language":   artifact.get("language", ""),
                "line_start": artifact.get("line_start", 0),
                "line_end":   artifact.get("line_end", 0),
                "docstring":  artifact.get("docstring", ""),
                "name":       artifact.get("name", ""),
            },
        )

    def _make_function_chunk(self, artifact: dict, repo: str, parent_id: str | None = None) -> Chunk:
        content = self._build_function_content(artifact)
        return Chunk(
            content=content,
            chunk_type=ChunkStrategy.FUNCTION,
            parent_id=parent_id,
            metadata={
                "repo":       repo,
                "file":       artifact.get("file", ""),
                "language":   artifact.get("language", ""),
                "line_start": artifact.get("line_start", 0),
                "line_end":   artifact.get("line_end", 0),
                "docstring":  artifact.get("docstring", ""),
                "name":       artifact.get("name", ""),
                "complexity": artifact.get("complexity", 0),
            },
        )

    def _build_function_content(self, artifact: dict) -> str:
        """
        Constrói texto rico para embedding — não só o código bruto.
        Contexto semântico ajuda o modelo a entender o que a função FAZ.
        """
        parts = []
        if name := artifact.get("name"):
            parts.append(f"Function: {name}")
        if docstring := artifact.get("docstring"):
            parts.append(f"Description: {docstring}")
        if params := artifact.get("parameters"):
            parts.append(f"Parameters: {', '.join(params)}")
        if returns := artifact.get("return_type"):
            parts.append(f"Returns: {returns}")
        if code := artifact.get("content") or artifact.get("code"):
            parts.append(f"Code:\n{code}")
        return "\n".join(parts)

    def _build_class_content(self, artifact: dict) -> str:
        parts = []
        if name := artifact.get("name"):
            parts.append(f"Class: {name}")
        if docstring := artifact.get("docstring"):
            parts.append(f"Description: {docstring}")
        if bases := artifact.get("bases"):
            parts.append(f"Inherits: {', '.join(bases)}")
        if methods := artifact.get("methods"):
            method_names = [m.get("name", "") for m in methods]
            parts.append(f"Methods: {', '.join(method_names)}")
        return "\n".join(parts)


class SlidingWindowChunker:
    """
    Para textos longos: README, docstrings extensas, comentários.
    Sliding window com overlap para preservar contexto nas bordas.
    """

    def __init__(
        self,
        chunk_size: int = 512,   # tokens estimados
        overlap: int = 64,       # overlap em tokens
        min_chunk_size: int = 50,
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size

    def chunk(self, text: str, metadata: dict) -> list[Chunk]:
        # Estimativa: 4 chars ≈ 1 token
        char_size    = self.chunk_size * 4
        char_overlap = self.overlap * 4

        chunks = []
        start = 0
        parent_id = None

        # Primeiro chunk é "parent" dos seguintes (para context expansion)
        while start < len(text):
            end = min(start + char_size, len(text))

            # Tenta quebrar em fronteira de frase
            if end < len(text):
                last_period = text.rfind(".", start, end)
                last_newline = text.rfind("\n", start, end)
                break_point = max(last_period, last_newline)
                if break_point > start + (char_size // 2):
                    end = break_point + 1

            content = text[start:end].strip()
            if len(content) < self.min_chunk_size * 4:
                break

            chunk = Chunk(
                content=content,
                chunk_type=ChunkStrategy.SLIDING,
                parent_id=parent_id,
                metadata={**metadata, "char_start": start, "char_end": end},
            )

            if parent_id is None:
                parent_id = chunk.id  # primeiro chunk é pai

            chunks.append(chunk)
            start = end - char_overlap

        return chunks


class MarkdownChunker:
    """
    Chunking por seção de Markdown — para README.md, docs, ADRs.
    Cada heading H1/H2 vira um chunk com parent_id hierárquico.
    """

    def chunk(self, text: str, metadata: dict) -> list[Chunk]:
        sections = re.split(r'\n(#{1,3} .+)\n', text)
        chunks = []
        h1_parent = None
        h2_parent = None

        for i, section in enumerate(sections):
            section = section.strip()
            if not section or len(section) < 20:
                continue

            level = len(section) - len(section.lstrip('#')) if section.startswith('#') else 0

            if level == 1:
                parent_id = None
                h1_parent = None  # será preenchido após criar o chunk
            elif level == 2:
                parent_id = h1_parent
            else:
                parent_id = h2_parent or h1_parent

            chunk = Chunk(
                content=section,
                chunk_type=ChunkStrategy.SEMANTIC,
                parent_id=parent_id,
                metadata={**metadata, "heading_level": level},
            )

            if level == 1:
                h1_parent = chunk.id
            elif level == 2:
                h2_parent = chunk.id

            chunks.append(chunk)

        return chunks


# ─── Chunker factory ─────────────────────────────────────────────────────────

def get_chunker(strategy: ChunkStrategy):
    """
    Factory para selecionar chunker por estratégia.

    chunker = get_chunker(ChunkStrategy.SLIDING)
    chunks = chunker.chunk(text, metadata)
    """
    return {
        ChunkStrategy.FUNCTION:   ASTChunker(),
        ChunkStrategy.CLASS:      ASTChunker(),
        ChunkStrategy.SLIDING:    SlidingWindowChunker(),
        ChunkStrategy.SEMANTIC:   MarkdownChunker(),
    }.get(strategy, SlidingWindowChunker())
