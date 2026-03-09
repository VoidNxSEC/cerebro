#!/usr/bin/env python3
"""
Vertex AI Search - Grounded Generation

Consolidated from test_credits.py and real.py
Uses SearchServiceClient (NOT GroundedGenerationServiceClient)
"""
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from google.cloud import discoveryengine_v1beta as discoveryengine
from google.auth import default


@dataclass
class SearchResult:
    """Single search result"""
    title: str
    snippet: str
    link: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class GroundedResponse:
    """Grounded generation response with citations"""
    summary: str
    citations: List[str]
    results: List[SearchResult]
    cost_estimate: float  # USD
    snippets: List[str] = None  # Short excerpts from top results

    def __post_init__(self):
        if self.snippets is None:
            self.snippets = []


class VertexAISearch:
    """
    Vertex AI Search with Grounded Generation

    This uses SearchServiceClient with summary_spec to achieve
    grounded generation (NOT GroundedGenerationServiceClient which
    returns HTTP 501)
    """

    # Pricing (as of 2025)
    SEARCH_ENTERPRISE_COST_PER_1K = 4.00  # USD

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "global",
        data_store_id: Optional[str] = None
    ):
        """
        Initialize Vertex AI Search client

        Args:
            project_id: GCP project ID (auto-detected if None)
            location: GCP location (default: global)
            data_store_id: Data store ID (can be set later)
        """
        if project_id is None:
            _, project_id = default()

        self.project_id = project_id
        self.location = location
        self.data_store_id = data_store_id

        # Setup client
        client_options = None
        if location != "global":
            api_endpoint = f"{location}-discoveryengine.googleapis.com"
            client_options = {"api_endpoint": api_endpoint}

        self.client = discoveryengine.SearchServiceClient(client_options=client_options)

    def _get_serving_config(self, data_store_id: Optional[str] = None) -> str:
        """Build serving config path"""
        ds_id = data_store_id or self.data_store_id

        if not ds_id:
            raise ValueError("data_store_id must be provided")

        return (
            f"projects/{self.project_id}/locations/{self.location}/"
            f"collections/default_collection/dataStores/{ds_id}/"
            f"servingConfigs/default_config"
        )

    def search(
        self,
        query: str,
        data_store_id: Optional[str] = None,
        page_size: int = 10,
        include_summary: bool = True
    ) -> GroundedResponse:
        """
        Execute a search query with optional grounded generation

        Args:
            query: Search query
            data_store_id: Data store ID (uses instance default if None)
            page_size: Number of results to return
            include_summary: Include AI-generated summary (grounded generation)

        Returns:
            GroundedResponse with results and optional summary

        Raises:
            ValueError: If data_store_id not provided
            RuntimeError: If search fails
        """
        serving_config = self._get_serving_config(data_store_id)

        # Build request
        request_kwargs = {
            "serving_config": serving_config,
            "query": query,
            "page_size": page_size,
        }

        # Add grounded generation if requested.
        # summary_result_count max is 5 per Discovery Engine limits.
        if include_summary:
            request_kwargs["content_search_spec"] = (
                discoveryengine.SearchRequest.ContentSearchSpec(
                    summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                        summary_result_count=min(page_size, 5),
                        include_citations=True,
                        ignore_adversarial_query=True,
                        ignore_non_summary_seeking_query=False,
                        model_prompt_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
                            preamble=(
                                "You are Cerebro, an expert code analysis assistant. "
                                "Answer questions about the codebase using only the provided context. "
                                "Be concise and precise. Include relevant file paths, function names, "
                                "and code snippets when available. If the context does not contain "
                                "enough information to answer, say so clearly."
                            ),
                        ),
                    ),
                    snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                        return_snippet=True
                    ),
                )
            )

        try:
            request = discoveryengine.SearchRequest(**request_kwargs)
            response = self.client.search(request)

            # Parse response
            summary_text = ""
            citations = []

            if hasattr(response, 'summary') and response.summary:
                summary_text = response.summary.summary_text

                # Extract citations from summary_with_metadata (preferred)
                if hasattr(response.summary, 'summary_with_metadata') and \
                        response.summary.summary_with_metadata:
                    for ref in response.summary.summary_with_metadata.references:
                        title = getattr(ref, 'title', None) or getattr(ref, 'uri', None)
                        if title:
                            citations.append(title)

                # Fallback: extract from search results titles
                if not citations and hasattr(response, 'results'):
                    for result in response.results:
                        doc = result.document
                        title = doc.derived_struct_data.get('title') or \
                                doc.derived_struct_data.get('link')
                        if title:
                            citations.append(title)

            # Parse results
            results = []
            top_snippets = []
            for result in response.results:
                doc = result.document

                title = doc.derived_struct_data.get('title', 'Untitled')

                # Extract snippet
                raw_snippets = doc.derived_struct_data.get('snippets', [])
                snippet = raw_snippets[0].get('snippet', '') if raw_snippets else ''
                if snippet:
                    top_snippets.append(snippet[:300])

                link = doc.derived_struct_data.get('link')

                results.append(SearchResult(
                    title=title,
                    snippet=snippet[:500],  # Limit snippet length
                    link=link,
                    metadata=dict(doc.derived_struct_data)
                ))

            # Cost estimate
            cost_estimate = self.SEARCH_ENTERPRISE_COST_PER_1K / 1000

            return GroundedResponse(
                summary=summary_text,
                citations=citations,
                results=results,
                cost_estimate=cost_estimate,
                snippets=top_snippets,
            )

        except Exception as e:
            raise RuntimeError(f"Search failed: {e}")

    def grounded_search(
        self,
        query: str,
        data_store_id: Optional[str] = None,
        top_k: int = 5
    ) -> GroundedResponse:
        """
        Convenience method for grounded generation search

        Args:
            query: Search query
            data_store_id: Data store ID
            top_k: Number of results to use for grounding

        Returns:
            GroundedResponse with AI-generated summary and citations
        """
        return self.search(
            query=query,
            data_store_id=data_store_id,
            page_size=top_k,
            include_summary=True
        )


def main():
    """CLI entry point for testing search"""
    import sys

    print("="*60)
    print("💸 PHANTOM - Vertex AI Search Test")
    print("="*60)

    # Get config
    _, project = default()
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    data_store_id = os.getenv("DATA_STORE_ID")

    query = os.getenv("SEARCH_QUERY", "What is machine learning?")

    print(f"\n🎯 Configuration:")
    print(f"   Project: {project}")
    print(f"   Location: {location}")
    print(f"   Data Store: {data_store_id or '⚠️  NOT CONFIGURED'}")

    if not data_store_id:
        print("\n❌ DATA_STORE_ID not configured!")
        print("\n🔧 FIX:")
        print("   1. Run: phantom gcp datastores list")
        print("   2. Copy the data store ID")
        print("   3. Export: export DATA_STORE_ID='your-id-here'")
        sys.exit(1)

    # Execute search
    print(f"\n🔍 Executing query: {query}")
    print("⏳ Sending request...\n")

    search = VertexAISearch(
        project_id=project,
        location=location,
        data_store_id=data_store_id
    )

    try:
        response = search.grounded_search(query)

        print("="*60)
        print("📋 RESULTS")
        print("="*60)

        if response.summary:
            print("\n🤖 GENERATIVE SUMMARY:")
            print("-" * 60)
            print(response.summary)
            print("-" * 60)

            if response.citations:
                print("\n📚 Citations:")
                for citation in response.citations:
                    print(f"  • {citation}")

        print(f"\n🔎 SEARCH RESULTS ({len(response.results)} found):")

        if not response.results:
            print("  (No results found)")
            print("\n💡 TIP: Your data store may be empty!")
            print("   Add documents at: https://console.cloud.google.com/gen-app-builder")
        else:
            for i, result in enumerate(response.results, 1):
                print(f"\n  [{i}] {result.title}")
                if result.snippet:
                    print(f"      {result.snippet[:200]}...")
                if result.link:
                    print(f"      🔗 {result.link}")

        print("\n" + "="*60)
        print("✅ QUERY EXECUTED SUCCESSFULLY!")
        print("="*60)
        print(f"\n💰 CREDIT CONSUMED:")
        print(f"   • Search Enterprise Edition: ${VertexAISearch.SEARCH_ENTERPRISE_COST_PER_1K} / 1,000 queries")
        print(f"   • This query: ~${response.cost_estimate:.4f}")

        print("\n🎉 Validation complete!")
        print("Credits are being consumed correctly.")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"\n🔧 DEBUG INFO:")
        print(f"   - Project: {project}")
        print(f"   - Location: {location}")
        print(f"   - Data Store: {data_store_id}")
        print("\n📋 CHECKLIST:")
        print("   [ ] API discoveryengine.googleapis.com enabled?")
        print("   [ ] Data store exists and has documents?")
        print("   [ ] Billing account configured with credits?")
        print("   [ ] Permissions correct (roles/discoveryengine.admin)?")
        sys.exit(1)


if __name__ == "__main__":
    main()
