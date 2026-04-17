#!/usr/bin/env bash
set -euo pipefail

# === CONFIGURE AQUI ===
SUBSCRIPTION_ID="${SUBSCRIPTION_ID:-SEU_SUBSCRIPTION_ID}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-meu-projeto}"
LOCATION="${LOCATION:-eastus}"
ACR_NAME="${ACR_NAME:-meuacr$(date +%s | sha256sum | head -c6)}"
ACR_REPOSITORY="${ACR_REPOSITORY:-cerebro}"
AKS_NAME="${AKS_NAME:-aks-meu-projeto}"
AKS_NAMESPACE="${AKS_NAMESPACE:-default}"
AKS_SECRET_NAME="${AKS_SECRET_NAME:-cerebro-env}"
SP_NAME="${SP_NAME:-gh-actions-sp-meu-projeto}"
GITHUB_OWNER="${GITHUB_OWNER:-minhaorg}"
GITHUB_REPO="${GITHUB_REPO:-meu-repo}"
GITHUB_REPO_FULL="${GITHUB_OWNER}/${GITHUB_REPO}"
AZURE_DEVOPS_ORG="${AZURE_DEVOPS_ORG:-minhaorg}"
AZURE_DEVOPS_PROJECT="${AZURE_DEVOPS_PROJECT:-meu-projeto}"
# =======================

echo "Subscription: $SUBSCRIPTION_ID"
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "ACR: $ACR_NAME"
echo "ACR repository: $ACR_REPOSITORY"
echo "AKS: $AKS_NAME"
echo "AKS namespace: $AKS_NAMESPACE"
echo "AKS secret name: $AKS_SECRET_NAME"
echo "SP: $SP_NAME"
echo "GitHub repo: $GITHUB_REPO_FULL"
echo

if [[ "$SUBSCRIPTION_ID" == "SEU_SUBSCRIPTION_ID" ]]; then
  echo "Defina SUBSCRIPTION_ID antes de rodar."
  exit 1
fi

az account show >/dev/null 2>&1 || az login
az account set --subscription "$SUBSCRIPTION_ID"

echo "Criando resource group..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none

echo "Criando Azure Container Registry..."
az acr create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ACR_NAME" \
  --sku Basic \
  --admin-enabled false \
  --output none

ACR_LOGIN_SERVER="$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query loginServer -o tsv)"
echo "ACR criado: $ACR_LOGIN_SERVER"

echo "Criando AKS (pode demorar alguns minutos)..."
az aks create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$AKS_NAME" \
  --node-count 3 \
  --enable-managed-identity \
  --generate-ssh-keys \
  --location "$LOCATION" \
  --output none

echo "Anexando ACR ao AKS..."
az aks update -n "$AKS_NAME" -g "$RESOURCE_GROUP" --attach-acr "$ACR_NAME" --output none

echo "Baixando credenciais do AKS para kubectl..."
az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$AKS_NAME" --overwrite-existing

echo "Criando Service Principal para GitHub Actions..."
SP_JSON_FILE="sp-${SP_NAME}.json"
az ad sp create-for-rbac \
  --name "$SP_NAME" \
  --role contributor \
  --scopes "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}" \
  --sdk-auth > "$SP_JSON_FILE"

echo "Service Principal criado e salvo em $SP_JSON_FILE"
echo

ACR_RESOURCE_ID="$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query id -o tsv)"
SP_APP_ID="$(jq -r '.clientId' < "$SP_JSON_FILE")"
echo "Atribuindo role AcrPush ao SP no ACR..."
az role assignment create --assignee "$SP_APP_ID" --role AcrPush --scope "$ACR_RESOURCE_ID" --output none

if command -v gh >/dev/null 2>&1; then
  echo "Tentando gravar secret AZURE_CREDENTIALS no GitHub repo $GITHUB_REPO_FULL..."
  gh auth status >/dev/null 2>&1 || echo "gh CLI não autenticado. Rode 'gh auth login' se quiser automatizar o secret."
  gh secret set AZURE_CREDENTIALS --body "$(cat "$SP_JSON_FILE")" --repo "$GITHUB_REPO_FULL"
  echo "Secret AZURE_CREDENTIALS gravado no GitHub."

  echo "Gravando vars do GitHub Actions..."
  gh variable set AZURE_RESOURCE_GROUP --body "$RESOURCE_GROUP" --repo "$GITHUB_REPO_FULL"
  gh variable set AZURE_AKS_NAME --body "$AKS_NAME" --repo "$GITHUB_REPO_FULL"
  gh variable set AZURE_AKS_NAMESPACE --body "$AKS_NAMESPACE" --repo "$GITHUB_REPO_FULL"
  gh variable set AZURE_AKS_SECRET_NAME --body "$AKS_SECRET_NAME" --repo "$GITHUB_REPO_FULL"
  gh variable set AZURE_ACR_NAME --body "$ACR_NAME" --repo "$GITHUB_REPO_FULL"
  gh variable set AZURE_ACR_LOGIN_SERVER --body "$ACR_LOGIN_SERVER" --repo "$GITHUB_REPO_FULL"
  gh variable set AZURE_ACR_REPOSITORY --body "$ACR_REPOSITORY" --repo "$GITHUB_REPO_FULL"
  echo "Vars do GitHub Actions gravadas."
else
  echo "gh CLI não encontrada. Copie o conteúdo de $SP_JSON_FILE e crie o secret AZURE_CREDENTIALS manualmente no GitHub."
fi

echo
echo "=== Próximo passo: Service Connection Azure DevOps (opcional) ==="
echo "Se você usa Azure Pipelines e quer que o Azure DevOps acesse o GitHub, crie um Service Connection."
cat <<EOF
az devops configure --defaults organization=https://dev.azure.com/${AZURE_DEVOPS_ORG} project=${AZURE_DEVOPS_PROJECT}
az extension add --name azure-devops
# Em geral é mais simples criar o Service Connection via UI do Azure DevOps
EOF

echo
echo "=== Instalar ArgoCD no AKS (opcional) ==="
cat <<'EOF'
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl -n argocd port-forward svc/argocd-server 8080:443
EOF

echo
echo "=== RESUMO ==="
echo "Resource Group: $RESOURCE_GROUP"
echo "ACR: $ACR_LOGIN_SERVER"
echo "AKS: $AKS_NAME"
echo "Service Principal JSON: $SP_JSON_FILE"
echo
echo "Crie ou confira estas GitHub Actions vars:"
echo "  AZURE_RESOURCE_GROUP=$RESOURCE_GROUP"
echo "  AZURE_AKS_NAME=$AKS_NAME"
echo "  AZURE_AKS_NAMESPACE=$AKS_NAMESPACE"
echo "  AZURE_AKS_SECRET_NAME=$AKS_SECRET_NAME"
echo "  AZURE_ACR_NAME=$ACR_NAME"
echo "  AZURE_ACR_LOGIN_SERVER=$ACR_LOGIN_SERVER"
echo "  AZURE_ACR_REPOSITORY=$ACR_REPOSITORY"
echo
echo "Para runtime seguro com SOPS no GitHub Actions:"
echo "  1. crie o secret SOPS_AGE_KEY com sua chave privada age"
echo "  2. versione secrets/cerebro.enc.env criptografado com SOPS"
