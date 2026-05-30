# INFRA-MAESTRO: Quick Reference Cheatsheet

> **TL;DR:** Referência rápida para decisões arquiteturais e comandos essenciais

## 🎯 Decision Matrix (30 segundos)

### Repository Structure
```
Small project (<5 services)     → Monorepo
Large org (>10 teams)           → Polyrepo per team
Medium (5-10 services)          → Monorepo (easier ops)
```

### Manifest Management
```
Simple configs                  → Plain YAML
Need templating                 → Kustomize
Complex package mgmt            → Helm (but consider Nix first)
Multi-cluster                   → ArgoCD/Flux
```

### Container Building
```
Simple apps                     → dockerTools.buildImage
Complex deps                    → dockerTools.buildLayeredImage
Need caching                    → buildLayeredImage + maxLayers=120
Multi-stage builds              → Nix derivations
```

## ⚡ Essential Commands

### Nix Flakes
```bash
# Enter dev shell
nix develop

# Build package
nix build .#package-name

# Run app
nix run .#app-name

# Update dependencies
nix flake update

# Check flake
nix flake check

# Show outputs
nix flake show
```

### Kustomize
```bash
# Build overlay
kustomize build overlays/prod

# Preview changes
kustomize build overlays/prod | kubectl diff -f -

# Apply
kustomize build overlays/prod | kubectl apply -f -

# Edit image
cd overlays/prod
kustomize edit set image app=myapp:v2
```

### Kubectl Essentials
```bash
# Context
kubectl config use-context prod
kubectl config set-context --current --namespace=myapp

# Deployments
kubectl rollout status deployment/app
kubectl rollout history deployment/app
kubectl rollout undo deployment/app
kubectl rollout restart deployment/app

# Debugging
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl logs -f deployment/app
kubectl describe pod app-xxx
kubectl exec -it app-xxx -- sh

# Resources
kubectl top nodes
kubectl top pods
kubectl get all -n myapp
```

## 🏗️ Quick Repo Bootstrap

```bash
# 1. Create structure
mkdir -p {nix/{lib,modules,packages},kubernetes/{base,overlays/{dev,staging,prod},components},scripts,docs/{runbooks,decisions}}

# 2. Initialize flake
cat > flake.nix << 'EOF'
{
  description = "My Infrastructure";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  outputs = { nixpkgs, ... }: {
    devShells.x86_64-linux.default = 
      nixpkgs.legacyPackages.x86_64-linux.mkShell {
        buildInputs = with nixpkgs.legacyPackages.x86_64-linux; [
          kubectl kustomize just
        ];
      };
  };
}
EOF

# 3. Create justfile
cat > justfile << 'EOF'
default:
    @just --list

dev:
    nix develop

deploy ENV:
    kustomize build kubernetes/overlays/{{ENV}} | kubectl apply -f -
EOF

# 4. Initialize git
git init
git add .
git commit -m "feat: initial commit"
```

## 📋 Template Snippets

### Minimal flake.nix
```nix
{
  description = "Infra";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  outputs = { self, nixpkgs }: {
    devShells.x86_64-linux.default = 
      nixpkgs.legacyPackages.x86_64-linux.mkShell {
        buildInputs = with nixpkgs.legacyPackages.x86_64-linux; [
          kubectl kustomize
        ];
      };
  };
}
```

### Docker Image (Nix)
```nix
packages.my-app-image = pkgs.dockerTools.buildLayeredImage {
  name = "my-app";
  tag = "latest";
  maxLayers = 120;
  contents = [ self.packages.${system}.my-app ];
  config.Cmd = [ "${self.packages.${system}.my-app}/bin/my-app" ];
};
```

### Kustomization Base
```yaml
# kubernetes/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
commonLabels:
  app: myapp
```

### Kustomization Overlay
```yaml
# kubernetes/overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
bases:
  - ../../base
replicas:
  - name: myapp
    count: 3
images:
  - name: myapp
    newTag: v1.0.0
```

### Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:latest
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
```

### Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

## 🔐 Security Checklist

```bash
# Before every commit
□ No secrets in code (check with: gitleaks detect)
□ All images scanned (trivy image myapp:latest)
□ K8s configs validated (kubeval)
□ Dependencies updated (nix flake update)

# Before production deploy
□ Resource limits set
□ Health checks configured
□ Network policies applied
□ RBAC configured
□ Secrets externalized (sealed-secrets/vault)
□ Monitoring enabled
□ Backups configured
□ Runbook exists
```

## 🚨 Common Issues & Solutions

### Issue: Nix builds are slow
```bash
# Solution: Use binary cache
nix.settings = {
  substituters = ["https://cache.nixos.org" "https://your-cache.cachix.org"];
  trusted-public-keys = ["cache.nixos.org-1:..."];
};
```

### Issue: K8s manifest too long
```bash
# Solution: Use kustomize components
# kubernetes/components/monitoring/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component
resources:
  - prometheus.yaml
  - grafana.yaml
```

### Issue: Can't reproduce builds
```bash
# Solution: Pin all inputs
nix flake update
git add flake.lock
git commit -m "chore: pin dependencies"
```

### Issue: Secrets in git
```bash
# Prevention: Use git-secrets
git secrets --install
git secrets --register-aws
git secrets --scan
```

## 📊 Monitoring Queries (Prometheus)

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Pod restarts
rate(kube_pod_container_status_restarts_total[1h])

# CPU usage
rate(container_cpu_usage_seconds_total[5m])

# Memory usage
container_memory_working_set_bytes
```

## 🎨 ASCII Art Structure

```
┌─────────────────────────────────────┐
│         INFRASTRUCTURE              │
├─────────────────────────────────────┤
│                                     │
│  Nix Flake (Source of Truth)       │
│      ↓                              │
│  ┌──────────┐    ┌──────────┐      │
│  │ Packages │    │ K8s YAML │      │
│  └────┬─────┘    └────┬─────┘      │
│       │               │             │
│       ↓               ↓             │
│  Container        Kustomize         │
│   Images          Overlays          │
│       │               │             │
│       └───────┬───────┘             │
│               ↓                     │
│          Kubernetes                 │
│           Cluster                   │
│                                     │
└─────────────────────────────────────┘
```

## 🎯 Golden Rules

1. **README First** - Se você não pode explicar em 2 min, simplifique
2. **Declarative Always** - Estado visível > Estado escondido
3. **Delete Often** - Código deletável > Código eterno
4. **Test Before Prod** - Staging deve ser prod-like
5. **Monitor Everything** - Se não tem métrica, não existe
6. **Document Decisions** - ADRs > Wiki morto
7. **Automate Boring** - Scripts > Processos manuais
8. **Secure by Default** - Security afterthought = Security disaster

## 🏄 Flow State Commands

```bash
# Morning routine
just update && just build && just test

# Pre-deploy
just validate prod && just diff prod && just security-scan

# Deploy
just deploy prod

# Post-deploy
just health && just logs api

# Incident response
just rollback api && just debug api-xxx-yyy
```

## 💡 Pro Tips

1. **Use direnv** - Auto-load nix shell quando entrar no repo
2. **Alias comum** - `alias k=kubectl`, `alias kx=kubectx`
3. **Shell prompt** - Mostre namespace/context atual
4. **Pre-commit hooks** - Valide antes de commit
5. **Cache agressivo** - Nix binary cache salva horas
6. **Logs estruturados** - JSON logs > Plain text
7. **GitOps** - Git push → Auto deploy
8. **Backup configs** - Terraform state, sealed-secrets keys

## 🔗 Essential Links

- **Nix**: https://nix.dev
- **Kustomize**: https://kustomize.io
- **Kubectl**: https://kubernetes.io/docs/reference/kubectl/
- **Just**: https://just.systems
- **ArgoCD**: https://argo-cd.readthedocs.io

---

**Remember**: Simplicidade é a sofisticação suprema. Se está complexo, você ainda não entendeu o problema direito. 🎯

**Surf the wave** 🏄
