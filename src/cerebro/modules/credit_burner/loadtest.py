#!/usr/bin/env python3
"""
Load Test Module - Burn GenAI App Builder Credits

Consolidated from burn_credits_loadtest.py
Uses validated SearchServiceClient with summary_spec
"""
import os
import sys
import time
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from cerebro.core.gcp import VertexAISearch


# Sample queries for realistic load testing
SAMPLE_QUERIES = [
    "What is artificial intelligence and how does it work?",
    "Explain machine learning algorithms",
    "What are the applications of deep learning?",
    "How does natural language processing work?",
    "What is the difference between supervised and unsupervised learning?",
    "Explain neural networks architecture",
    "What are transformers in AI?",
    "How do large language models work?",
    "What is reinforcement learning?",
    "Explain computer vision techniques",
    "What is generative AI?",
    "How does recommendation systems work?",
    "What are the ethical considerations in AI?",
    "Explain explainable AI (XAI)",
    "What is edge AI and its benefits?",
    "How does AI help in healthcare?",
    "What are GANs and their applications?",
    "Explain AutoML and its use cases",
    "What is federated learning?",
    "How does AI impact cybersecurity?",
]


def run_loadtest(
    num_queries: int,
    data_store_id: str,
    max_workers: int = 10,
    queries: Optional[List[str]] = None,
    project_id: Optional[str] = None,
    location: str = "global",
    auto_confirm: bool = False
) -> dict:
    """
    Run load test to consume GenAI App Builder credits

    Args:
        num_queries: Total number of queries to execute
        data_store_id: Vertex AI Data Store ID
        max_workers: Parallel workers (be careful with rate limits!)
        queries: Custom queries (uses SAMPLE_QUERIES if None)
        project_id: GCP project ID (auto-detected if None)
        location: GCP location
        auto_confirm: Skip confirmation prompt

    Returns:
        Dict with test results
    """
    query_list = queries or SAMPLE_QUERIES

    print("="*60)
    print("🔥 PHANTOM - GenAI App Builder Load Test")
    print("="*60)

    # Setup search client
    search = VertexAISearch(
        project_id=project_id,
        location=location,
        data_store_id=data_store_id
    )

    print(f"\n📊 Configuration:")
    print(f"   Project: {search.project_id}")
    print(f"   Data Store: {data_store_id}")
    print(f"   Total Queries: {num_queries}")
    print(f"   Workers: {max_workers}")

    # Cost estimate
    estimated_cost = (num_queries / 1000) * VertexAISearch.SEARCH_ENTERPRISE_COST_PER_1K

    print(f"\n💰 Cost Estimate:")
    print(f"   Rate: ${VertexAISearch.SEARCH_ENTERPRISE_COST_PER_1K} / 1,000 queries")
    print(f"   Total Cost: ~${estimated_cost:.2f} USD")

    # Confirmation
    if not auto_confirm and os.getenv("AUTO_CONFIRM") != "true":
        response = input("\n🚀 Continue with load test? (y/n): ").strip().lower()
        if response != 'y':
            print("❌ Cancelled")
            return {"status": "cancelled"}

    print(f"\n⏳ Executing {num_queries} queries...")
    print("=" * 60)

    # Prepare queries
    queries_to_run = []
    for i in range(num_queries):
        query_text = query_list[i % len(query_list)]
        queries_to_run.append((i, query_text))

    # Metrics
    successful = 0
    failed = 0
    total_cost = 0.0
    start_time = time.time()

    # Execute in parallel
    def execute_query(query_id, query_text):
        try:
            response = search.grounded_search(query_text)
            return {
                'status': 'success',
                'query_id': query_id,
                'cost': response.cost_estimate
            }
        except Exception as e:
            return {
                'status': 'failed',
                'query_id': query_id,
                'error': str(e)
            }

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(execute_query, qid, qtxt): qid
            for qid, qtxt in queries_to_run
        }

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            if result['status'] == 'success':
                successful += 1
                total_cost += result['cost']
            else:
                failed += 1

            # Progress
            if len(results) % 50 == 0:
                elapsed = time.time() - start_time
                qps = len(results) / elapsed if elapsed > 0 else 0
                print(f"   [{len(results)}/{num_queries}] "
                      f"Success: {successful} | "
                      f"Failed: {failed} | "
                      f"QPS: {qps:.2f} | "
                      f"Cost: ${total_cost:.4f}")

    duration = time.time() - start_time
    qps = num_queries / duration if duration > 0 else 0

    # Final report
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    print(f"\n⏱️  Duration: {duration:.2f}s")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Queries/sec: {qps:.2f}")
    print(f"💰 Total cost: ${total_cost:.4f} USD")

    if failed > 0:
        print(f"\n⚠️  {failed} queries failed")

    print("\n✅ Load test complete!")

    return {
        "status": "completed",
        "total_queries": num_queries,
        "successful": successful,
        "failed": failed,
        "total_cost_usd": total_cost,
        "duration_seconds": duration,
        "queries_per_second": qps
    }


def main():
    """CLI entry point"""
    data_store_id = os.getenv("DATA_STORE_ID")
    num_queries = int(os.getenv("NUM_QUERIES", "100"))
    max_workers = int(os.getenv("MAX_WORKERS", "10"))

    if not data_store_id:
        print("❌ DATA_STORE_ID not configured!")
        print("\n🔧 FIX:")
        print("   1. Run: phantom gcp datastores list")
        print("   2. Copy the data store ID")
        print("   3. Export: export DATA_STORE_ID='your-id-here'")
        sys.exit(1)

    run_loadtest(
        num_queries=num_queries,
        data_store_id=data_store_id,
        max_workers=max_workers
    )


if __name__ == "__main__":
    main()
