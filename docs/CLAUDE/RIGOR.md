# INFRA-MAESTRO: RIGOR & ENFORCEMENT

> *"Discipline equals freedom. Constraints breed creativity. Automation prevents stupidity."*

## 🔒 MANDATORY PRACTICES (Non-Negotiable)

### The Iron Laws of Infrastructure

Estas não são sugestões. São **requisitos obrigatórios** para qualquer repo de produção.

#### Law #1: NO SECRETS IN GIT - EVER

**Enforcement**:
```nix
# .githooks/pre-commit
#!/usr/bin/env bash
set -euo pipefail

echo "🔐 Scanning for secrets..."

# Gitleaks scan
if ! gitleaks detect --source . --verbose --no-git; then
    echo "❌ SECRETS DETECTED! Commit BLOCKED."
    echo "Remove secrets and try again."
    exit 1
fi

# Additional patterns
FORBIDDEN_PATTERNS=(
    "password\s*=\s*['\"].*['\"]"
    "api[_-]?key\s*=\s*['\"].*['\"]"
    "secret\s*=\s*['\"].*['\"]"
    "token\s*=\s*['\"].*['\"]"
    "AWS.*SECRET"
    "PRIVATE.*KEY"
)

for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
    if git diff --cached | grep -iE "$pattern"; then
        echo "❌ FORBIDDEN PATTERN DETECTED: $pattern"
        exit 1
    fi
done

echo "✅ No secrets found"
```

**CI Enforcement**:
```yaml
# .github/workflows/security.yaml
name: Security Gate

on: [push, pull_request]

jobs:
  secrets-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Full history for comprehensive scan
      
      - name: Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      
      - name: TruffleHog
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD
```

#### Law #2: ALL IMAGES MUST BE SCANNED

**Enforcement**:
```nix
# nix/lib/security.nix
{ pkgs, ... }:
{
  # Wrap docker build with mandatory scanning
  buildSecureImage = args:
    let
      image = pkgs.dockerTools.buildLayeredImage args;
    in
    pkgs.runCommand "${args.name}-scanned" {
      buildInputs = [ pkgs.trivy ];
    } ''
      # Load image
      docker load < ${image}
      
      # Scan with strict severity threshold
      trivy image \
        --severity CRITICAL,HIGH \
        --exit-code 1 \
        --no-progress \
        ${args.name}:${args.tag or "latest"}
      
      # If scan passes, output the image
      cp ${image} $out
    '';
}
```

**Usage (MANDATORY)**:
```nix
packages.api-image = lib.buildSecureImage {
  name = "api";
  tag = "latest";
  contents = [ self.packages.${system}.api ];
  config.Cmd = [ "${self.packages.${system}.api}/bin/api" ];
};
```

#### Law #3: RESOURCE LIMITS ARE REQUIRED

**Validation**:
```nix
# nix/validators/k8s.nix
{ pkgs, lib }:
{
  validateDeployment = manifest:
    let
      hasResourceLimits = deployment:
        deployment.spec.template.spec.containers
        |> builtins.all (container:
          container ? resources &&
          container.resources ? limits &&
          container.resources.limits ? cpu &&
          container.resources.limits ? memory
        );
      
      yaml = builtins.fromJSON manifest;
    in
    assert hasResourceLimits yaml.spec
      "CRITICAL: All containers MUST have resource limits defined";
    manifest;
}
```

**Kustomize Plugin**:
```yaml
# kubernetes/validators/resource-limits.yaml
apiVersion: builtin
kind: ValidatingWebhookConfiguration
metadata:
  name: resource-limits-enforcer
webhooks:
- name: enforce-limits.example.com
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: ["apps"]
    apiVersions: ["v1"]
    resources: ["deployments"]
  failurePolicy: Fail
  sideEffects: None
  admissionReviewVersions: ["v1"]
  clientConfig:
    service:
      name: resource-validator
      namespace: kube-system
```

#### Law #4: MANIFESTS MUST VALIDATE BEFORE MERGE

**Pre-commit**:
```bash
#!/usr/bin/env bash
set -euo pipefail

echo "📋 Validating Kubernetes manifests..."

VALIDATORS=(
    "kubeval --strict"
    "kubeconform -strict -summary"
    "kube-score score -"
    "conftest test -p policy/"
)

for env in dev staging prod; do
    echo "Validating $env..."
    
    MANIFESTS=$(kustomize build kubernetes/overlays/$env)
    
    for validator in "${VALIDATORS[@]}"; do
        echo "  Running: $validator"
        echo "$MANIFESTS" | $validator || {
            echo "❌ Validation failed for $env"
            exit 1
        }
    done
done

echo "✅ All manifests valid"
```

**OPA Policies** (Conftest):
```rego
# policy/resource-limits.rego
package main

deny[msg] {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    not container.resources.limits.cpu
    msg = sprintf("Container '%s' missing CPU limit", [container.name])
}

deny[msg] {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    not container.resources.limits.memory
    msg = sprintf("Container '%s' missing memory limit", [container.name])
}

deny[msg] {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    not container.securityContext.readOnlyRootFilesystem
    msg = sprintf("Container '%s' must use read-only root filesystem", [container.name])
}

deny[msg] {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    not container.securityContext.runAsNonRoot
    msg = sprintf("Container '%s' must run as non-root", [container.name])
}
```

#### Law #5: PRODUCTION REQUIRES HEALTH CHECKS

**Validation**:
```rego
# policy/health-checks.rego
package main

deny[msg] {
    input.kind == "Deployment"
    input.metadata.namespace == "production"
    container := input.spec.template.spec.containers[_]
    not container.livenessProbe
    msg = sprintf("Production container '%s' missing liveness probe", [container.name])
}

deny[msg] {
    input.kind == "Deployment"
    input.metadata.namespace == "production"
    container := input.spec.template.spec.containers[_]
    not container.readinessProbe
    msg = sprintf("Production container '%s' missing readiness probe", [container.name])
}
```

---

## 🛡️ SECURITY HARDENING (Mandatory Baseline)

### Network Policies (Default Deny)

```yaml
# kubernetes/base/default-deny.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: {{ .namespace }}
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

**Enforcement**: Every namespace MUST have a default-deny policy.

```bash
# Validator script
#!/usr/bin/env bash

for ns in $(kubectl get ns -o name | cut -d/ -f2); do
    if ! kubectl get networkpolicy -n "$ns" | grep -q default-deny; then
        echo "❌ Namespace $ns missing default-deny NetworkPolicy"
        exit 1
    fi
done
```

### Pod Security Standards

```yaml
# kubernetes/base/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    # MANDATORY: Enforce restricted PSS
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### Security Context (Non-Root Containers)

```yaml
# Mandatory security context for ALL containers
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
  seccompProfile:
    type: RuntimeDefault
```

**Validator**:
```rego
# policy/security-context.rego
package main

required_security_context := {
    "runAsNonRoot": true,
    "readOnlyRootFilesystem": true,
    "allowPrivilegeEscalation": false
}

deny[msg] {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    required_field := required_security_context[field]
    container.securityContext[field] != required_field
    msg = sprintf("Container '%s' security context field '%s' must be %v", 
                  [container.name, field, required_field])
}
```

---

## 🎯 CODE QUALITY GATES

### Pre-commit Hook Suite

```bash
#!/usr/bin/env bash
# .githooks/pre-commit
set -euo pipefail

echo "🚦 Running pre-commit checks..."

# 1. Format check
echo "📝 Checking code formatting..."
if ! nix fmt --check; then
    echo "❌ Code not formatted. Run: nix fmt"
    exit 1
fi

# 2. Nix flake check
echo "❄️  Checking Nix flake..."
if ! nix flake check --all-systems; then
    echo "❌ Nix flake check failed"
    exit 1
fi

# 3. YAML/JSON validation
echo "📋 Validating YAML/JSON..."
find . -name "*.yaml" -o -name "*.yml" | while read -r file; do
    if ! yamllint "$file"; then
        echo "❌ YAML validation failed: $file"
        exit 1
    fi
done

# 4. Kubernetes manifest validation
echo "☸️  Validating Kubernetes manifests..."
for env in dev staging prod; do
    if ! kustomize build "kubernetes/overlays/$env" | kubeval --strict; then
        echo "❌ K8s validation failed for $env"
        exit 1
    fi
done

# 5. Security scan
echo "🔒 Running security scans..."
if ! gitleaks detect --source . --verbose --no-git; then
    echo "❌ Secret detected!"
    exit 1
fi

if ! trivy config kubernetes/ --exit-code 1 --severity HIGH,CRITICAL; then
    echo "❌ Security issues found in configs"
    exit 1
fi

# 6. Policy validation (OPA)
echo "📜 Checking policies..."
if ! conftest test kubernetes/; then
    echo "❌ Policy violations detected"
    exit 1
fi

# 7. Shell script validation
echo "🐚 Checking shell scripts..."
find . -name "*.sh" | while read -r script; do
    if ! shellcheck "$script"; then
        echo "❌ Shellcheck failed: $script"
        exit 1
    fi
done

# 8. Terraform validation (if exists)
if [ -d "terraform" ]; then
    echo "🏗️  Validating Terraform..."
    terraform fmt -check -recursive terraform/
    terraform validate terraform/
fi

echo "✅ All pre-commit checks passed!"
```

### CI/CD Quality Gates

```yaml
# .github/workflows/quality-gate.yaml
name: Quality Gate

on:
  pull_request:
    branches: [main, develop]

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Nix
        uses: cachix/install-nix-action@v20
      
      # GATE 1: Code Quality
      - name: Code Quality
        run: |
          nix fmt --check
          nix flake check --all-systems
      
      # GATE 2: Security
      - name: Security Scan
        run: |
          nix develop --command gitleaks detect --source . --verbose
          nix develop --command trivy config kubernetes/ --exit-code 1
          nix develop --command trivy fs --exit-code 1 .
      
      # GATE 3: Manifest Validation
      - name: Validate Manifests
        run: |
          for env in dev staging prod; do
            nix develop --command bash -c "
              kustomize build kubernetes/overlays/$env | kubeval --strict
              kustomize build kubernetes/overlays/$env | conftest test -
            "
          done
      
      # GATE 4: Build Test
      - name: Build All Images
        run: |
          nix build .#api-image
          nix build .#worker-image
      
      # GATE 5: Integration Tests
      - name: Integration Tests
        run: |
          nix build .#checks.integration-tests
      
      # GATE 6: Performance Baseline
      - name: Performance Check
        run: |
          # Ensure image sizes are reasonable
          IMAGE_SIZE=$(docker load < result | grep "Loaded image" | awk '{print $NF}')
          if [ "$IMAGE_SIZE" -gt 500000000 ]; then  # 500MB
            echo "❌ Image too large: $IMAGE_SIZE bytes"
            exit 1
          fi
      
      # GATE 7: Documentation
      - name: Documentation Check
        run: |
          # Ensure critical docs exist
          [ -f README.md ] || exit 1
          [ -f ARCHITECTURE.md ] || exit 1
          [ -d docs/runbooks ] || exit 1
          
          # Ensure README has quickstart
          grep -q "Quickstart" README.md || exit 1
```

---

## 📊 METRICS & OBSERVABILITY (Required Baseline)

### Mandatory Prometheus Annotations

```yaml
# Every deployment MUST have these annotations
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  template:
    metadata:
      annotations:
        # MANDATORY
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
```

**Validator**:
```rego
# policy/observability.rego
package main

deny[msg] {
    input.kind == "Deployment"
    not input.spec.template.metadata.annotations["prometheus.io/scrape"]
    msg = "Deployment must have prometheus.io/scrape annotation"
}

deny[msg] {
    input.kind == "Deployment"
    not input.spec.template.metadata.annotations["prometheus.io/port"]
    msg = "Deployment must have prometheus.io/port annotation"
}
```

### Required Metrics

**Every service MUST expose**:
```
# RED metrics (mandatory)
- request_total (counter)
- request_duration_seconds (histogram)
- request_errors_total (counter)

# Resource metrics (mandatory)
- process_cpu_seconds_total
- process_resident_memory_bytes
- go_goroutines (for Go apps)

# Business metrics (recommended)
- business_events_total
- active_users_gauge
```

**Validation**:
```bash
#!/usr/bin/env bash
# scripts/validate-metrics.sh

REQUIRED_METRICS=(
    "request_total"
    "request_duration_seconds"
    "request_errors_total"
)

SERVICE_URL=$1

for metric in "${REQUIRED_METRICS[@]}"; do
    if ! curl -s "$SERVICE_URL/metrics" | grep -q "$metric"; then
        echo "❌ Missing required metric: $metric"
        exit 1
    fi
done

echo "✅ All required metrics present"
```

---

## 🔄 DEPLOYMENT RIGOR

### Mandatory Rollout Strategy

```yaml
# Production deployments MUST have:
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3  # Minimum 3 for HA
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # Zero-downtime required
  minReadySeconds: 10
  progressDeadlineSeconds: 600
```

### Pod Disruption Budget (Mandatory for Prod)

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: myapp
spec:
  minAvailable: 2  # Ensures availability during disruptions
  selector:
    matchLabels:
      app: myapp
```

### Horizontal Pod Autoscaler (Prod Requirement)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

---

## 🧪 TESTING REQUIREMENTS

### Minimum Test Coverage

```nix
{
  # Every package MUST pass tests
  packages.api = pkgs.buildGoModule {
    pname = "api";
    src = ./services/api;
    
    # MANDATORY: Run tests
    checkPhase = ''
      go test -v -race -coverprofile=coverage.out ./...
      
      # Enforce minimum coverage
      COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//')
      if [ $(echo "$COVERAGE < 80" | bc) -eq 1 ]; then
        echo "❌ Coverage $COVERAGE% < 80% minimum"
        exit 1
      fi
    '';
  };
}
```

### Integration Test Requirements

```bash
#!/usr/bin/env bash
# tests/integration/test-suite.sh
set -euo pipefail

# 1. Spin up test cluster
kind create cluster --name test

# 2. Deploy application
kustomize build kubernetes/overlays/dev | kubectl apply -f -

# 3. Wait for ready
kubectl wait --for=condition=ready pod -l app=api --timeout=300s

# 4. Run tests
for test in tests/integration/*_test.sh; do
    echo "Running $test..."
    if ! bash "$test"; then
        echo "❌ Test failed: $test"
        kind delete cluster --name test
        exit 1
    fi
done

# 5. Cleanup
kind delete cluster --name test

echo "✅ All integration tests passed"
```

---

## 📝 DOCUMENTATION REQUIREMENTS

### Mandatory Files

```bash
# Repository MUST have:
□ README.md              # Quickstart (<2 min)
□ ARCHITECTURE.md        # Design decisions
□ CONTRIBUTING.md        # How to contribute
□ CHANGELOG.md           # Version history
□ docs/runbooks/         # Operational procedures
□ docs/decisions/        # ADRs

# Enforcement
if [ ! -f README.md ] || [ ! -f ARCHITECTURE.md ]; then
    echo "❌ Missing required documentation"
    exit 1
fi
```

### ADR Template (Mandatory Format)

```markdown
# ADR-XXX: [Title]

Date: YYYY-MM-DD
Status: [Proposed | Accepted | Deprecated | Superseded]
Deciders: [List of people involved]

## Context

[What is the issue we're facing?]

## Decision

[What did we decide?]

## Consequences

### Positive
- [Benefit 1]

### Negative
- [Cost 1]

### Risks
- [Risk 1]

## Alternatives Considered

### Alternative 1: [Name]
- Pros: [...]
- Cons: [...]
- Why rejected: [...]

## Implementation Notes

[Technical details]

## References

- [Link 1]
```

---

## 🚨 INCIDENT RESPONSE REQUIREMENTS

### Runbook Template (Mandatory)

```markdown
# Runbook: [Service Name] - [Incident Type]

## Severity: [P0 | P1 | P2 | P3]

## Symptoms

- [Observable symptom 1]
- [Observable symptom 2]

## Investigation Steps

1. Check metrics:
   ```bash
   kubectl top pods -n production
   kubectl logs -f deployment/api -n production
   ```

2. Check recent changes:
   ```bash
   git log --since="1 hour ago" --oneline
   kubectl rollout history deployment/api
   ```

## Resolution Steps

### Quick Fix (< 5 min)

1. Rollback deployment:
   ```bash
   kubectl rollout undo deployment/api -n production
   ```

### Root Cause Fix

[Detailed steps]

## Validation

- [ ] Metrics returned to normal
- [ ] Error rate < 0.1%
- [ ] Latency p95 < 200ms

## Post-Mortem

Create post-mortem doc at: `docs/postmortems/YYYY-MM-DD-incident.md`
```

---

## 🎯 ENFORCEMENT AUTOMATION

### Comprehensive Nix Check

```nix
{
  checks = {
    # All these MUST pass before merge
    
    format-check = pkgs.runCommand "format-check" {} ''
      nixpkgs-fmt --check ${./.}
      prettier --check "**/*.{yaml,yml,json,md}"
      touch $out
    '';
    
    security-scan = pkgs.runCommand "security-scan" {
      buildInputs = [ pkgs.trivy pkgs.gitleaks ];
    } ''
      gitleaks detect --source ${./.} --verbose --no-git
      trivy config ${./.}/kubernetes --exit-code 1
      touch $out
    '';
    
    manifest-validation = pkgs.runCommand "manifest-validation" {
      buildInputs = [ pkgs.kustomize pkgs.kubeval ];
    } ''
      for env in dev staging prod; do
        kustomize build ${./.}/kubernetes/overlays/$env | kubeval --strict
      done
      touch $out
    '';
    
    policy-validation = pkgs.runCommand "policy-validation" {
      buildInputs = [ pkgs.conftest ];
    } ''
      conftest test ${./.}/kubernetes
      touch $out
    '';
    
    test-suite = pkgs.runCommand "test-suite" {} ''
      # Run all tests
      ${self.packages.${system}.api}/bin/api test
      touch $out
    '';
  };
}
```

---

## 📋 FINAL CHECKLIST (Every PR Must Pass)

```yaml
# .github/PULL_REQUEST_TEMPLATE.md
## Pre-merge Checklist

### Code Quality
- [ ] All tests pass (`nix build .#checks`)
- [ ] Code formatted (`nix fmt`)
- [ ] No linting errors
- [ ] Test coverage ≥ 80%

### Security
- [ ] No secrets in code (gitleaks passed)
- [ ] All images scanned (trivy passed)
- [ ] Security policies validated (conftest passed)
- [ ] Dependencies up to date

### Infrastructure
- [ ] K8s manifests validated (kubeval passed)
- [ ] Resource limits defined
- [ ] Health checks configured
- [ ] Observability annotations present

### Documentation
- [ ] README updated (if needed)
- [ ] ARCHITECTURE.md updated (if needed)
- [ ] ADR created (for significant changes)
- [ ] Runbook created/updated

### Deployment
- [ ] Tested in dev environment
- [ ] Rollback procedure documented
- [ ] Monitoring alerts configured
- [ ] PDB defined for production

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing done:

## Rollout Plan
Describe deployment strategy:
```

---

## 🏆 BADGES OF HONOR

Add these to your README when all requirements are met:

```markdown
![Security Scan](https://github.com/org/repo/workflows/Security/badge.svg)
![Tests](https://github.com/org/repo/workflows/Tests/badge.svg)
![Coverage](https://img.shields.io/codecov/c/github/org/repo)
![Manifests](https://github.com/org/repo/workflows/K8s%20Validation/badge.svg)
```

---

## 💎 GOLDEN RULE OF RIGOR

> **"If it's not automated, it will be forgotten. If it's not enforced, it will be violated. If it's not tested, it's broken."**

**AUTOMATE EVERYTHING. TRUST NOTHING. VERIFY ALWAYS.**

---

*This rigor document is not optional. It's the difference between "works on my machine" and "works in production for 3 years straight without incident."*

**Discipline is freedom. Constraints breed excellence.** 🎯
