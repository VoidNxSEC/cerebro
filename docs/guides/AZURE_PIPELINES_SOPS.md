# Azure Pipelines + SOPS

## What this setup does

- Runs backend quality gates with `nix develop --command`
- Runs dashboard lint, type-check, and build with the same Nix dev shell
- Publishes pytest and coverage results in Azure DevOps
- Adds security gates for `gitleaks`, `pip-audit`, `npm audit`, and `syft`
- Supports CD to Azure Container Apps after decrypting a SOPS-managed env file

## Assumption

This pipeline assumes the deploy target is an existing Azure Container App with pull access to your Azure Container Registry.

## Required Azure DevOps variables

Set these in the pipeline UI or a variable group:

- `AZURE_SERVICE_CONNECTION`: Azure Resource Manager service connection name
- `ACR_NAME`: Azure Container Registry name
- `ACR_LOGIN_SERVER`: Example `myregistry.azurecr.io`
- `AZURE_RESOURCE_GROUP`: Resource group that owns the Container App
- `CONTAINER_APP_NAME`: Existing Azure Container App name
- `SOPS_AGE_KEY`: secret variable containing the private `age` identity used to decrypt the repo secrets
- `ENABLE_AZURE_DEPLOY`: set to `true` only when the deploy path is ready

## Required repo secret file

The deploy stage expects this encrypted file:

- `secrets/cerebro.enc.env`

Create it from the example template:

```bash
mkdir -p secrets
cp config/examples/cerebro.secrets.env.example secrets/cerebro.enc.env
nix develop --command sops encrypt --in-place secrets/cerebro.enc.env
```

## Recommended local SOPS bootstrap

Generate an `age` key locally:

```bash
mkdir -p ~/.config/sops/age
nix develop --command age-keygen -o ~/.config/sops/age/keys.txt
```

Then inspect the public recipient and add it to [.sops.yaml](/home/kernelcore/master/cerebro/.sops.yaml:1) if needed:

```bash
nix develop --command age-keygen -y ~/.config/sops/age/keys.txt
```

## Pipeline flow

1. Install Nix on the hosted Azure agent.
2. Run all project validation through `nix develop --command`.
3. Publish test, coverage, and security artifacts.
4. If `ENABLE_AZURE_DEPLOY=true`, build the container image in ACR.
5. Decrypt `secrets/cerebro.enc.env` with `SOPS_AGE_KEY`.
6. Update the Azure Container App to the new image and env set.

## Notes

- The flake no longer depends on the local-only `/home/kernelcore/master/spider-nix` path, so remote CI runners can evaluate it.
- The dev shell now includes `gitleaks`, `syft`, `pip-audit`, and `nodejs_20`.
- CI mode suppresses the interactive shell cosmetics to keep logs readable.
