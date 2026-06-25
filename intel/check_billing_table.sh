#!/usr/bin/env bash
# Script para verificar status da tabela de billing

PROJECT_ID="${GOOGLE_CLOUD_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
DATASET_ID="${BILLING_EXPORT_DATASET:-billing_export}"

echo "🔍 Verificando tabelas de billing..."
echo "   Project: $PROJECT_ID"
echo "   Dataset: $DATASET_ID"
echo ""

# Verifica se dataset existe
if ! bq ls -d --project_id="$PROJECT_ID" 2>/dev/null | grep -q "$DATASET_ID"; then
    echo "❌ Dataset '$DATASET_ID' não existe"
    echo ""
    echo "Crie com:"
    echo "  bq mk --project_id=$PROJECT_ID --location=US --dataset $DATASET_ID"
    echo ""
    echo "Ou execute:"
    echo "  ./setup_bigquery_simple.sh"
    exit 1
fi

echo "✅ Dataset '$DATASET_ID' existe"
echo ""

# Lista tabelas
echo "📊 Tabelas no dataset:"
TABLES=$(bq ls --max_results=100 --project_id="$PROJECT_ID" "$DATASET_ID" 2>/dev/null)

if [ -z "$TABLES" ]; then
    echo "   (Vazio - ainda não há tabelas)"
    echo ""
    echo "💡 Se você já configurou o export:"
    echo "   Aguarde 24-48h para dados aparecerem"
else
    echo "$TABLES"
    echo ""

    # Procura tabela de billing
    BILLING_TABLE=$(echo "$TABLES" | grep "gcp_billing_export_v1" | awk '{print $1}' | head -n1)

    if [ -n "$BILLING_TABLE" ]; then
        echo "✅ TABELA DE BILLING ENCONTRADA!"
        echo ""
        echo "Configure:"
        echo "  export BILLING_EXPORT_DATASET='$DATASET_ID'"
        echo "  export BILLING_EXPORT_TABLE='$BILLING_TABLE'"
        echo ""
        echo "Ou adicione ao .billing_export.env:"
        cat > .billing_export.env <<-EOF
export BILLING_EXPORT_DATASET='$DATASET_ID'
export BILLING_EXPORT_TABLE='$BILLING_TABLE'
EOF
        echo "  source .billing_export.env"
    else
        echo "⚠️  Nenhuma tabela de billing ainda"
        echo ""
        echo "Configure o export em:"
        echo "  https://console.cloud.google.com/billing/export?project=$PROJECT_ID"
    fi
fi
