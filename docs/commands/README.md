# Cerebro CLI Command Reference

> Total commands: 45
> Command groups: 12

## Executive Summary

| Group | Commands | Requires |
|-------|----------|---------|
| `root` | 4 | — |
| `knowledge` | 7 | — |
| `ops` | 2 | — |
| `rag` | 7 | — |
| `rag backend` | 5 | — |
| `rag backends` | 1 | — |
| `setup` | 1 | — |
| `metrics` | 5 | — |
| `content` | 2 | LLM provider |
| `strategy` | 4 | LLM provider |
| `test` | 3 | LLM provider + RAG backend |
| `gcp` | 4 | GCP credentials |

## Root Commands

- [cerebro dashboard](cerebro_dashboard.md) - Launch the React Dashboard GUI (FastAPI backend + Vite frontend).
- [cerebro info](cerebro_info.md) - Display Cerebro environment information.
- [cerebro tui](cerebro_tui.md) - Launch interactive Terminal User Interface (TUI).
- [cerebro version](cerebro_version.md) - Display the current version.

## Group: knowledge

- [cerebro knowledge analyze](cerebro_knowledge_analyze.md) - Extract AST and generate JSONL.
- [cerebro knowledge batch-analyze](cerebro_knowledge_batch-analyze.md) - Process all repositories defined in the configuration file.
- [cerebro knowledge docs](cerebro_knowledge_docs.md) - Generate project documentation automatically.
- [cerebro knowledge etl](cerebro_knowledge_etl.md) - ETL pipeline for documentation processing.
- [cerebro knowledge generate-queries](cerebro_knowledge_generate-queries.md) - Generate search queries for a topic.
- [cerebro knowledge index-repo](cerebro_knowledge_index-repo.md) - Index a code repository for knowledge base.
- [cerebro knowledge summarize](cerebro_knowledge_summarize.md) - 

## Group: ops

- [cerebro ops health](cerebro_ops_health.md) - Check system health (Credentials, Permissions, APIs, Data Stores).
- [cerebro ops status](cerebro_ops_status.md) - 

## Group: rag

- [cerebro rag ingest](cerebro_rag_ingest.md) - Ingest artifacts into the active RAG backend.
- [cerebro rag init](cerebro_rag_init.md) - Initialize backend-specific storage structures for the active RAG backend.
- [cerebro rag migrate](cerebro_rag_migrate.md) - Migrate stored vectors from a source backend into the active RAG backend.
- [cerebro rag query](cerebro_rag_query.md) - Query the active RAG backend with grounded generation.
- [cerebro rag rerank](cerebro_rag_rerank.md) - Rerank documents using a cross‑encoder model (service or local fallback).
- [cerebro rag smoke](cerebro_rag_smoke.md) - Run a backend smoke test against the active RAG runtime.
- [cerebro rag status](cerebro_rag_status.md) - Show the configured production RAG runtime status.

## Group: rag backend

- [cerebro rag backend health](cerebro_rag_backend_health.md) - Report whether the active RAG backend is healthy.
- [cerebro rag backend info](cerebro_rag_backend_info.md) - Show detailed information for the active RAG backend.
- [cerebro rag backend init](cerebro_rag_backend_init.md) - Initialize storage structures for the active RAG backend.
- [cerebro rag backend migrate](cerebro_rag_backend_migrate.md) - Migrate vectors from a source backend into the active backend.
- [cerebro rag backend smoke](cerebro_rag_backend_smoke.md) - Run a smoke test against the active RAG backend.

## Group: rag backends

- [cerebro rag backends list](cerebro_rag_backends_list.md) - List the vector store backends known by the current CLI build.

## Group: setup

- [cerebro setup wizard](cerebro_setup.md) - Interactive configuration wizard (LLM provider, API keys, vector store).

## Group: metrics _(zero-token)_

- [cerebro metrics scan](cerebro_metrics.md) - Full zero-token scan of all repositories under `CEREBRO_ARCH_PATH`.
- [cerebro metrics watch](cerebro_metrics.md) - Interactive real-time metrics watcher.
- [cerebro metrics report](cerebro_metrics.md) - Detailed metrics report for a single repository.
- [cerebro metrics compare](cerebro_metrics.md) - Side-by-side comparison of two or more repositories.
- [cerebro metrics check](cerebro_metrics.md) - Quick health check across all tracked repositories.

## Group: content _(requires LLM provider)_

- [cerebro content mine](cerebro_content.md) - Mine and index content from URLs or local files.
- [cerebro content analyze](cerebro_content.md) - Analyze a single content file in detail.

## Group: strategy _(requires LLM provider)_

- [cerebro strategy optimize](cerebro_strategy.md) - ROI-based strategy optimizer.
- [cerebro strategy salary](cerebro_strategy.md) - Salary intelligence and negotiation analysis.
- [cerebro strategy moat](cerebro_strategy.md) - Build a personal technical moat strategy.
- [cerebro strategy trends](cerebro_strategy.md) - Predict technology trends from the knowledge base.

## Group: test _(requires LLM provider + RAG backend)_

- [cerebro test grounded-search](cerebro_test.md) - Test grounded search with relevance scoring.
- [cerebro test grounded-gen](cerebro_test.md) - Test full grounded generation (retrieval + LLM).
- [cerebro test verify-api](cerebro_test.md) - Verify connectivity to an arbitrary API endpoint.

## Group: gcp _(requires GCP credentials)_

- [cerebro gcp status](cerebro_gcp.md) - Show GCP project and Discovery Engine status.
- [cerebro gcp create-engine](cerebro_gcp.md) - Create a Discovery Engine search app.
- [cerebro gcp monitor](cerebro_gcp.md) - Monitor GCP billing for Discovery Engine usage.
- [cerebro gcp burn](cerebro_gcp.md) - Execute batch queries for load testing.
