#!/bin/bash
# .gitlab-ci/scripts/deploy.sh
# Deploy script for Cloud Run

set -e

echo "Deploying to Cloud Run..."

# Authenticate with GCP
echo $GCP_SERVICE_ACCOUNT_KEY | base64 -d > ${HOME}/gcp-key.json
gcloud auth activate-service-account --key-file ${HOME}/gcp-key.json
gcloud config set project $GCP_PROJECT_ID

# Deploy to Cloud Run
gcloud run deploy cerebro-api \
    --source . \
    --region $GCP_REGION \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars "GCP_PROJECT_ID=$GCP_PROJECT_ID,DATA_STORE_ID=$DATA_STORE_ID" \
    --memory 2Gi \
    --timeout 3600

echo "✅ Deployment to Cloud Run completed successfully"
