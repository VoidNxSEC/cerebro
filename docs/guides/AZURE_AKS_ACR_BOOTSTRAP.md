# Azure AKS + ACR Bootstrap

## Goal

Provision the minimum infrastructure to publish the Cerebro image to an `Azure Container Registry` and deploy it to `AKS` via GitHub Actions.

## Files

- Infrastructure bootstrap: `scripts/bootstrap-azure-aks-acr.sh`
- ACR push workflow: `.github/workflows/deploy-acr.yml`
- AKS deploy workflow: `.github/workflows/deploy-aks.yml`
- AKS manifests: `kubernetes/aks-deployment.yaml` and `kubernetes/aks-service.yaml`

## Usage

Run the bootstrap script:

```bash
chmod +x scripts/bootstrap-azure-aks-acr.sh
./scripts/bootstrap-azure-aks-acr.sh
```

It creates:

- `Resource Group`
- `ACR`
- `AKS`
- `Service Principal` for `AZURE_CREDENTIALS`
- `GitHub Actions vars` if `gh` is authenticated

## Required GitHub variables and secrets

- `AZURE_ACR_NAME`
- `AZURE_ACR_LOGIN_SERVER`
- `AZURE_ACR_REPOSITORY`
- `AZURE_RESOURCE_GROUP`
- `AZURE_AKS_NAME`
- `AZURE_AKS_NAMESPACE` — optional, default `default`
- `AZURE_AKS_SECRET_NAME` — optional, default `cerebro-env`
- secret `AZURE_CREDENTIALS`
- secret `SOPS_AGE_KEY`

## Recommended production flow

1. Run the Azure bootstrap to create `ACR`, `AKS`, and populate GitHub vars.
2. Generate your `age` key, update `.sops.yaml` if needed, and commit `secrets/cerebro.enc.env`.
3. Trigger `.github/workflows/deploy-acr.yml` to publish the image to `ACR`.
4. Trigger `.github/workflows/deploy-aks.yml` with:
   - `build_image=true` for a full pipeline run
   - `build_image=false` and `image_tag=<tag>` to promote an already-published image
5. Check the workflow summary to confirm `image ref`, namespace, and rollout status.

## Runtime secrets with SOPS

The AKS deploy stage expects an encrypted file committed to the repository:

- `secrets/cerebro.enc.env`

Create it from the example template:

```bash
mkdir -p secrets
cp config/examples/cerebro.secrets.env.example secrets/cerebro.enc.env
nix develop --command sops encrypt --in-place secrets/cerebro.enc.env
```

On GitHub:

- Add the private `age` key as `SOPS_AGE_KEY`
- Keep the encrypted file committed to the repo

In the workflow:

- The runner decrypts the file with `nix develop --command sops decrypt`
- Creates/updates the Kubernetes `Secret`
- Rolls out the `Deployment` consuming `envFrom.secretRef`

## Bootstrap with custom variable names

You can pass all final names upfront:

```bash
SUBSCRIPTION_ID="xxxx-xxxx-xxxx" \
RESOURCE_GROUP="rg-cerebro-prod" \
LOCATION="eastus" \
ACR_NAME="cerebroprodacr" \
ACR_REPOSITORY="cerebro" \
AKS_NAME="aks-cerebro-prod" \
AKS_NAMESPACE="cerebro" \
AKS_SECRET_NAME="cerebro-env" \
GITHUB_OWNER="your-org" \
GITHUB_REPO="cerebro" \
./scripts/bootstrap-azure-aks-acr.sh
```

## Published build

The workflow uses the Nix output:

```bash
nix build .#dockerImage
docker load < result
```

By default, `.#dockerImage` points to the Azure-validated image defined in the `flake`.
