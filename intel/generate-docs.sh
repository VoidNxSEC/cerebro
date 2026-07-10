#!/usr/bin/env bash
set -e

echo "🚀 Starting Self-Documentation Engine..."

# 1. Ensure Dependencies
if ! command -v cerebro &> /dev/null; then
    echo "❌ 'cerebro' command not found. Run 'poetry install' first."
    exit 1
fi

# 2. Run Analysis (The Engine)
# Analyze the current directory to extract AST
echo "🔬 Analyzing Source Code..."
cerebro knowledge analyze . --task-context "Documentation Generation"

# 3. Run Generator
echo "✍️  Generating Markdown Docs..."
python scripts/generate_docs.py

# 4. ETL Transformation (Prepare for Vertex AI)
echo "🏭 Running ETL for Vertex AI Search..."
python scripts/etl_docs.py

echo "✅ Documentation Complete!"
echo "   - Local: docs/commands/"
echo "   - Ingestion Artifact: data/ingestion/docs_vertex.jsonl"
echo ""
echo "🚀 To Deploy to GCS & Index:"
echo "   gsutil cp data/ingestion/docs_vertex.jsonl gs://YOUR_BUCKET/ingest/docs_$(date +%s).jsonl"
echo "   (Then trigger your Vertex AI Pipeline or BigQuery Data Transfer)"
