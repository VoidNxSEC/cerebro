# .gitlab-ci/ Directory

This directory contains GitLab CI/CD configuration and helper scripts for the Cerebro project.

## Directory Structure

```
.gitlab-ci/
├── stages/
│   ├── validate.yml      # Validation stage job configurations
│   ├── test.yml          # Test stage job configurations (future)
│   ├── build.yml         # Build stage job configurations (future)
│   ├── deploy.yml        # Deploy stage job configurations (future)
│   └── monitor.yml       # Monitor stage job configurations (future)
├── scripts/
│   ├── setup.sh          # Setup script for CI environment
│   ├── test.sh           # Test execution script
│   ├── build.sh          # Docker build script
│   └── deploy.sh         # Cloud Run deployment script
└── README.md             # This file
```

## Usage

### Main Configuration
The main GitLab CI/CD configuration is in `.gitlab-ci.yml` at the repository root. This file defines:
- Pipeline stages
- Job definitions
- Caching and artifacts
- Environment variables

### Stage Configurations
Individual stage configurations are in the `stages/` directory:
- `validate.yml` - Import and syntax validation jobs
- Additional stage files can be created for organization

### Helper Scripts
Helper scripts in the `scripts/` directory are used by CI/CD jobs:
- `setup.sh` - Installs Poetry and dependencies
- `test.sh` - Runs all tests and quality checks
- `build.sh` - Builds and pushes Docker image
- `deploy.sh` - Deploys to Cloud Run

## Running Locally

To simulate the GitLab CI/CD pipeline locally:

```bash
# Run the full local CI pipeline
just ci-local

# Run individual checks
just validate-imports
just validate-syntax
just lint
just format
just test-unit
```

## Configuration

### Environment Variables
Set the following variables in GitLab project settings (Settings → CI/CD → Variables):

- `GCP_PROJECT_ID` - Google Cloud Project ID
- `GCP_REGION` - Google Cloud Region (default: us-central1)
- `DATA_STORE_ID` - Vertex AI Data Store ID
- `GCP_SERVICE_ACCOUNT_KEY` - Base64-encoded GCP service account key

### Protected Variables
Mark the following as protected and masked:
- `GCP_SERVICE_ACCOUNT_KEY`
- `DATA_STORE_ID`

## Troubleshooting

### Pipeline Not Running
1. Check `.gitlab-ci.yml` syntax using GitLab CI Lint tool
2. Verify branch protection rules
3. Check project settings → CI/CD
4. Ensure GitLab Runner is available

### Jobs Failing
1. Check job logs in GitLab UI
2. Run `just ci-local` to test locally
3. Verify environment variables are set
4. Check Docker image availability

### Docker Build Issues
1. Verify `Dockerfile` syntax
2. Check `.dockerignore` for excluded files
3. Ensure `poetry.lock` is committed
4. Test build locally: `docker build -t cerebro:latest .`

## References

- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [GitLab Runner Documentation](https://docs.gitlab.com/runner/)
- [Main CI/CD Documentation](../docs/GITLAB_CI_CD.md)
- [Migration Guide](../docs/GITLAB_CI_MIGRATION.md)
