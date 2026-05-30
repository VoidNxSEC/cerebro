# INFRA-MAESTRO: Practical Examples

## Example 1: Complete Microservice Repository Structure

```
my-platform/
├── flake.nix                    # The orchestrator
├── flake.lock
├── justfile                     # Task runner
├── README.md
├── ARCHITECTURE.md
│
├── nix/
│   ├── lib/
│   │   ├── default.nix         # Helper functions
│   │   └── k8s-builders.nix    # K8s manifest builders
│   │
│   ├── modules/
│   │   ├── app.nix             # Reusable app module
│   │   ├── database.nix        # Database module
│   │   └── monitoring.nix      # Monitoring stack
│   │
│   └── packages/
│       ├── api/                # API service
│       │   ├── default.nix
│       │   └── Dockerfile.nix
│       │
│       └── worker/             # Background worker
│           ├── default.nix
│           └── Dockerfile.nix
│
├── kubernetes/
│   ├── base/
│   │   ├── kustomization.yaml
│   │   ├── namespace.yaml
│   │   ├── api/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   └── configmap.yaml
│   │   │
│   │   └── worker/
│   │       └── deployment.yaml
│   │
│   ├── components/
│   │   ├── postgres/
│   │   │   ├── kustomization.yaml
│   │   │   ├── statefulset.yaml
│   │   │   └── service.yaml
│   │   │
│   │   └── redis/
│   │       ├── kustomization.yaml
│   │       └── deployment.yaml
│   │
│   └── overlays/
│       ├── dev/
│       │   ├── kustomization.yaml
│       │   └── patches/
│       │
│       ├── staging/
│       │   └── kustomization.yaml
│       │
│       └── prod/
│           ├── kustomization.yaml
│           ├── hpa.yaml
│           └── pdb.yaml
│
├── terraform/                   # Cloud resources (if needed)
│   ├── modules/
│   │   └── gke-cluster/
│   │
│   └── environments/
│       ├── dev/
│       ├── staging/
│       └── prod/
│
├── scripts/
│   ├── bootstrap-cluster.sh
│   ├── backup-db.sh
│   └── rotate-secrets.sh
│
└── docs/
    ├── runbooks/
    │   ├── incident-response.md
    │   └── deployment.md
    │
    └── decisions/
        ├── 001-use-kustomize.md
        └── 002-monorepo-structure.md
```

## Example 2: Complete flake.nix

```nix
{
  description = "Production-Grade Microservices Platform";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ self.overlays.default ];
        };

        # Shared configuration
        commonConfig = {
          version = "1.0.0";
          registry = "ghcr.io/myorg";
        };

        # Import custom lib
        lib = import ./nix/lib { inherit pkgs; };

      in
      {
        # Overlay for custom packages
        overlays.default = final: prev: {
          # Your custom packages here
        };

        # Development environment
        devShells.default = pkgs.mkShell {
          name = "platform-dev";
          
          buildInputs = with pkgs; [
            # Kubernetes
            kubectl
            kubernetes-helm
            kustomize
            k9s
            stern
            kubectx
            
            # Development
            just
            direnv
            
            # Tools
            jq
            yq-go
            
            # Security
            trivy
            kubesec
            gitleaks
          ];

          shellHook = ''
            echo "🚀 Platform Development Environment"
            echo ""
            echo "Available commands:"
            echo "  just dev       - Start local cluster"
            echo "  just deploy    - Deploy to cluster"
            echo "  just test      - Run tests"
            echo ""
            
            # Set KUBECONFIG
            export KUBECONFIG=~/.kube/config
            
            # Enable direnv if available
            if command -v direnv &> /dev/null; then
              eval "$(direnv hook bash)"
            fi
          '';
        };

        # Packages (applications)
        packages = {
          # API service
          api = pkgs.buildGoModule {
            pname = "api";
            version = commonConfig.version;
            src = ./services/api;
            vendorHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
          };

          # API container image
          api-image = pkgs.dockerTools.buildLayeredImage {
            name = "${commonConfig.registry}/api";
            tag = commonConfig.version;
            
            maxLayers = 120;
            
            contents = [ self.packages.${system}.api ];
            
            config = {
              Cmd = [ "${self.packages.${system}.api}/bin/api" ];
              ExposedPorts = {
                "8080/tcp" = {};
              };
              Env = [
                "PATH=/bin"
              ];
            };
          };

          # Worker service
          worker = pkgs.buildGoModule {
            pname = "worker";
            version = commonConfig.version;
            src = ./services/worker;
            vendorHash = "sha256-BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=";
          };

          # Worker container image
          worker-image = pkgs.dockerTools.buildLayeredImage {
            name = "${commonConfig.registry}/worker";
            tag = commonConfig.version;
            
            maxLayers = 120;
            
            contents = [ self.packages.${system}.worker ];
            
            config = {
              Cmd = [ "${self.packages.${system}.worker}/bin/worker" ];
            };
          };

          # K8s manifests for each environment
          k8s-dev = lib.buildKustomize {
            name = "manifests-dev";
            src = ./kubernetes/overlays/dev;
          };

          k8s-staging = lib.buildKustomize {
            name = "manifests-staging";
            src = ./kubernetes/overlays/staging;
          };

          k8s-prod = lib.buildKustomize {
            name = "manifests-prod";
            src = ./kubernetes/overlays/prod;
          };

          # Security scanner
          security-scan = pkgs.writeScriptBin "security-scan" ''
            #!${pkgs.bash}/bin/bash
            set -euo pipefail
            
            echo "🔒 Running security scans..."
            
            # Scan container images
            echo "📦 Scanning container images..."
            ${pkgs.trivy}/bin/trivy image \
              --severity HIGH,CRITICAL \
              ${commonConfig.registry}/api:${commonConfig.version}
            
            # Scan Kubernetes configs
            echo "☸️  Scanning Kubernetes manifests..."
            ${pkgs.trivy}/bin/trivy config kubernetes/
            
            # Check for secrets in code
            echo "🔐 Checking for leaked secrets..."
            ${pkgs.gitleaks}/bin/gitleaks detect \
              --source . \
              --verbose \
              --no-git
            
            echo "✅ Security scan complete!"
          '';
        };

        # Apps (executable commands)
        apps = {
          # Deploy to environment
          deploy = {
            type = "app";
            program = toString (pkgs.writeScript "deploy" ''
              #!${pkgs.bash}/bin/bash
              set -euo pipefail
              
              ENV=''${1:-dev}
              
              echo "🚀 Deploying to $ENV..."
              
              # Build manifests
              ${pkgs.kustomize}/bin/kustomize build \
                kubernetes/overlays/$ENV \
                | ${pkgs.kubectl}/bin/kubectl apply -f -
              
              echo "✅ Deployment complete!"
              
              # Watch rollout
              ${pkgs.kubectl}/bin/kubectl rollout status \
                deployment/api -n platform
            '');
          };

          # Run local cluster
          dev-cluster = {
            type = "app";
            program = toString (pkgs.writeScript "dev-cluster" ''
              #!${pkgs.bash}/bin/bash
              set -euo pipefail
              
              echo "🏗️  Starting local cluster..."
              
              ${pkgs.kind}/bin/kind create cluster \
                --name platform-dev \
                --config kind-config.yaml
              
              # Load images
              ${pkgs.kind}/bin/kind load docker-image \
                ${commonConfig.registry}/api:${commonConfig.version}
              
              echo "✅ Cluster ready!"
            '');
          };
        };

        # Checks (CI/CD validation)
        checks = {
          # Validate Nix code
          nix-fmt = pkgs.runCommand "check-nix-fmt" {
            buildInputs = [ pkgs.nixpkgs-fmt ];
          } ''
            nixpkgs-fmt --check ${./.}
            touch $out
          '';

          # Validate K8s manifests
          k8s-validate = pkgs.runCommand "check-k8s" {
            buildInputs = [ pkgs.kustomize pkgs.kubeval ];
          } ''
            for env in dev staging prod; do
              echo "Validating $env..."
              kustomize build kubernetes/overlays/$env | kubeval
            done
            touch $out
          '';

          # Run tests
          unit-tests = pkgs.runCommand "unit-tests" {
            buildInputs = [ self.packages.${system}.api ];
          } ''
            # Run Go tests
            cd ${./services/api}
            go test ./...
            touch $out
          '';
        };
      }
    );
}
```

## Example 3: Advanced K8s Builder (lib/k8s-builders.nix)

```nix
{ pkgs }:
rec {
  # Build kustomize manifests
  buildKustomize = { name, src }:
    pkgs.runCommand name {
      buildInputs = [ pkgs.kustomize ];
    } ''
      mkdir -p $out
      kustomize build ${src} > $out/manifests.yaml
    '';

  # Generate deployment manifest
  mkDeployment = {
    name,
    namespace ? "default",
    replicas ? 1,
    image,
    port ? 8080,
    env ? {},
    resources ? {},
    ...
  }:
    pkgs.writeText "${name}-deployment.yaml" ''
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: ${name}
        namespace: ${namespace}
        labels:
          app: ${name}
      spec:
        replicas: ${toString replicas}
        selector:
          matchLabels:
            app: ${name}
        template:
          metadata:
            labels:
              app: ${name}
          spec:
            containers:
            - name: ${name}
              image: ${image}
              ports:
              - containerPort: ${toString port}
              env:
              ${pkgs.lib.concatStringsSep "\n" (
                pkgs.lib.mapAttrsToList (k: v: ''
                  - name: ${k}
                    value: "${v}"
                '') env
              )}
              ${if resources != {} then ''
              resources:
                ${if resources ? requests then ''
                requests:
                  cpu: ${resources.requests.cpu or "100m"}
                  memory: ${resources.requests.memory or "128Mi"}
                '' else ""}
                ${if resources ? limits then ''
                limits:
                  cpu: ${resources.limits.cpu or "500m"}
                  memory: ${resources.limits.memory or "512Mi"}
                '' else ""}
              '' else ""}
    '';

  # Generate service manifest
  mkService = {
    name,
    namespace ? "default",
    port ? 8080,
    targetPort ? 8080,
    type ? "ClusterIP",
    ...
  }:
    pkgs.writeText "${name}-service.yaml" ''
      apiVersion: v1
      kind: Service
      metadata:
        name: ${name}
        namespace: ${namespace}
        labels:
          app: ${name}
      spec:
        type: ${type}
        selector:
          app: ${name}
        ports:
        - port: ${toString port}
          targetPort: ${toString targetPort}
          protocol: TCP
    '';

  # Generate complete app (deployment + service)
  mkApp = args:
    let
      deployment = mkDeployment args;
      service = mkService args;
    in
    pkgs.runCommand "${args.name}-manifests" {} ''
      mkdir -p $out
      cat ${deployment} > $out/deployment.yaml
      cat ${service} > $out/service.yaml
    '';
}
```

## Example 4: Perfect Justfile

```just
# Environment variables
export KUBECONFIG := env_var_or_default('KUBECONFIG', '~/.kube/config')
export ENVIRONMENT := env_var_or_default('ENVIRONMENT', 'dev')

# Default recipe (shows help)
default:
    @just --list --unsorted

# Development
# ===========

# Enter Nix development shell
dev:
    nix develop

# Start local Kubernetes cluster
cluster-up:
    kind create cluster --name platform-dev --config kind-config.yaml
    kubectl cluster-info

# Delete local cluster
cluster-down:
    kind delete cluster --name platform-dev

# Load images into local cluster
cluster-load-images:
    @echo "Loading images into cluster..."
    nix build .#api-image
    kind load docker-image $(docker load < result | grep -oP 'Loaded image: \K.*')
    nix build .#worker-image
    kind load docker-image $(docker load < result | grep -oP 'Loaded image: \K.*')

# Build
# =====

# Build all container images
build:
    @echo "Building images..."
    nix build .#api-image
    nix build .#worker-image

# Build and tag images
build-and-tag VERSION:
    @echo "Building and tagging version {{VERSION}}..."
    nix build .#api-image
    docker load < result
    docker tag api:latest ghcr.io/myorg/api:{{VERSION}}
    
    nix build .#worker-image
    docker load < result
    docker tag worker:latest ghcr.io/myorg/worker:{{VERSION}}

# Push images to registry
push VERSION:
    docker push ghcr.io/myorg/api:{{VERSION}}
    docker push ghcr.io/myorg/worker:{{VERSION}}

# Deployment
# ==========

# Deploy to environment
deploy ENV='dev':
    @echo "Deploying to {{ENV}}..."
    kustomize build kubernetes/overlays/{{ENV}} | kubectl apply -f -
    kubectl rollout status deployment/api -n platform
    kubectl rollout status deployment/worker -n platform

# Show diff before deploying
diff ENV='dev':
    kustomize build kubernetes/overlays/{{ENV}} | kubectl diff -f -

# Rollback deployment
rollback DEPLOYMENT:
    kubectl rollout undo deployment/{{DEPLOYMENT}} -n platform

# Restart deployment (rolling restart)
restart DEPLOYMENT:
    kubectl rollout restart deployment/{{DEPLOYMENT}} -n platform

# Scale deployment
scale DEPLOYMENT REPLICAS:
    kubectl scale deployment/{{DEPLOYMENT}} --replicas={{REPLICAS}} -n platform

# Operations
# ==========

# Get pod logs
logs SERVICE:
    stern {{SERVICE}} -n platform --tail 100

# Execute shell in pod
shell POD:
    kubectl exec -it {{POD}} -n platform -- /bin/sh

# Port forward to service
forward SERVICE PORT:
    kubectl port-forward svc/{{SERVICE}} {{PORT}}:{{PORT}} -n platform

# Get all resources
status:
    kubectl get all -n platform

# Describe resource
describe RESOURCE NAME:
    kubectl describe {{RESOURCE}} {{NAME}} -n platform

# Testing
# =======

# Run all tests
test:
    @echo "Running tests..."
    nix build .#checks.unit-tests
    nix build .#checks.integration-tests

# Validate manifests
validate ENV='dev':
    @echo "Validating {{ENV}} manifests..."
    kustomize build kubernetes/overlays/{{ENV}} | kubeval

# Security scan
security-scan:
    nix run .#security-scan

# Quality
# =======

# Format all code
fmt:
    @echo "Formatting Nix code..."
    nix fmt
    @echo "Formatting YAML..."
    prettier --write "**/*.{yaml,yml,json,md}"

# Lint code
lint:
    @echo "Linting Nix code..."
    nix flake check
    @echo "Linting Kubernetes manifests..."
    just validate dev
    just validate staging
    just validate prod

# Run pre-commit checks
pre-commit:
    just fmt
    just lint
    just security-scan
    just test

# Maintenance
# ===========

# Update dependencies
update:
    nix flake update
    git add flake.lock
    git commit -m "chore: update dependencies"

# Clean build artifacts
clean:
    rm -rf result result-*
    docker system prune -f

# Backup database
backup-db:
    ./scripts/backup-db.sh

# Restore database
restore-db BACKUP_FILE:
    ./scripts/restore-db.sh {{BACKUP_FILE}}

# Monitoring
# ==========

# Open Grafana
grafana:
    kubectl port-forward svc/grafana 3000:80 -n monitoring

# Open Prometheus
prometheus:
    kubectl port-forward svc/prometheus 9090:9090 -n monitoring

# View metrics for service
metrics SERVICE:
    kubectl top pod -l app={{SERVICE}} -n platform

# Troubleshooting
# ==============

# Debug pod (shows events, logs, describe)
debug POD:
    @echo "=== Events ==="
    kubectl get events --field-selector involvedObject.name={{POD}} -n platform
    @echo -e "\n=== Logs ==="
    kubectl logs {{POD}} -n platform --tail=50
    @echo -e "\n=== Description ==="
    kubectl describe pod {{POD}} -n platform

# Check cluster health
health:
    kubectl get nodes
    kubectl top nodes
    kubectl get pods --all-namespaces | grep -v Running

# Get resource usage
usage:
    kubectl top pods -n platform
    kubectl top nodes
```

## Example 5: GitHub Actions CI/CD

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  validate:
    name: Validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: cachix/install-nix-action@v20
        with:
          nix_path: nixpkgs=channel:nixos-unstable
          extra_nix_config: |
            experimental-features = nix-command flakes
      
      - uses: cachix/cachix-action@v12
        with:
          name: myorg
          authToken: '${{ secrets.CACHIX_AUTH_TOKEN }}'
      
      - name: Check Nix flake
        run: nix flake check
      
      - name: Validate Kubernetes manifests
        run: |
          nix develop --command bash -c "
            for env in dev staging prod; do
              echo \"Validating \$env...\"
              kustomize build kubernetes/overlays/\$env | kubeval
            done
          "
      
      - name: Security scan
        run: nix run .#security-scan

  test:
    name: Test
    runs-on: ubuntu-latest
    needs: validate
    steps:
      - uses: actions/checkout@v3
      
      - uses: cachix/install-nix-action@v20
        with:
          nix_path: nixpkgs=channel:nixos-unstable
      
      - name: Run tests
        run: |
          nix build .#checks.unit-tests
          nix build .#checks.integration-tests

  build:
    name: Build Images
    runs-on: ubuntu-latest
    needs: test
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v3
      
      - uses: cachix/install-nix-action@v20
      
      - name: Log in to registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push API image
        run: |
          nix build .#api-image
          IMAGE_ID=$(docker load < result | grep -oP 'Loaded image: \K.*')
          docker tag $IMAGE_ID ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/api:${{ github.sha }}
          docker push ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/api:${{ github.sha }}
      
      - name: Build and push Worker image
        run: |
          nix build .#worker-image
          IMAGE_ID=$(docker load < result | grep -oP 'Loaded image: \K.*')
          docker tag $IMAGE_ID ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/worker:${{ github.sha }}
          docker push ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/worker:${{ github.sha }}

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - uses: actions/checkout@v3
      
      - name: Update image tags
        run: |
          cd kubernetes/overlays/staging
          kustomize edit set image \
            api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/api:${{ github.sha }} \
            worker=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/worker:${{ github.sha }}
      
      - name: Commit manifest updates
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add kubernetes/overlays/staging
          git commit -m "chore: update staging images to ${{ github.sha }}"
          git push

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://example.com
    steps:
      - uses: actions/checkout@v3
      
      - name: Update image tags
        run: |
          cd kubernetes/overlays/prod
          kustomize edit set image \
            api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/api:${{ github.sha }} \
            worker=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/worker:${{ github.sha }}
      
      - name: Commit manifest updates
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add kubernetes/overlays/prod
          git commit -m "chore: update production images to ${{ github.sha }}"
          git push
      
      - name: Create release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: v${{ github.run_number }}
          release_name: Release v${{ github.run_number }}
          body: |
            Deployed commit: ${{ github.sha }}
            Changes: See commit history
```

## Summary

These examples demonstrate:

1. **Complete repository structure** - Monorepo layout with clear separation
2. **Nix-powered builds** - Declarative, reproducible everything
3. **Kubernetes organization** - Base + overlays + components
4. **Task automation** - Just commands for all operations
5. **CI/CD pipeline** - Automated testing and deployment
6. **Developer experience** - Fast feedback, easy debugging

**Key Principles Applied:**

- ✅ Declarative everything
- ✅ Single source of truth
- ✅ Composable modules
- ✅ Environment parity
- ✅ Security by default
- ✅ Observable from day one

**Next Steps:**

1. Copy structure to your repo
2. Customize for your services
3. Add monitoring/logging
4. Document decisions in ADRs
5. Test disaster recovery

**Remember:** Start simple, add complexity only when justified by pain. 🎯
