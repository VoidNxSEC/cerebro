#!/usr/bin/env bash
# scripts/sync_data.sh - Helper para Sincronização de Dados com GCS (A LEI)
# Uso: ./scripts/sync_data.sh [local_dir] [remote_path]

set -e

# Configurações
PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project)}
BUCKET_NAME="${PROJECT_ID}-cerebro-ingest"
LOCAL_DIR=${1:-"./data/analyzed"}
REMOTE_SUBDIR=${2:-"staging"}

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Erro: GCP_PROJECT_ID não definido e não detectado no gcloud config."
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧠 CEREBRO - GCS Sync (Programmatic Credit Consumption)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Project: $PROJECT_ID"
echo "📂 Bucket:  gs://$BUCKET_NAME"
echo "📁 Source:  $LOCAL_DIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Garantir que o bucket existe
if ! gcloud storage buckets describe "gs://$BUCKET_NAME" &>/dev/null; then
    echo "🔨 Criando bucket gs://$BUCKET_NAME..."
    gcloud storage buckets create "gs://$BUCKET_NAME" --location=us-central1
fi

# 2. Sincronização de alta performance
echo "🚀 Sincronizando dados..."
gcloud storage cp -r "$LOCAL_DIR" "gs://$BUCKET_NAME/$REMOTE_SUBDIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Sincronização concluída!"
echo "🔗 URI para Importação: gs://$BUCKET_NAME/$REMOTE_SUBDIR/$(basename $LOCAL_DIR)/*"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
