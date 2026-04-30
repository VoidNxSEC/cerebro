# Cerebro Deployment Guide

This guide separates the current deploy paths for the Cerebro application from
local dashboard development and docs publishing.

## What is actually deployed

- The deployable runtime is the FastAPI API server from `cerebro.api.server`.
- The container listens on `PORT` when provided, or `8000` by default.
- `cerebro dashboard` is not the production runtime. It is a local dev workflow
  that starts:
  - backend API on `localhost:8009`
  - Vite frontend on `localhost:18321`

## Recommended production path: Azure ACR + AKS

This is the most coherent production route in the repo today.

### Source of truth

- Nix image build: `flake.nix` via `packages.dockerImage`
- Image publish workflow: `.github/deploy-acr.yml`
- Cluster deploy workflow: `.github/deploy-aks.yml`
- Bootstrap script: `scripts/bootstrap-azure-aks-acr.sh`
- AKS manifests: `kubernetes/aks-deployment.yaml`, `kubernetes/aks-service.yaml`

### Required GitHub configuration

Variables:

- `AZURE_ACR_NAME`
- `AZURE_ACR_LOGIN_SERVER`
- `AZURE_ACR_REPOSITORY`
- `AZURE_RESOURCE_GROUP`
- `AZURE_AKS_NAME`
- `AZURE_AKS_NAMESPACE` (optional, defaults to `default`)
- `AZURE_AKS_SECRET_NAME` (optional, defaults to `cerebro-env`)

Secrets:

- `AZURE_CREDENTIALS`
- `SOPS_AGE_KEY`

### Runtime secrets

Commit an encrypted runtime env file:

```bash
mkdir -p secrets
cp config/examples/cerebro.secrets.env.example secrets/cerebro.enc.env
nix develop --command sops encrypt --in-place secrets/cerebro.enc.env
```

The AKS workflow decrypts this file and creates the Kubernetes secret consumed
by `kubernetes/aks-deployment.yaml`.

### Flow

1. Bootstrap Azure infra with `scripts/bootstrap-azure-aks-acr.sh`.
2. Commit `secrets/cerebro.enc.env` encrypted with SOPS.
3. Run `.github/deploy-acr.yml` to publish the Nix-built image to ACR.
4. Run `.github/deploy-aks.yml` to roll out the selected image into AKS.

### Local validation

```bash
nix eval .#packages.x86_64-linux.dockerImage.name
nix build .#dockerImage
```

## Optional path: Cloud Run

Use `.github/deploy.yml` when the target is Google Cloud Run.

Notes:

- The workflow deploys from source using the repository `Dockerfile`.
- The container now honors `PORT`, so Cloud Run can inject its runtime port.
- Set `vars.CLOUD_RUN_SERVICE` if you do not want the default service name.

Required secrets:

- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT`

Useful variables:

- `GCP_REGION`
- `GCP_PROJECT_ID`
- `GOOGLE_CLOUD_PROJECT_ID`
- `DATA_STORE_ID`
- `CLOUD_RUN_SERVICE`

## Optional path: Helm / BREV / generic Kubernetes

The repo also contains a Helm chart under `charts/cerebro`.

Useful files:

- `charts/cerebro/Chart.yaml`
- `charts/cerebro/values.yaml`
- `charts/cerebro/values-dev.yaml`
- `charts/cerebro/values-prod.yaml`

Typical flow:

```bash
helm dependency build charts/cerebro
helm upgrade --install cerebro charts/cerebro -f charts/cerebro/values-prod.yaml
```

This path is viable, but it is not the same source of truth as the AKS GitHub
Actions rollout above.

## Local container smoke run

If you want to verify the API container before pushing anything:

```bash
docker build -t cerebro:latest .
docker run --rm -p 8000:8000 cerebro:latest
curl http://127.0.0.1:8000/health
```

## What is separate from app deploy

- `wrangler.toml` is for docs/site publishing, not the Cerebro API runtime.
- MkDocs and Pages deploys should be treated separately from application deploy.
- `.github/docs.yml` currently validates that the docs site still builds; it does not publish the site by itself.
