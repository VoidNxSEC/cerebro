#!/usr/bin/env python3
"""
Cerebro RAG Performance Benchmark
===================================
Measures GPU/CPU performance across:
  - Embedding latency (Jina Code v2 / MPNET / MiniLM) per batch size
  - GPU vs CPU speedup ratio (when CUDA available)
  - RAG query latency: p50, p95, p99 (n=100 synthetic queries)
  - Document ingest throughput (docs/s, chunks/s)
  - Reranker latency per batch size
  - Memory footprint: RAM (psutil) + VRAM (pynvml if GPU available)

Output:
  JSON → docs/benchmarks/benchmark-YYYY-MM-DD.json
  Markdown table → docs/benchmarks/README.md (appended)

Usage:
  python scripts/benchmark.py [--quick] [--gpu-only] [--output PATH]
  # or via CLI:
  cerebro benchmark run [--quick] [--output PATH]
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─── Hardware detection ───────────────────────────────────────────────────────

def _detect_hardware() -> dict[str, Any]:
    info: dict[str, Any] = {"cuda_available": False, "devices": []}

    try:
        import torch
        info["cuda_available"] = torch.cuda.is_available()
        if info["cuda_available"]:
            info["cuda_device_count"] = torch.cuda.device_count()
            info["cuda_device_name"] = torch.cuda.get_device_name(0)
            try:
                total_vram = torch.cuda.get_device_properties(0).total_memory
                info["vram_total_gb"] = round(total_vram / (1024 ** 3), 2)
            except Exception:
                pass
        info["torch_version"] = torch.__version__
    except ImportError:
        info["torch_available"] = False

    try:
        import psutil
        mem = psutil.virtual_memory()
        info["ram_total_gb"] = round(mem.total / (1024 ** 3), 2)
        info["ram_available_gb"] = round(mem.available / (1024 ** 3), 2)
        info["cpu_count"] = psutil.cpu_count(logical=False)
        info["cpu_count_logical"] = psutil.cpu_count(logical=True)
    except ImportError:
        pass

    try:
        import platform
        info["python_version"] = platform.python_version()
        info["os"] = platform.system()
    except Exception:
        pass

    return info


def _get_ram_usage_mb() -> float:
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024 ** 2)
    except ImportError:
        return -1.0


def _get_vram_usage_mb() -> float:
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated(0) / (1024 ** 2)
    except Exception:
        pass
    return -1.0


# ─── Embedding benchmark ──────────────────────────────────────────────────────

EMBEDDING_MODELS = [
    ("jina-code-v2", "jinaai/jina-embeddings-v2-base-code"),
    ("mpnet", "sentence-transformers/all-mpnet-base-v2"),
    ("minilm", "sentence-transformers/all-MiniLM-L6-v2"),
]

SAMPLE_TEXTS = [
    "def compute_embeddings(texts, model, batch_size=32): return model.encode(texts)",
    "How does the RAG engine handle embedding model fallback when CUDA is unavailable?",
    "class RigorousRAGEngine: def __init__(self, llm_provider, vector_store): ...",
    "SELECT id, content, embedding FROM vector_documents WHERE namespace = $1 LIMIT 100",
    "The cross-encoder reranker uses MS-MARCO MiniLM-L6-v2 with adaptive model selection.",
    "async function handleCerebroRagQuery(args) { return fetch('/rag/query', { method: 'POST' }); }",
    "HNSW indexing provides approximate nearest-neighbor search with O(log n) query time.",
    "Jina embeddings support 8192-token context windows for long code files.",
]


def _benchmark_embedding_model(
    model_name: str,
    model_id: str,
    batch_sizes: list[int],
    device: str,
    n_repeats: int = 3,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "model": model_name,
        "model_id": model_id,
        "device": device,
        "batch_results": [],
        "ram_before_mb": _get_ram_usage_mb(),
        "vram_before_mb": _get_vram_usage_mb(),
    }

    try:
        from sentence_transformers import SentenceTransformer

        t_load = time.perf_counter()
        model = SentenceTransformer(model_id, device=device)
        load_ms = round((time.perf_counter() - t_load) * 1000)
        result["load_ms"] = load_ms
        result["ram_after_mb"] = _get_ram_usage_mb()
        result["vram_after_mb"] = _get_vram_usage_mb()
        result["ram_delta_mb"] = round(result["ram_after_mb"] - result["ram_before_mb"], 1)

        for bs in batch_sizes:
            texts = (SAMPLE_TEXTS * ((bs // len(SAMPLE_TEXTS)) + 1))[:bs]
            latencies = []
            for _ in range(n_repeats):
                t0 = time.perf_counter()
                model.encode(texts, batch_size=bs, show_progress_bar=False)
                latencies.append((time.perf_counter() - t0) * 1000)

            result["batch_results"].append({
                "batch_size": bs,
                "avg_ms": round(statistics.mean(latencies), 1),
                "min_ms": round(min(latencies), 1),
                "max_ms": round(max(latencies), 1),
                "ms_per_doc": round(statistics.mean(latencies) / bs, 2),
            })

        del model
        gc.collect()
        try:
            import torch
            torch.cuda.empty_cache()
        except Exception:
            pass

    except Exception as exc:
        result["error"] = str(exc)

    return result


def benchmark_embeddings(
    batch_sizes: list[int],
    devices: list[str],
    n_repeats: int = 3,
) -> list[dict[str, Any]]:
    results = []
    for model_name, model_id in EMBEDDING_MODELS:
        for device in devices:
            print(f"  [{model_name}] device={device} ...", end=" ", flush=True)
            r = _benchmark_embedding_model(model_name, model_id, batch_sizes, device, n_repeats)
            status = "error" if "error" in r else "ok"
            print(status)
            results.append(r)
    return results


# ─── RAG query benchmark (via HTTP) ──────────────────────────────────────────

SYNTHETIC_QUERIES = [
    "How does the embedding fallback chain work?",
    "What is HNSW indexing and why is it used?",
    "Explain the reranker model selection strategy",
    "How does prompt injection filtering prevent attacks?",
    "What are the vector store backend options?",
    "How is namespace isolation implemented?",
    "What is the relevance score threshold?",
    "How does grounded generation prevent hallucinations?",
    "Describe the document chunking strategy",
    "How does the LLM provider factory pattern work?",
    "What embedding dimensions does MiniLM use?",
    "How is idempotent upsert implemented?",
    "What is the purpose of the CrossEncoderReranker?",
    "How does the AST analyzer extract code structure?",
    "What NATS topics does Cerebro publish to?",
    "How does the circuit breaker handle GCP rate limits?",
    "Explain the content hashing strategy for deduplication",
    "What is the difference between hot and cold knowledge tiers?",
    "How does the WebSocket subscription manager work?",
    "What is the role of the SubscriptionManager in real-time updates?",
]


def benchmark_rag_queries(
    api_url: str,
    n_queries: int = 100,
    timeout_s: float = 30.0,
) -> dict[str, Any]:
    import urllib.request
    import urllib.error

    latencies: list[float] = []
    errors = 0

    # Warm-up
    payload = json.dumps({"query": "warm-up query", "grounded": False, "limit": 3}).encode()
    req = urllib.request.Request(
        f"{api_url}/rag/query",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s):
            pass
    except Exception:
        return {"error": f"Cerebro not reachable at {api_url}"}

    queries = (SYNTHETIC_QUERIES * ((n_queries // len(SYNTHETIC_QUERIES)) + 1))[:n_queries]

    for q in queries:
        payload = json.dumps({"query": q, "grounded": False, "limit": 3}).encode()
        req = urllib.request.Request(
            f"{api_url}/rag/query",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=timeout_s):
                pass
            latencies.append((time.perf_counter() - t0) * 1000)
        except Exception:
            errors += 1
            latencies.append(timeout_s * 1000)

    if not latencies:
        return {"error": "No successful queries"}

    sorted_lat = sorted(latencies)
    n = len(sorted_lat)

    def pct(p: float) -> float:
        return round(sorted_lat[min(int(n * p), n - 1)], 1)

    return {
        "n_queries": n_queries,
        "errors": errors,
        "error_rate_pct": round(errors / n_queries * 100, 1),
        "p50_ms": pct(0.5),
        "p95_ms": pct(0.95),
        "p99_ms": pct(0.99),
        "min_ms": round(min(latencies), 1),
        "max_ms": round(max(latencies), 1),
        "avg_ms": round(statistics.mean(latencies), 1),
        "throughput_qps": round(n_queries / (sum(latencies) / 1000), 2),
    }


# ─── Ingest benchmark ─────────────────────────────────────────────────────────

def benchmark_ingest(api_url: str, n_docs: int = 50, timeout_s: float = 120.0) -> dict[str, Any]:
    import urllib.request

    docs = [
        {
            "id": f"bench_doc_{i}",
            "content": f"Benchmark document {i}: " + " ".join(SAMPLE_TEXTS),
            "metadata": {"source": "benchmark", "index": i},
        }
        for i in range(n_docs)
    ]
    payload = json.dumps({"documents": docs}).encode()
    req = urllib.request.Request(
        f"{api_url}/rag/ingest",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            result = json.loads(resp.read())
        elapsed = time.perf_counter() - t0
        return {
            "n_docs": n_docs,
            "total_s": round(elapsed, 2),
            "docs_per_second": round(n_docs / elapsed, 2),
            "response": result,
        }
    except Exception as exc:
        return {"error": str(exc), "n_docs": n_docs}


# ─── Reranker benchmark ───────────────────────────────────────────────────────

def benchmark_reranker(batch_sizes: list[int], n_repeats: int = 5) -> list[dict[str, Any]]:
    results = []
    try:
        from sentence_transformers import CrossEncoder

        model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        for bs in batch_sizes:
            pairs = [("How does RAG work?", SAMPLE_TEXTS[i % len(SAMPLE_TEXTS)]) for i in range(bs)]
            latencies = []
            for _ in range(n_repeats):
                t0 = time.perf_counter()
                model.predict(pairs)
                latencies.append((time.perf_counter() - t0) * 1000)

            results.append({
                "batch_size": bs,
                "avg_ms": round(statistics.mean(latencies), 1),
                "min_ms": round(min(latencies), 1),
                "max_ms": round(max(latencies), 1),
                "ms_per_pair": round(statistics.mean(latencies) / bs, 2),
            })
        del model
        gc.collect()
    except Exception as exc:
        results.append({"error": str(exc)})

    return results


# ─── Output ───────────────────────────────────────────────────────────────────

def _write_results(result: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nJSON saved to: {output_path}")


def _update_readme(result: dict[str, Any], readme_path: Path) -> None:
    date = result["date"]
    hw = result.get("hardware", {})
    qb = result.get("rag_query_benchmark", {})
    ib = result.get("ingest_benchmark", {})

    device = "GPU" if hw.get("cuda_available") else "CPU"
    gpu_name = hw.get("cuda_device_name", "N/A")
    cpu_count = hw.get("cpu_count", "?")
    ram = hw.get("ram_total_gb", "?")

    lines = [
        f"\n## {date} — {device} ({gpu_name if device == 'GPU' else f'{cpu_count} cores, {ram}GB RAM'})\n",
        "### RAG Query Latency\n",
        "| Metric | Value |",
        "|--------|-------|",
    ]
    if "error" not in qb:
        for key in ["p50_ms", "p95_ms", "p99_ms", "avg_ms", "throughput_qps"]:
            lines.append(f"| {key} | {qb.get(key, 'N/A')} |")

    if "error" not in ib:
        lines += [
            "",
            "### Ingest Throughput\n",
            f"- {ib.get('n_docs', '?')} docs in {ib.get('total_s', '?')}s = **{ib.get('docs_per_second', '?')} docs/s**",
        ]

    # Embedding summary (MiniLM batch=1 as baseline)
    emb_results = result.get("embedding_benchmarks", [])
    minilm_cpu = next(
        (r for r in emb_results if r["model"] == "minilm" and r.get("device") == "cpu"), None
    )
    if minilm_cpu and "batch_results" in minilm_cpu:
        for br in minilm_cpu["batch_results"]:
            if br["batch_size"] == 1:
                lines += [
                    "",
                    "### MiniLM Embedding (CPU, batch=1)\n",
                    f"- {br['avg_ms']}ms avg ({br['ms_per_doc']} ms/doc)",
                ]
                break

    section = "\n".join(lines) + "\n"

    readme_path.parent.mkdir(parents=True, exist_ok=True)
    if not readme_path.exists():
        header = "# Cerebro RAG Benchmarks\n\nPerformance measurements across hardware configurations.\n"
        readme_path.write_text(header)

    with open(readme_path, "a") as f:
        f.write(section)
    print(f"README updated: {readme_path}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Cerebro RAG benchmark harness")
    parser.add_argument("--quick", action="store_true", help="Fewer queries and batch sizes (faster)")
    parser.add_argument("--gpu-only", action="store_true", help="Only benchmark GPU device")
    parser.add_argument("--cpu-only", action="store_true", help="Only benchmark CPU device")
    parser.add_argument("--no-embed", action="store_true", help="Skip embedding benchmark")
    parser.add_argument("--no-rag", action="store_true", help="Skip RAG query benchmark")
    parser.add_argument("--no-ingest", action="store_true", help="Skip ingest benchmark")
    parser.add_argument(
        "--api-url",
        default=os.environ.get("CEREBRO_API_URL", "http://localhost:8009"),
        help="Cerebro API URL (default: $CEREBRO_API_URL or http://localhost:8009)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path (default: docs/benchmarks/benchmark-YYYY-MM-DD.json)",
    )
    args = parser.parse_args()

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    project_root = Path(__file__).parent.parent
    output_path = Path(args.output) if args.output else project_root / "docs" / "benchmarks" / f"benchmark-{date_str}.json"
    readme_path = project_root / "docs" / "benchmarks" / "README.md"

    print("=" * 60)
    print("Cerebro RAG Benchmark")
    print("=" * 60)

    result: dict[str, Any] = {
        "date": date_str,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "quick" if args.quick else "full",
        "hardware": _detect_hardware(),
    }

    hw = result["hardware"]
    print(f"\nHardware: {'CUDA ' + hw.get('cuda_device_name', '') if hw.get('cuda_available') else 'CPU only'}")
    print(f"RAM: {hw.get('ram_total_gb', '?')} GB, CPUs: {hw.get('cpu_count', '?')}")

    # Embedding benchmark
    if not args.no_embed:
        print("\n[1/4] Embedding benchmark...")
        batch_sizes = [1, 8] if args.quick else [1, 8, 32, 64]
        n_repeats = 2 if args.quick else 3

        devices: list[str] = []
        cuda_ok = hw.get("cuda_available", False)
        if not args.cpu_only and cuda_ok:
            devices.append("cuda")
        if not args.gpu_only:
            devices.append("cpu")
        if not devices:
            devices = ["cpu"]

        result["embedding_benchmarks"] = benchmark_embeddings(batch_sizes, devices, n_repeats)

    # Reranker benchmark
    if not args.no_embed:
        print("\n[2/4] Reranker benchmark...")
        reranker_batch_sizes = [1, 4] if args.quick else [1, 4, 8, 16]
        result["reranker_benchmarks"] = benchmark_reranker(reranker_batch_sizes)

    # RAG query benchmark
    if not args.no_rag:
        print(f"\n[3/4] RAG query benchmark (API: {args.api_url})...")
        n_queries = 20 if args.quick else 100
        result["rag_query_benchmark"] = benchmark_rag_queries(args.api_url, n_queries)
        qb = result["rag_query_benchmark"]
        if "error" in qb:
            print(f"  WARNING: {qb['error']}")
        else:
            print(f"  p50={qb['p50_ms']}ms  p95={qb['p95_ms']}ms  p99={qb['p99_ms']}ms  qps={qb['throughput_qps']}")

    # Ingest benchmark
    if not args.no_ingest:
        print(f"\n[4/4] Ingest benchmark (API: {args.api_url})...")
        n_docs = 10 if args.quick else 50
        result["ingest_benchmark"] = benchmark_ingest(args.api_url, n_docs)
        ib = result["ingest_benchmark"]
        if "error" in ib:
            print(f"  WARNING: {ib['error']}")
        else:
            print(f"  {ib['n_docs']} docs in {ib['total_s']}s = {ib['docs_per_second']} docs/s")

    _write_results(result, output_path)
    _update_readme(result, readme_path)

    print("\nDone.")


if __name__ == "__main__":
    main()
