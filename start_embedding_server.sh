#!/usr/bin/env bash
# Start CEREBRO Embedding Server (Vertex AI Edition)

set -euo pipefail

echo "🧠 Starting CEREBRO Embedding Server..."

# Check GCP credentials
if [[ -z "${GCP_PROJECT_ID:-}" ]]; then
    echo "❌ Error: GCP_PROJECT_ID environment variable not set"
    exit 1
fi

# Export location if not set
export GCP_LOCATION="${GCP_LOCATION:-us-central1}"
export PORT="${PORT:-8001}"

echo "📍 Project: $GCP_PROJECT_ID"
echo "📍 Location: $GCP_LOCATION"
echo "📍 Port: $PORT"
echo "💰 Ready to burn those $6k credits! 🔥"

# Check if in nix shell
if [[ -z "${IN_NIX_SHELL:-}" ]]; then
    echo "⚠️  Not in nix shell, entering dev environment..."
    cd "$(dirname "$0")"
    exec nix develop --command bash "$0" "$@"
fi

# Run the server
cd "$(dirname "$0")"
python -m uvicorn cerebro.core.embedding_server:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level info \
    --reload
