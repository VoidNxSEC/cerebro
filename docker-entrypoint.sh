#!/bin/sh
set -eu

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

exec uvicorn cerebro.api.server:app --host "$HOST" --port "$PORT"
