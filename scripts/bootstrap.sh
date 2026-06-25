#!/usr/bin/env bash
# bootstrap.sh — idempotent first-run setup for the Cerebro RAG Docker stack
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ── colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${BLUE}[bootstrap]${NC} $*"; }
success() { echo -e "${GREEN}[ok]${NC} $*"; }
warn()    { echo -e "${YELLOW}[warn]${NC} $*"; }
die()     { echo -e "${RED}[error]${NC} $*" >&2; exit 1; }

# ── usage ─────────────────────────────────────────────────────────────────────
usage() {
  cat <<EOF
${BOLD}Usage:${NC} bash scripts/bootstrap.sh [OPTIONS]

Bootstrap the Cerebro RAG Docker stack.

${BOLD}Options:${NC}
  --profile PROFILE   Activate a vector-store sidecar profile.
                      Choices: qdrant | pgvector | opensearch
  --no-start          Build only; do not start containers.
  --no-build          Skip docker build (use existing image).
  -h, --help          Show this help and exit.

${BOLD}Examples:${NC}
  bash scripts/bootstrap.sh
  bash scripts/bootstrap.sh --profile qdrant
  bash scripts/bootstrap.sh --no-start
EOF
}

# ── argument parsing ──────────────────────────────────────────────────────────
PROFILE=""
START=true
BUILD=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)    PROFILE="$2"; shift 2 ;;
    --no-start)   START=false; shift ;;
    --no-build)   BUILD=false; shift ;;
    -h|--help)    usage; exit 0 ;;
    *) die "Unknown option: $1. Run with --help for usage." ;;
  esac
done

# ── prerequisites ──────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Cerebro RAG — Bootstrap${NC}"
echo "────────────────────────────────────────"

check_cmd() {
  command -v "$1" &>/dev/null || die "'$1' is required but not found. Install it and retry."
}

check_cmd docker
check_cmd curl

# Docker Compose v2 (plugin) or standalone
if docker compose version &>/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose &>/dev/null; then
  COMPOSE="docker-compose"
else
  die "Docker Compose not found. Install it: https://docs.docker.com/compose/install/"
fi

success "prerequisites ok (docker, compose, curl)"

# ── .env ──────────────────────────────────────────────────────────────────────
cd "$REPO_ROOT"

if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    cp .env.example .env
    warn ".env created from .env.example — edit it to add API keys before querying."
  else
    warn "No .env.example found; skipping .env creation."
  fi
else
  success ".env already exists"
fi

# ── docker-entrypoint.sh ──────────────────────────────────────────────────────
ENTRYPOINT="docker-entrypoint.sh"
if [[ ! -f "$ENTRYPOINT" ]]; then
  warn "$ENTRYPOINT missing — regenerating..."
  cat > "$ENTRYPOINT" <<'EOF'
#!/bin/sh
set -eu
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
exec uvicorn cerebro.api.server:app --host "$HOST" --port "$PORT"
EOF
fi
chmod +x "$ENTRYPOINT"
success "docker-entrypoint.sh ready"

# ── compose validation ────────────────────────────────────────────────────────
$COMPOSE config --quiet
success "docker-compose.yml syntax ok"

# ── build ─────────────────────────────────────────────────────────────────────
if [[ "$BUILD" == true ]]; then
  info "Building cerebro image…"
  $COMPOSE build --progress=plain
  success "image built"
else
  info "--no-build: skipping docker build"
fi

# ── start ─────────────────────────────────────────────────────────────────────
if [[ "$START" == false ]]; then
  info "--no-start: skipping container startup"
  echo ""
  echo -e "${GREEN}Build complete.${NC} Start with:"
  echo "  docker compose up -d"
  exit 0
fi

COMPOSE_UP_ARGS=("up" "-d" "--remove-orphans")
[[ -n "$PROFILE" ]] && COMPOSE_UP_ARGS+=("--profile" "$PROFILE")

info "Starting containers (profile: ${PROFILE:-default})…"
$COMPOSE "${COMPOSE_UP_ARGS[@]}"

# ── health check ─────────────────────────────────────────────────────────────
PORT="${PORT:-8000}"
HEALTH_URL="http://localhost:${PORT}/health"
MAX_WAIT=90
INTERVAL=5
elapsed=0

info "Waiting for API at ${HEALTH_URL} (up to ${MAX_WAIT}s)…"
until curl -fsS "$HEALTH_URL" &>/dev/null; do
  if [[ $elapsed -ge $MAX_WAIT ]]; then
    warn "API did not become healthy within ${MAX_WAIT}s."
    warn "Check logs: docker compose logs -f cerebro"
    exit 1
  fi
  sleep "$INTERVAL"
  elapsed=$((elapsed + INTERVAL))
  echo -n "."
done
echo ""

HEALTH=$(curl -fsS "$HEALTH_URL")
success "API healthy — ${HEALTH}"

# ── summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Cerebro RAG is running${NC}"
echo "────────────────────────────────────────"
echo -e "  API       → ${BLUE}http://localhost:${PORT}${NC}"
echo -e "  Docs      → ${BLUE}http://localhost:${PORT}/docs${NC}"
echo -e "  Health    → ${BLUE}http://localhost:${PORT}/health${NC}"
[[ "$PROFILE" == "qdrant" ]] && echo -e "  Qdrant    → ${BLUE}http://localhost:6333/dashboard${NC}"
echo ""
echo -e "Stop:   ${YELLOW}docker compose down${NC}"
echo -e "Logs:   ${YELLOW}docker compose logs -f cerebro${NC}"
echo -e "Guide:  ${YELLOW}docs/guides/DOCKER.md${NC}"
