#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "🔧 SETUP BIGQUERY BILLING EXPORT - VIA CLI"
echo "============================================================"

# Configurações
PROJECT_ID="${GOOGLE_CLOUD_PROJECT_ID:-$(gcloud config get-value project)}"
DATASET_ID="${BILLING_EXPORT_DATASET:-billing_export}"
LOCATION="${BIGQUERY_LOCATION:-US}"  # US, EU, etc

echo ""
echo "📋 Configuração:"
echo "   Project: $PROJECT_ID"
echo "   Dataset: $DATASET_ID"
echo "   Location: $LOCATION"
echo ""

# Passo 1: Habilitar API do BigQuery
echo "🔌 Passo 1/4: Habilitando BigQuery API..."
gcloud services enable bigquery.googleapis.com --project="$PROJECT_ID"
echo "✅ BigQuery API habilitada"

# Passo 2: Criar dataset
echo ""
echo "📊 Passo 2/4: Criando dataset '$DATASET_ID'..."

# Verifica se já existe
if bq ls -d --project_id="$PROJECT_ID" | grep -q "$DATASET_ID"; then
    echo "ℹ️  Dataset '$DATASET_ID' já existe"
else
    bq mk \
        --project_id="$PROJECT_ID" \
        --location="$LOCATION" \
        --dataset \
        "$DATASET_ID"
    echo "✅ Dataset criado"
fi

# Passo 3: Pegar Billing Account ID
echo ""
echo "💳 Passo 3/4: Identificando Billing Account..."

BILLING_ACCOUNT=$(gcloud billing projects describe "$PROJECT_ID" \
    --format="value(billingAccountName)" | sed 's|billingAccounts/||')

if [ -z "$BILLING_ACCOUNT" ]; then
    echo "❌ Erro: Projeto não tem billing account vinculada"
    echo ""
    echo "🔧 FIX: Vincule uma billing account primeiro:"
    echo "   gcloud billing projects link $PROJECT_ID \\"
    echo "     --billing-account=XXXXXX-XXXXXX-XXXXXX"
    exit 1
fi

echo "✅ Billing Account: $BILLING_ACCOUNT"

# Passo 4: Configurar export
echo ""
echo "📤 Passo 4/4: Configurando Billing Export..."

# IMPORTANTE: Precisa usar a API REST porque gcloud não tem comando direto
# Vamos usar curl com autenticação do gcloud

# Pega access token
ACCESS_TOKEN=$(gcloud auth print-access-token)

# Configuração do export
BIGQUERY_PROJECT="$PROJECT_ID"
BIGQUERY_DATASET="$DATASET_ID"

# Payload JSON
read -r -d '' PAYLOAD <<EOF || true
{
  "name": "billingAccounts/$BILLING_ACCOUNT/billingExports/billing-export-resource",
  "displayName": "Detailed Billing Export to BigQuery",
  "description": "Export billing data to BigQuery for credit validation",
  "bigqueryDestination": {
    "datasetId": "projects/$BIGQUERY_PROJECT/datasets/$BIGQUERY_DATASET"
  }
}
EOF

echo ""
echo "🌐 Chamando Cloud Billing API..."
echo ""

# Tenta criar o export
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    "https://cloudbilling.googleapis.com/v1beta/billingAccounts/$BILLING_ACCOUNT/billingExports")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 201 ]; then
    echo "✅ Billing Export configurado com sucesso!"
elif echo "$BODY" | grep -q "ALREADY_EXISTS"; then
    echo "ℹ️  Billing Export já existe. Verificando configuração..."

    # Lista exports existentes
    EXISTING=$(curl -s \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        "https://cloudbilling.googleapis.com/v1beta/billingAccounts/$BILLING_ACCOUNT/billingExports")

    echo "📋 Exports existentes:"
    echo "$EXISTING" | jq -r '.billingExports[]?.bigqueryDestination.datasetId // "N/A"' 2>/dev/null || echo "$EXISTING"
else
    echo "⚠️  Resposta da API (HTTP $HTTP_CODE):"
    echo "$BODY" | jq . 2>/dev/null || echo "$BODY"
fi

# Passo 5: Aguardar criação da tabela
echo ""
echo "============================================================"
echo "⏰ Aguardando criação da tabela de billing..."
echo "============================================================"
echo ""
echo "O Google Cloud cria automaticamente uma tabela no formato:"
echo "  gcp_billing_export_v1_XXXXXX_XXXXXX_XXXXXX"
echo ""
echo "⏳ Isso pode levar alguns minutos. Verificando..."

# Espera e verifica
MAX_ATTEMPTS=12  # 12 tentativas = 2 minutos
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))

    echo -n "   Tentativa $ATTEMPT/$MAX_ATTEMPTS: "

    # Lista tabelas no dataset
    TABLES=$(bq ls --max_results=100 --project_id="$PROJECT_ID" "$DATASET_ID" 2>/dev/null || echo "")

    # Procura por tabela de billing export
    BILLING_TABLE=$(echo "$TABLES" | grep "gcp_billing_export_v1" | awk '{print $1}' | head -n1)

    if [ -n "$BILLING_TABLE" ]; then
        echo "✅ ENCONTRADA!"
        echo ""
        echo "📊 Tabela de billing: $BILLING_TABLE"
        echo ""

        # Exporta para uso nos scripts
        echo "============================================================"
        echo "✅ SETUP COMPLETO!"
        echo "============================================================"
        echo ""
        echo "📝 Configure as variáveis de ambiente:"
        echo ""
        echo "export BILLING_EXPORT_DATASET='$DATASET_ID'"
        echo "export BILLING_EXPORT_TABLE='$BILLING_TABLE'"
        echo ""
        echo "Ou adicione no flake.nix:"
        echo ""
        cat <<-'NIXCODE'
		shellHook = ''
		  export BILLING_EXPORT_DATASET="billing_export"
		  export BILLING_EXPORT_TABLE="<tabela-aqui>"
		'';
		NIXCODE
        echo ""
        echo "🚀 Agora você pode executar:"
        echo "   python audit_credits_bigquery.py"
        echo ""
        echo "⚠️  IMPORTANTE: Dados de billing podem levar 24-48h para aparecer!"

        # Cria arquivo .env local com as configs
        ENV_FILE=".billing_export.env"
        cat > "$ENV_FILE" <<-ENVEOF
# Auto-gerado por setup_bigquery_export.sh
export BILLING_EXPORT_DATASET='$DATASET_ID'
export BILLING_EXPORT_TABLE='$BILLING_TABLE'
ENVEOF

        echo ""
        echo "💾 Salvo em: $ENV_FILE"
        echo "   Source com: source $ENV_FILE"

        exit 0
    fi

    echo "Aguardando..."
    sleep 10
done

echo ""
echo "⚠️  Tabela ainda não apareceu após 2 minutos."
echo ""
echo "💡 Isso é NORMAL. Pode levar até 24h."
echo ""
echo "🔍 Verifique manualmente depois:"
echo "   bq ls --project_id=$PROJECT_ID $DATASET_ID"
echo ""
echo "📋 Quando a tabela aparecer, anote o nome (formato: gcp_billing_export_v1_...)"
echo "   e configure:"
echo ""
echo "   export BILLING_EXPORT_TABLE='gcp_billing_export_v1_...'"
echo ""
