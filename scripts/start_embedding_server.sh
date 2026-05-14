#!/usr/bin/env bash
# Start the optional Cerebro GCP embedding server.

set -euo pipefail

echo "🧠 Starting CEREBRO Embedding Server..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/$(basename "$0")"

if [[ "${CEREBRO_GCP_SHELL_ACTIVE:-}" != "1" ]]; then
    echo "☁️  Entering optional GCP shell..."
    cd "$SCRIPT_DIR"
    exec nix develop .#gcp --command bash "$SCRIPT_PATH" "$@"
fi

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

# Run the server
cd "$SCRIPT_DIR"
python -m uvicorn cerebro.core.gcp_embedding_server:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level info \
    --reload
