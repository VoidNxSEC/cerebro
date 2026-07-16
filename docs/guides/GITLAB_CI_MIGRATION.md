# GitHub Actions to GitLab CI Migration Guide

## Overview

This guide documents the migration from GitHub Actions to GitLab CI/CD for the Cerebro project. Both systems provide CI/CD automation, but they have different syntax and concepts.

## Key Differences

### Syntax
- **GitHub Actions:** YAML with `jobs`, `steps`, `uses` keywords
- **GitLab CI:** YAML with `stages`, `jobs`, `script` keywords

### Runners
- **GitHub Actions:** `runs-on` specifies runner type (ubuntu-latest, self-hosted, etc.)
- **GitLab CI:** `image` specifies Docker image or `tags` for runner selection

### Secrets
- **GitHub Actions:** `secrets.SECRET_NAME` or `vars.VARIABLE_NAME`
- **GitLab CI:** `$SECRET_NAME` or `$VARIABLE_NAME` (defined in project settings)

### Artifacts
- **GitHub Actions:** `actions/upload-artifact@v3` action
- **GitLab CI:** `artifacts:` section in job definition

### Caching
- **GitHub Actions:** `actions/cache@v3` action
- **GitLab CI:** `cache:` section in job definition

## Migration Mapping

### GitHub Actions → GitLab CI

| GitHub Actions | GitLab CI | Notes |
|---|---|---|
| `jobs` | `stages` + `jobs` | GitLab uses stages for organization |
| `runs-on` | `image` or `tags` | Use Docker image or runner tags |
| `uses` | `image` | Specify Docker image directly |
| `steps` | `script` | Use script array for commands |
| `secrets.VAR` | `$VAR` | Define in project settings |
| `artifacts` | `artifacts:` | Similar structure |
| `cache` | `cache:` | Similar structure |
| `if` conditions | `only:` / `except:` | Use for conditional execution |
| `with:` | Environment variables | Use `variables:` or `env:` |

## Migrated Workflows

### CI Workflow
- **GitHub:** `.github/workflows/ci.yml`
- **GitLab:** `.gitlab-ci.yml` (stages: validate, test)

**GitHub Actions:**
```yaml
jobs:
  validate-commands:
    runs-on: [self-hosted, nixos]
    steps:
      - uses: actions/checkout@v4
      - run: chmod +x ./scripts/ci-test.sh && ./scripts/ci-test.sh
```

**GitLab CI:**
```yaml
validate:imports:
  stage: validate
  image: python:3.13-slim
  script:
    - poetry install --no-root
    - poetry run python -c "from phantom.core import gcp"
```

### Deploy Workflow
- **GitHub:** `.github/workflows/deploy.yml`
- **GitLab:** `.gitlab-ci.yml` (stages: build, deploy)

**GitHub Actions:**
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
      - uses: google-github-actions/deploy-cloudrun@v2
```

**GitLab CI:**
```yaml
deploy:cloud-run:
  stage: deploy
  image: google/cloud-sdk:alpine
  script:
    - echo $GCP_SERVICE_ACCOUNT_KEY | base64 -d > ${HOME}/gcp-key.json
    - gcloud auth activate-service-account --key-file ${HOME}/gcp-key.json
    - gcloud run deploy cerebro-api --source .
```

## Setup Steps

1. **Create `.gitlab-ci.yml`** in repository root
   - Define stages: validate, test, build, deploy, monitor
   - Configure jobs for each stage
   - Set up caching and artifacts

2. **Configure CI/CD variables** in GitLab project settings
   - Go to Project Settings → CI/CD → Variables
   - Add GCP_PROJECT_ID, GCP_REGION, GCP_SERVICE_ACCOUNT_KEY, etc.
   - Mark sensitive variables as protected and masked

3. **Set up GitLab Runner** (optional, for self-hosted)
   - Install GitLab Runner on your infrastructure
   - Configure executor (Docker, NixOS, etc.)
   - Register runner with GitLab project

4. **Enable protected branches** for main branch
   - Go to Project Settings → Repository → Protected Branches
   - Require pipeline to pass before merge
   - Require code review before merge

5. **Configure merge request rules** to require pipeline
   - Go to Project Settings → Merge requests
   - Require all discussions to be resolved
   - Require pipeline to succeed

## Testing Migration

### Local Testing
```bash
# Simulate GitLab CI locally
just ci-local

# Run individual checks
just validate-imports
just validate-syntax
just lint
just format
just test-unit
```

### GitLab Testing
1. Push to feature branch
2. Create merge request
3. Monitor pipeline in GitLab UI
4. Check job logs for errors
5. Iterate on configuration based on results

## Troubleshooting

### Pipeline Not Triggering
- Check `.gitlab-ci.yml` syntax (use GitLab CI Lint tool)
- Verify branch protection rules
- Check project settings → CI/CD
- Ensure GitLab Runner is available

### Jobs Failing
- Check job logs in GitLab UI
- Run `just ci-local` to test locally
- Verify environment variables are set
- Check Docker image availability

### Docker Image Issues
- Verify Docker image exists and is accessible
- Check image pull policies
- Verify registry credentials
- Test image locally: `docker pull <image>`

### GCP Authentication Issues
- Verify GCP_SERVICE_ACCOUNT_KEY is set correctly
- Check service account permissions
- Verify Cloud Run API is enabled
- Test authentication locally: `gcloud auth activate-service-account`

### Poetry/Dependency Issues
- Ensure `poetry.lock` is committed to repository
- Check `pyproject.toml` for syntax errors
- Verify all dependencies are available
- Run `poetry install` locally to test

## Key Differences in Behavior

### Caching
- **GitHub Actions:** Cache is per-branch and per-workflow
- **GitLab CI:** Cache is per-runner and per-job

### Artifacts
- **GitHub Actions:** Artifacts are retained for 90 days by default
- **GitLab CI:** Artifacts are retained for 30 days by default (configurable)

### Secrets
- **GitHub Actions:** Secrets are scoped to repository or organization
- **GitLab CI:** Variables are scoped to project or group

### Runners
- **GitHub Actions:** Shared runners are provided by GitHub
- **GitLab CI:** Shared runners are provided by GitLab.com (limited minutes)

## Migration Checklist

- [ ] Create `.gitlab-ci.yml` with all stages and jobs
- [ ] Create `Dockerfile` for containerization
- [ ] Create `.dockerignore` to exclude unnecessary files
- [ ] Update `pyproject.toml` with test dependencies
- [ ] Update `Justfile` with CI/CD recipes
- [ ] Create `.gitlab/merge_request_templates/default.md`
- [ ] Create documentation in `docs/GITLAB_CI_CD.md`
- [ ] Configure GitLab CI/CD variables in project settings
- [ ] Enable protected branches for main branch
- [ ] Test pipeline with merge request
- [ ] Monitor pipeline execution and logs
- [ ] Iterate on configuration based on results

## References

- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitLab Runner Documentation](https://docs.gitlab.com/runner/)
- [GitLab CI Lint Tool](https://docs.gitlab.com/ee/ci/lint.html)
- [Docker Documentation](https://docs.docker.com/)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
