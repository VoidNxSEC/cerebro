# GitLab CI/CD Pipeline Documentation

## Overview

This document describes the GitLab CI/CD pipeline for the Cerebro project. The pipeline automates testing, linting, building, and deployment of the Knowledge Extraction and RAG platform.

## Pipeline Stages

### 1. Validate Stage
- **Purpose:** Quick syntax and import checks
- **Jobs:**
  - `validate:imports` - Verify Python imports and dependencies
  - `validate:syntax` - Check Python syntax compilation

### 2. Test Stage
- **Purpose:** Comprehensive testing and code quality checks
- **Jobs:**
  - `test:unit` - Unit tests with coverage reporting
  - `test:integration` - Integration tests (optional, allows failure)
  - `test:lint` - Code linting with ruff
  - `test:format` - Code format checking
  - `test:cli` - CLI command verification

### 3. Build Stage
- **Purpose:** Build Docker image
- **Jobs:**
  - `build:docker` - Build and push Docker image (manual trigger)

### 4. Deploy Stage
- **Purpose:** Deploy to production
- **Jobs:**
  - `deploy:cloud-run` - Deploy to Google Cloud Run (manual trigger)

### 5. Monitor Stage
- **Purpose:** Health checks and monitoring
- **Jobs:**
  - `monitor:health` - System health verification

## Setup Instructions

### 1. Configure GitLab CI/CD Variables

Go to **Project Settings → CI/CD → Variables** and add the following variables:

```
GCP_PROJECT_ID = gen-lang-client-0530325234
GCP_REGION = us-central1
DATA_STORE_ID = <your-data-store-id>
GCP_SERVICE_ACCOUNT_KEY = <base64-encoded-key>
```

**Note:** The `GCP_SERVICE_ACCOUNT_KEY` should be a base64-encoded JSON key file from your GCP service account.

### 2. Configure GitLab Runner

**Option A: Use GitLab.com shared runners (Docker)**
```bash
# No configuration needed, uses default Docker runners
# Pipeline will automatically use shared runners
```

**Option B: Use self-hosted NixOS runner**
```bash
# Install GitLab Runner on NixOS
# Configure to use NixOS executor
# See: https://docs.gitlab.com/runner/
```

### 3. Enable Protected Branches

Go to **Project Settings → Repository → Protected Branches**:
- Protect `main` branch
- Require pipeline to pass before merge
- Require code review before merge

## Running Pipelines

### Automatic Triggers
- Push to `main` branch
- Merge requests to `main` branch

### Manual Triggers
- Build Docker image: Click "Play" on `build:docker` job
- Deploy to Cloud Run: Click "Play" on `deploy:cloud-run` job

## Monitoring Pipeline

### View Pipeline Status
1. Go to **CI/CD → Pipelines**
2. Click on pipeline to view details
3. Click on job to view logs

### View Test Coverage
1. Go to **CI/CD → Pipelines**
2. Click on `test:unit` job
3. View coverage report in job output

### View Artifacts
1. Go to **CI/CD → Pipelines**
2. Click on job
3. Download artifacts (coverage.xml, etc.)

## Troubleshooting

### Pipeline Fails on Import Tests
- Check that all dependencies are listed in `pyproject.toml`
- Run `poetry install` locally to verify
- Check that the module paths are correct

### Pipeline Fails on Linting
- Run `poetry run ruff check --fix src/ tests/` locally
- Commit fixes and push
- Verify ruff configuration in `pyproject.toml`

### Pipeline Fails on Tests
- Run `poetry run pytest tests/ -v` locally
- Fix failing tests
- Commit and push
- Check test markers and pytest configuration

### Docker Build Fails
- Check `Dockerfile` syntax
- Verify all required files are included
- Check `.dockerignore` for excluded files
- Ensure `poetry.lock` is committed to repository

### Cloud Run Deployment Fails
- Verify GCP credentials are correct
- Check that Cloud Run API is enabled
- Verify service account has necessary permissions
- Check Cloud Run quotas and limits

## Best Practices

1. **Always run tests locally before pushing**
   ```bash
   just quality  # Runs lint, format, and tests
   ```

2. **Keep pipeline fast**
   - Use caching for dependencies
   - Run tests in parallel when possible
   - Skip unnecessary jobs for documentation changes

3. **Use protected branches**
   - Require pipeline to pass before merge
   - Require code review before merge

4. **Monitor pipeline metrics**
   - Track pipeline duration
   - Monitor test coverage trends
   - Alert on pipeline failures

5. **Use merge request templates**
   - Ensure all PRs follow the template
   - Include testing checklist
   - Link related issues

## Advanced Configuration

### Caching Strategy
```yaml
cache:
  paths:
    - .venv/
    - .cache/pip/
  key:
    files:
      - poetry.lock
```

### Artifacts Retention
```yaml
artifacts:
  paths:
    - coverage.xml
  expire_in: 30 days
```

### Conditional Execution
```yaml
only:
  - main
  - merge_requests
  - tags
```

## Local Testing

### Simulate GitLab CI Locally
```bash
# Run the local CI pipeline
just ci-local

# Run specific checks
just validate-imports
just validate-syntax
just lint
just format
just test-unit
```

## References

- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [GitLab Runner Documentation](https://docs.gitlab.com/runner/)
- [Docker Documentation](https://docs.docker.com/)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
