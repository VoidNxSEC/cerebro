#!/usr/bin/env python3
"""
CEREBRO Embedding Server - GCP Vertex AI Edition
Embedding server using Vertex AI text-embedding-004.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import vertexai
from vertexai.language_models import TextEmbeddingModel
import os
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cerebro-embeddings")

app = FastAPI(title="CEREBRO Embeddings API", version="1.0.0")

class EmbeddingRequest(BaseModel):
    content: str
    task_type: str = "RETRIEVAL_DOCUMENT"  # or RETRIEVAL_QUERY

class EmbeddingResponse(BaseModel):
    embedding: List[float]
    dimension: int
    model: str
    cost_estimate_usd: float

class BatchEmbeddingRequest(BaseModel):
    texts: List[str]
    task_type: str = "RETRIEVAL_DOCUMENT"

class BatchEmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    dimension: int
    model: str
    total_tokens: int
    cost_estimate_usd: float

# Global state
embedding_model = None
project_id = None
location = None

@app.on_event("startup")
async def startup():
    global embedding_model, project_id, location

    project_id = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION", "us-central1")

    if not project_id:
        raise ValueError("GCP_PROJECT_ID environment variable required")

    logger.info(f"🧠 Initializing Vertex AI Embeddings - Project: {project_id}, Location: {location}")

    # Initialize Vertex AI
    vertexai.init(project=project_id, location=location)

    # Load embedding model
    embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")

    logger.info("✅ CEREBRO Embedding Server ready!")

@app.post("/embedding", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest):
    """
    Generate a single embedding using Vertex AI text-embedding-004
    Compatible with llama.cpp format for drop-in replacement
    """
    if not embedding_model:
        raise HTTPException(500, "Embedding model not initialized")

    try:
        start = time.time()

        # Generate embedding via Vertex AI
        embeddings = embedding_model.get_embeddings([request.content])

        latency = time.time() - start

        # Vertex AI text-embedding-004: 768 dimensions
        embedding_vector = embeddings[0].values

        # Cost estimate: ~$0.00001 per 1k characters (rough estimate)
        chars = len(request.content)
        cost = (chars / 1000) * 0.00001

        logger.info(f"💰 Generated embedding: {chars} chars, {latency:.3f}s, ~${cost:.6f}")

        return EmbeddingResponse(
            embedding=embedding_vector,
            dimension=len(embedding_vector),
            model="text-embedding-004",
            cost_estimate_usd=cost
        )

    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(500, f"Embedding failed: {str(e)}")

@app.post("/embeddings/batch", response_model=BatchEmbeddingResponse)
async def generate_batch_embeddings(request: BatchEmbeddingRequest):
    """
    Generate multiple embeddings in batch (more efficient for bulk operations)
    """
    if not embedding_model:
        raise HTTPException(500, "Embedding model not initialized")

    try:
        start = time.time()

        # Batch embedding via Vertex AI
        embeddings = embedding_model.get_embeddings(request.texts)

        latency = time.time() - start

        embedding_vectors = [emb.values for emb in embeddings]

        # Cost calculation
        total_chars = sum(len(text) for text in request.texts)
        cost = (total_chars / 1000) * 0.00001

        logger.info(f"💰 Batch embeddings: {len(request.texts)} texts, {total_chars} chars, {latency:.3f}s, ~${cost:.6f}")

        return BatchEmbeddingResponse(
            embeddings=embedding_vectors,
            dimension=len(embedding_vectors[0]) if embedding_vectors else 0,
            model="text-embedding-004",
            total_tokens=total_chars // 4,  # rough token estimate
            cost_estimate_usd=cost
        )

    except Exception as e:
        logger.error(f"Batch embedding failed: {e}")
        raise HTTPException(500, f"Batch embedding failed: {str(e)}")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy" if embedding_model else "initializing",
        "model": "text-embedding-004",
        "dimensions": 768,
        "provider": "Google Cloud Vertex AI",
        "project_id": project_id,
        "location": location,
        "credits_remaining": "check GCP console"
    }

@app.get("/stats")
async def stats():
    """Quick stats about the embedding service"""
    return {
        "model": "text-embedding-004",
        "max_input_tokens": 2048,
        "output_dimensions": 768,
        "task_types": [
            "RETRIEVAL_DOCUMENT",
            "RETRIEVAL_QUERY",
            "SEMANTIC_SIMILARITY",
            "CLASSIFICATION",
            "CLUSTERING"
        ],
        "cost_per_1k_chars": "$0.00001 (estimate)",
        "message": "Cerebro Embedding Server operational"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
