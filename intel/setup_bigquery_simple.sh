#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "🔧 SETUP BIGQUERY DATASET - MÉTODO SIMPLES"
echo "============================================================"
echo ""
echo "Este script:"
echo "  1. Cria o dataset BigQuery"
echo "  2. Mostra o link do console para configurar export"
echo "  3. Verifica quando a tabela aparecer"
echo ""

# Configurações
PROJECT_ID="${GOOGLE_CLOUD_PROJECT_ID:-$(gcloud config get-value project)}"
DATASET_ID="${BILLING_EXPORT_DATASET:-billing_export}"
LOCATION="${BIGQUERY_LOCATION:-US}"

echo "📋 Configuração:"
echo "   Project: $PROJECT_ID"
echo "   Dataset: $DATASET_ID"
echo "   Location: $LOCATION"
echo ""

# Passo 1: Habilitar BigQuery
echo "🔌 Habilitando BigQuery API..."
gcloud services enable bigquery.googleapis.com --project="$PROJECT_ID" 2>/dev/null || true
echo "✅ BigQuery API habilitada"

# Passo 2: Criar dataset
echo ""
echo "📊 Criando dataset '$DATASET_ID'..."

if bq ls -d --project_id="$PROJECT_ID" 2>/dev/null | grep -q "$DATASET_ID"; then
    echo "ℹ️  Dataset '$DATASET_ID' já existe"
else
    bq mk \
        --project_id="$PROJECT_ID" \
        --location="$LOCATION" \
        --dataset \
        "$DATASET_ID"
    echo "✅ Dataset criado"
fi

# Passo 3: Instruções manuais
echo ""
echo "============================================================"
echo "📋 CONFIGURAÇÃO MANUAL NECESSÁRIA"
echo "============================================================"
echo ""
echo "Abra este link no navegador:"
echo ""
echo "  https://console.cloud.google.com/billing/export?project=$PROJECT_ID"
echo ""
echo "E siga os passos:"
echo "  1. Clique em 'EDIT SETTINGS' na seção 'Detailed usage cost'"
echo "  2. Marque 'Export to BigQuery'"
echo "  3. Project: $PROJECT_ID"
echo "  4. Dataset: $DATASET_ID"
echo "  5. Clique 'SAVE'"
echo ""
read -p "Pressione ENTER quando terminar a configuração..."

# Passo 4: Aguardar tabela
echo ""
echo "============================================================"
echo "⏰ Aguardando criação da tabela..."
echo "============================================================"
echo ""

MAX_ATTEMPTS=24  # 4 minutos
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))

    # Lista tabelas
    TABLES=$(bq ls --max_results=100 --project_id="$PROJECT_ID" "$DATASET_ID" 2>/dev/null || echo "")
    BILLING_TABLE=$(echo "$TABLES" | grep "gcp_billing_export_v1" | awk '{print $1}' | head -n1)

    if [ -n "$BILLING_TABLE" ]; then
        echo ""
        echo "✅ TABELA ENCONTRADA: $BILLING_TABLE"
        echo ""
        echo "============================================================"
        echo "✅ SETUP COMPLETO!"
        echo "============================================================"
        echo ""
        echo "Configure as variáveis:"
        echo ""
        echo "export BILLING_EXPORT_DATASET='$DATASET_ID'"
        echo "export BILLING_EXPORT_TABLE='$BILLING_TABLE'"
        echo ""

        # Salva em arquivo
        ENV_FILE=".billing_export.env"
        cat > "$ENV_FILE" <<-EOF
# Auto-gerado por setup_bigquery_simple.sh
export BILLING_EXPORT_DATASET='$DATASET_ID'
export BILLING_EXPORT_TABLE='$BILLING_TABLE'
EOF

        echo "💾 Salvo em: $ENV_FILE"
        echo ""
        echo "🚀 Use com:"
        echo "   source $ENV_FILE"
        echo "   python audit_credits_bigquery.py"
        echo ""
        echo "⚠️  Dados podem levar 24-48h para aparecer!"
        exit 0
    fi

    echo -n "."
    sleep 10
done

echo ""
echo ""
echo "⚠️  Tabela ainda não apareceu."
echo ""
echo "💡 Isso é NORMAL. O Google Cloud pode levar até 24h para:"
echo "   1. Processar a configuração"
echo "   2. Criar a tabela"
echo "   3. Popular com dados iniciais"
echo ""
echo "🔍 Verifique depois com:"
echo "   bq ls --project_id=$PROJECT_ID $DATASET_ID"
echo ""
echo "Ou liste todas as tabelas:"
echo "   bq ls --project_id=$PROJECT_ID $DATASET_ID | grep billing"
echo ""
