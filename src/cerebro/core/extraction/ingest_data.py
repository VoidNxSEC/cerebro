#!/usr/bin/env python3
"""
03_ingest_data.py - Document ingestion via Discovery Engine.
Instead of generating embeddings manually (expensive), import into the Data Store.
Vertex AI Search handles indexing/vectorization using GCP credits.
"""
import os
import json
from typing import List, Dict
from google.cloud import discoveryengine_v1beta as discoveryengine
from google.api_core.client_options import ClientOptions

def import_documents(project_id: str, location: str, data_store_id: str, input_jsonl: str):
    print("🚀 Starting document ingestion (credit-funded)...")

    # 1. Configure client for Discovery Engine endpoint
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global" else None
    )
    client = discoveryengine.DocumentServiceClient(client_options=client_options)

    # 2. Define the Data Store path
    parent = client.branch_path(
        project=project_id,
        location=location,
        data_store=data_store_id,
        branch="default_branch"
    )

    # 3. Prepare the Import Request (GCS or Inline)
    # For large datasets, upload the JSONL to GCS first.
    # Use GCS for bulk ingestion.

    print("⚠️  For bulk ingestion, upload 'all_artifacts.jsonl' to a GCS bucket.")
    gcs_uri = f"gs://{project_id}-staging/all_artifacts.jsonl"

    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(input_uris=[gcs_uri]),
        # INCREMENTAL mode allows re-running without breaking existing data
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
    )

    # 4. Trigger the long-running operation
    operation = client.import_documents(request=request)
    print(f"⏳ Import started: {operation.operation.name}")
    print("   Vertex AI Search is now generating embeddings and indexing (covered by credits).")

    # Optional: operation.result() to wait for completion

if __name__ == "__main__":
    # Exemplo de uso
    import_documents(
        project_id=os.getenv("GCP_PROJECT"),
        location="global",
        data_store_id=os.getenv("DATA_STORE_ID"),
        input_jsonl="data/analyzed/all_artifacts.jsonl"
    )
