#!/bin/bash
# .gitlab-ci/scripts/build.sh
# Build script for Docker image

set -e

echo "Building Docker image..."

# Login to registry
docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY

# Build image
docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA -t $CI_REGISTRY_IMAGE:latest .

# Push image
docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
docker push $CI_REGISTRY_IMAGE:latest

echo "✅ Docker image built and pushed successfully"
