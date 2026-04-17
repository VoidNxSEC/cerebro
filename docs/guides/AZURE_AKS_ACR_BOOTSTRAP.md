# Azure AKS + ACR Bootstrap

## Objetivo

Provisionar o mínimo para publicar a imagem do Cerebro em um `Azure Container Registry` e fazer deploy em `AKS` usando GitHub Actions.

## Arquivos envolvidos

- Bootstrap de infraestrutura: [bootstrap-azure-aks-acr.sh](/home/kernelcore/master/cerebro/scripts/bootstrap-azure-aks-acr.sh:1)
- Workflow de push para ACR: [deploy-acr.yml](/home/kernelcore/master/cerebro/.github/workflows/deploy-acr.yml:1)
- Workflow de deploy para AKS: [deploy-aks.yml](/home/kernelcore/master/cerebro/.github/workflows/deploy-aks.yml:1)
- Manifest AKS: [aks-deployment.yaml](/home/kernelcore/master/cerebro/kubernetes/aks-deployment.yaml:1) e [aks-service.yaml](/home/kernelcore/master/cerebro/kubernetes/aks-service.yaml:1)

## Uso

Rode o bootstrap:

```bash
chmod +x scripts/bootstrap-azure-aks-acr.sh
./scripts/bootstrap-azure-aks-acr.sh
```

Ele cria:

- `Resource Group`
- `ACR`
- `AKS`
- `Service Principal` para `AZURE_CREDENTIALS`
- `GitHub Actions vars` se `gh` estiver autenticado

## Variáveis esperadas no GitHub

- `AZURE_ACR_NAME`
- `AZURE_ACR_LOGIN_SERVER`
- `AZURE_ACR_REPOSITORY`
- `AZURE_RESOURCE_GROUP`
- `AZURE_AKS_NAME`
- `AZURE_AKS_NAMESPACE` opcional, default `default`
- `AZURE_AKS_SECRET_NAME` opcional, default `cerebro-env`
- secret `AZURE_CREDENTIALS`
- secret `SOPS_AGE_KEY`

## Fluxo recomendado de produção

1. Rode o bootstrap Azure para criar `ACR`, `AKS` e popular as vars do GitHub.
2. Gere sua chave `age`, atualize [.sops.yaml](/home/kernelcore/master/cerebro/.sops.yaml:1) se necessário e versione `secrets/cerebro.enc.env`.
3. Dispare [deploy-acr.yml](/home/kernelcore/master/cerebro/.github/workflows/deploy-acr.yml:1) para publicar a imagem no `ACR`.
4. Dispare [deploy-aks.yml](/home/kernelcore/master/cerebro/.github/workflows/deploy-aks.yml:1) com:
   - `build_image=true` para pipeline completa
   - `build_image=false` e `image_tag=<tag>` para promover imagem já publicada
5. Use o resumo do workflow para confirmar `image ref`, namespace e rollout.

## Segredos de runtime com SOPS

O deploy para AKS agora espera um arquivo criptografado no repositório:

- `secrets/cerebro.enc.env`

Fluxo:

```bash
mkdir -p secrets
cp config/examples/cerebro.secrets.env.example secrets/cerebro.enc.env
nix develop --command sops encrypt --in-place secrets/cerebro.enc.env
```

No GitHub:

- adicione a chave privada `age` em `SOPS_AGE_KEY`
- mantenha o arquivo criptografado versionado no repo

No workflow:

- o runner decripta o arquivo com `nix develop --command sops decrypt`
- cria/atualiza o `Secret` Kubernetes
- faz rollout do `Deployment` consumindo `envFrom.secretRef`

## Bootstrap com variáveis customizadas

Você pode rodar tudo já com nomes finais:

```bash
SUBSCRIPTION_ID="xxxx-xxxx-xxxx" \
RESOURCE_GROUP="rg-cerebro-prod" \
LOCATION="eastus" \
ACR_NAME="cerebroprodacr" \
ACR_REPOSITORY="cerebro" \
AKS_NAME="aks-cerebro-prod" \
AKS_NAMESPACE="cerebro" \
AKS_SECRET_NAME="cerebro-env" \
GITHUB_OWNER="minhaorg" \
GITHUB_REPO="cerebro" \
./scripts/bootstrap-azure-aks-acr.sh
```

## Build publicado

O workflow usa o output Nix:

```bash
nix build .#dockerImage
docker load < result
```

Por padrão, `.#dockerImage` aponta para a imagem Azure validada no `flake`.
