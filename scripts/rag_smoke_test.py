#!/usr/bin/env python3
"""RAG prod-readiness smoke test: ChromaDB + LlamaCpp (no external deps)."""

import os
import shutil
import sys
from pathlib import Path

os.environ.setdefault("CEREBRO_VECTOR_STORE_PROVIDER", "chroma")

test_dir = Path("/tmp/cerebro_rag_smoke")
shutil.rmtree(test_dir, ignore_errors=True)
test_dir.mkdir()
os.environ.setdefault("CEREBRO_VECTOR_STORE_PERSIST_DIRECTORY", str(test_dir))

from cerebro.core.rag.engine import RigorousRAGEngine
from cerebro.providers.llamacpp import LlamaCppProvider
from cerebro.providers.vector_store_factory import build_vector_store_provider

vs = build_vector_store_provider()
llm = LlamaCppProvider()

print(f"  vector_store={vs.backend_name} healthy={vs.health_check()}")
print(f"  llm=llamacpp healthy={llm.health_check()}")

engine = RigorousRAGEngine(
    llm_provider=llm,
    vector_store_provider=vs,
    persist_directory=str(test_dir / "vdb"),
)

engine.initialize_runtime()
result = engine.run_smoke_test()

steps = [(s["name"], s["ok"]) for s in result["steps"]]
healthy = result["healthy"]
print(f"  smoke steps: {steps}")
print(f"  smoke healthy={healthy}")
print(f"  query_hits={result.get('query_hits', 0)}")

sys.exit(0 if healthy else 1)
