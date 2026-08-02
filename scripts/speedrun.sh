#!/bin/bash
# Speedrun script - Full pipeline for GCP Discovery Engine batch processing

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?GCP_PROJECT_ID or GOOGLE_CLOUD_PROJECT must be set}"
LOCATION="${GOOGLE_CLOUD_LOCATION:-global}"
ENGINE_ID="${ENGINE_ID}"

QUERIES_FILE="queries_10k.txt"
WORKERS=10

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

function print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

function print_error() {
    echo -e "${RED}❌ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

function cmd_help() {
    cat <<EOF
🚀 SPEEDRUN - GCP Discovery Engine Batch Query Pipeline

Usage: ./speedrun.sh <command> [options]

Commands:
  setup                  Initial setup (validate env, create datastore)
  generate [N]           Generate N queries (default: 10000)
  process <file> [workers]  Process queries from file
  monitor                Monitor credit consumption in real time
  status                 Show current credit status
  all                    Run everything (setup + generate + process)

Examples:
  ./speedrun.sh setup
  ./speedrun.sh generate 5000
  ./speedrun.sh burn queries_10k.txt 20
  ./speedrun.sh monitor
  ./speedrun.sh all

Environment variables:
  GOOGLE_CLOUD_PROJECT   GCP Project ID (default: value of GOOGLE_CLOUD_PROJECT env var)
  GOOGLE_CLOUD_LOCATION  Location (default: global)
  ENGINE_ID              Discovery Engine ID
EOF
}

function cmd_setup() {
    print_header "🔧 SETUP - Validando ambiente"

    if ! command -v nix &> /dev/null; then
        print_error "Nix not found. Install NixOS/Nix first."
        exit 1
    fi

    print_success "Nix found"

    print_header "🔐 Validating GCP"
    nix develop --command cerebro gcp validate

    print_success "Setup complete!"
}

function cmd_generate() {
    local count=${1:-10000}

    print_header "📝 Generating $count queries"

    nix develop --command python scripts/generate_queries.py \
        --count "$count" \
        --output "$QUERIES_FILE"

    print_success "Queries generated: $QUERIES_FILE"
}

function cmd_burn() {
    local file=${1:-$QUERIES_FILE}
    local workers=${2:-$WORKERS}

    if [ ! -f "$file" ]; then
        print_error "File not found: $file"
        print_warning "Run: ./speedrun.sh generate"
        exit 1
    fi

    print_header "🔥 Processing queries — $file (workers: $workers)"

    if [ -z "$ENGINE_ID" ]; then
        print_error "ENGINE_ID not set!"
        print_warning "Set: export ENGINE_ID=your-engine-id"
        exit 1
    fi

    nix develop --command python scripts/batch_burn.py \
        --file "$file" \
        --project "$PROJECT_ID" \
        --location "$LOCATION" \
        --engine "$ENGINE_ID" \
        --workers "$workers"

    print_success "Batch processing complete!"
}

function cmd_monitor() {
    print_header "📊 Monitoring credits in real time"

    nix develop --command python scripts/monitor_credits.py \
        --project "$PROJECT_ID" \
        --interval 60

}

function cmd_status() {
    print_header "💰 Current credit status"

    nix develop --command python scripts/monitor_credits.py \
        --project "$PROJECT_ID" \
        --once

}

function cmd_all() {
    print_header "🚀 FULL SPEEDRUN"

    cmd_setup
    cmd_generate 10000
    cmd_burn "$QUERIES_FILE" 20

    print_success "🎉 Speedrun complete!"
    print_warning "Run './speedrun.sh monitor' to track progress"
}

# Main
case "${1:-help}" in
    setup)
        cmd_setup
        ;;
    generate)
        cmd_generate "${2:-10000}"
        ;;
    burn)
        cmd_burn "${2:-$QUERIES_FILE}" "${3:-$WORKERS}"
        ;;
    monitor)
        cmd_monitor
        ;;
    status)
        cmd_status
        ;;
    all)
        cmd_all
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        print_error "Unknown command: $1"
        cmd_help
        exit 1
        ;;
esac
