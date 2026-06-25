#!/bin/bash
# Speedrun script - Executa pipeline completo de consumo de créditos

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-gen-lang-client-0530325234}"
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
🚀 SPEEDRUN - Phoenix Cloud Run Credit Burner

Usage: ./speedrun.sh <command> [options]

Commands:
  setup                  Setup inicial (validar env, criar datastore)
  generate [N]           Gerar N queries (default: 10000)
  burn <file> [workers]  Processar queries do arquivo
  monitor                Monitorar consumo em tempo real
  status                 Ver status atual dos créditos
  all                    Executar tudo (setup + generate + burn)

Examples:
  ./speedrun.sh setup
  ./speedrun.sh generate 5000
  ./speedrun.sh burn queries_10k.txt 20
  ./speedrun.sh monitor
  ./speedrun.sh all

Environment variables:
  GOOGLE_CLOUD_PROJECT   GCP Project ID (default: gen-lang-client-0530325234)
  GOOGLE_CLOUD_LOCATION  Location (default: global)
  ENGINE_ID              Discovery Engine ID
EOF
}

function cmd_setup() {
    print_header "🔧 SETUP - Validando ambiente"

    # Check nix develop
    if ! command -v nix &> /dev/null; then
        print_error "Nix não encontrado. Instale NixOS/Nix primeiro."
        exit 1
    fi

    print_success "Nix encontrado"

    # Validate GCP
    print_header "🔐 Validando GCP"
    nix develop --command python phantom.py gcp validate

    print_success "Setup completo!"
}

function cmd_generate() {
    local count=${1:-10000}

    print_header "📝 Gerando $count queries"

    nix develop --command python scripts/generate_queries.py \
        --count "$count" \
        --output "$QUERIES_FILE"

    print_success "Queries geradas: $QUERIES_FILE"
}

function cmd_burn() {
    local file=${1:-$QUERIES_FILE}
    local workers=${2:-$WORKERS}

    if [ ! -f "$file" ]; then
        print_error "Arquivo não encontrado: $file"
        print_warning "Execute: ./speedrun.sh generate"
        exit 1
    fi

    print_header "🔥 QUEIMANDO CRÉDITOS - $file (workers: $workers)"

    if [ -z "$ENGINE_ID" ]; then
        print_error "ENGINE_ID não definido!"
        print_warning "Defina: export ENGINE_ID=seu-engine-id"
        exit 1
    fi

    nix develop --command python scripts/batch_burn.py \
        --file "$file" \
        --project "$PROJECT_ID" \
        --location "$LOCATION" \
        --engine "$ENGINE_ID" \
        --workers "$workers"

    print_success "Batch processing completo!"
}

function cmd_monitor() {
    print_header "📊 Monitorando créditos em tempo real"

    nix develop --command python scripts/monitor_credits.py \
        --project "$PROJECT_ID" \
        --interval 60

}

function cmd_status() {
    print_header "💰 Status atual dos créditos"

    nix develop --command python scripts/monitor_credits.py \
        --project "$PROJECT_ID" \
        --once

}

function cmd_all() {
    print_header "🚀 SPEEDRUN COMPLETO"

    cmd_setup
    cmd_generate 10000
    cmd_burn "$QUERIES_FILE" 20

    print_success "🎉 Speedrun completo!"
    print_warning "Execute './speedrun.sh monitor' para acompanhar"
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
        print_error "Comando desconhecido: $1"
        cmd_help
        exit 1
        ;;
esac
