#!/usr/bin/env python3
"""
Test script for Cerebro Reranker Integration.
"""

import sys
import os
import logging
from typing import List

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from cerebro.core.rerank import rerank, get_reranker_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_reranker")

def test_reranking():
    query = "What is the capital of France?"
    documents = [
        "Berlin is the capital of Germany.",
        "Paris is the capital of France.",
        "London is the capital of the United Kingdom.",
        "Madrid is the capital of Spain.",
        "France has many cities, but Paris is the most famous."
    ]
    
    logger.info("--- Testing Default Reranking (Service Preferred) ---")
    try:
        results = rerank(query, documents, top_k=3)
        
        print(f"Query: {query}")
        print("Top 3 Results:")
        for idx, score, doc in results:
            print(f"[{idx}] {score:.4f} : {doc}")
    except Exception as e:
        logger.error(f"Default reranking failed (likely due to missing deps for fallback): {e}")
        
    # Check client mode
    client = get_reranker_client()
    print(f"\nClient Mode: {client.mode}")
    print(f"Service URL: {client.service_url}")
    
    # Test fallback by pointing to invalid URL
    logger.info("\n--- Testing Fallback (Invalid URL) ---")
    
    # Force a new client with bad URL
    from cerebro.core.rerank_client import CerebroRerankerClient
    bad_client = CerebroRerankerClient(service_url="http://localhost:9999", timeout=0.5)
    
    try:
        fallback_results = bad_client.rerank(query, documents, top_k=3)
        print("Fallback Results (should match local model):")
        for idx, score, doc in fallback_results:
            print(f"[{idx}] {score:.4f} : {doc}")
    except Exception as e:
        print(f"Fallback failed: {e}")

if __name__ == "__main__":
    test_reranking()
