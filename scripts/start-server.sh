#!/usr/bin/env bash
# SecureLLM Bridge - Start Script
# This script starts the server with proper environment variables

set -e

# Colors
GREEN='\033[0.32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting SecureLLM Bridge...${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure directories exist
mkdir -p logs data

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Redis not running. Starting Redis...${NC}"
    nix-shell -p redis --command "redis-server --daemonize yes --port 6379 --dir /tmp" 2>/dev/null || {
        echo -e "${YELLOW}Failed to start Redis. Trying system Redis...${NC}"
    }
    sleep 1
fi

# Export environment variables
export LOG_DIR="${SCRIPT_DIR}/logs"
export DATABASE_URL="sqlite:${SCRIPT_DIR}/data/models.db"
export REDIS_URL="redis://localhost:6379"
export SERVER_HOST="0.0.0.0"
export SERVER_PORT="8080"

# Provider configuration (customize as needed)
export LLAMACPP_ENABLED=true
export LLAMACPP_BASE_URL="http://localhost:5001"
export LLAMACPP_MODEL_NAME="local-model"

export DEEPSEEK_ENABLED="${DEEPSEEK_ENABLED:-false}"
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-your-key-here}"

export OPENAI_ENABLED="${OPENAI_ENABLED:-false}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-your-key-here}"

export ANTHROPIC_ENABLED="${ANTHROPIC_ENABLED:-false}"
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-your-key-here}"

export GROQ_ENABLED="${GROQ_ENABLED:-false}"
export GROQ_API_KEY="${GROQ_API_KEY:-your-key-here}"

export GEMINI_ENABLED="${GEMINI_ENABLED:-false}"
export GEMINI_API_KEY="${GEMINI_API_KEY:-your-key-here}"

export NVIDIA_ENABLED="${NVIDIA_ENABLED:-false}"
export NVIDIA_API_KEY="${NVIDIA_API_KEY:-your-key-here}"

# Security
export REQUIRE_AUTH=false
export LOG_LEVEL=info

echo -e "${GREEN}✅ Environment configured${NC}"
echo -e "${BLUE}📊 Configuration:${NC}"
echo "  - Log Directory: $LOG_DIR"
echo "  - Database: $DATABASE_URL"
echo "  - Redis: $REDIS_URL"
echo "  - Server: $SERVER_HOST:$SERVER_PORT"
echo "  - LlamaCpp: $LLAMACPP_BASE_URL"
echo ""

# Build and run
echo -e "${BLUE}🔨 Building and starting server...${NC}"
cargo run --release --bin securellm-api-server

