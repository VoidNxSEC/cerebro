#!/usr/bin/env python3
"""
CREATE SEARCH ENGINE - Helper script to create Discovery Engine App

Creates a Search Engine (App) that uses existing data store for queries.
This is the missing piece to start consuming credits.
"""

import argparse
from google.cloud import discoveryengine_v1
from google.api_core import exceptions
import time


def create_search_engine(
    project_id: str,
    location: str,
    engine_id: str,
    data_store_id: str,
    display_name: str = None,
):
    """Create a Search Engine (App) for Discovery Engine."""

    if not display_name:
        display_name = f"Phoenix Search Engine ({engine_id})"

    print(f"🔧 Creating Search Engine...")
    print(f"   Project: {project_id}")
    print(f"   Location: {location}")
    print(f"   Engine ID: {engine_id}")
    print(f"   Data Store: {data_store_id}")
    print()

    try:
        client = discoveryengine_v1.EngineServiceClient()

        # Configure engine
        engine = discoveryengine_v1.Engine(
            display_name=display_name,
            solution_type=discoveryengine_v1.SolutionType.SOLUTION_TYPE_SEARCH,
            data_store_ids=[data_store_id],

            # Search engine config (ENTERPRISE tier for best quality)
            search_engine_config=discoveryengine_v1.Engine.SearchEngineConfig(
                search_tier=discoveryengine_v1.SearchTier.SEARCH_TIER_ENTERPRISE,
                search_add_ons=[
                    discoveryengine_v1.SearchAddOn.SEARCH_ADD_ON_LLM,  # RAG/summarization
                ],
            ),
        )

        # Parent collection
        parent = f"projects/{project_id}/locations/{location}/collections/default_collection"

        # Create engine (returns long-running operation)
        print("📡 Sending create request...")
        operation = client.create_engine(
            parent=parent,
            engine=engine,
            engine_id=engine_id,
        )

        print("⏳ Waiting for engine creation (this can take 2-5 minutes)...")
        print("   You can Ctrl+C and check status later if needed.")
        print()

        # Wait for operation to complete
        start_time = time.time()
        result = operation.result(timeout=600)  # 10 minute timeout
        elapsed = time.time() - start_time

        print(f"✅ Engine created successfully! ({elapsed:.1f}s)")
        print()
        print(f"📋 Engine details:")
        print(f"   Name: {result.name}")
        print(f"   Display Name: {result.display_name}")
        print(f"   Solution Type: {result.solution_type.name}")
        print()

        print(f"🎯 NEXT STEPS:")
        print()
        print(f"1. Set ENGINE_ID environment variable:")
        print(f"   export ENGINE_ID={engine_id}")
        print()
        print(f"2. Add to your shell config (permanent):")
        print(f"   echo 'export ENGINE_ID={engine_id}' >> ~/.bashrc")
        print(f"   source ~/.bashrc")
        print()
        print(f"3. Test with a query:")
        print(f"   pxq 'test query'")
        print()
        print(f"4. Execute strategy:")
        print(f"   python scripts/strategy_optimizer.py")
        print()

        return result

    except exceptions.AlreadyExists:
        print(f"❌ Engine '{engine_id}' already exists!")
        print()
        print(f"💡 Options:")
        print(f"   1. Use existing engine: export ENGINE_ID={engine_id}")
        print(f"   2. Choose different engine_id: --engine-id my-other-engine")
        print(f"   3. Delete existing: (not recommended, use Console UI)")
        return None

    except exceptions.PermissionDenied as e:
        print(f"❌ Permission denied: {e}")
        print()
        print(f"💡 Make sure:")
        print(f"   1. Discovery Engine API is enabled")
        print(f"   2. You have permission to create engines")
        print(f"   3. Run: gcloud services enable discoveryengine.googleapis.com")
        return None

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        print()
        print(f"💡 Check:")
        print(f"   1. Data store '{data_store_id}' exists")
        print(f"   2. Project ID is correct: {project_id}")
        print(f"   3. Location is valid: {location}")
        return None


def list_existing_engines(project_id: str, location: str):
    """List all existing engines."""

    print(f"🔍 Listing existing engines...")
    print()

    try:
        client = discoveryengine_v1.EngineServiceClient()
        parent = f"projects/{project_id}/locations/{location}/collections/default_collection"

        request = discoveryengine_v1.ListEnginesRequest(parent=parent)
        page_result = client.list_engines(request=request)

        found = False
        for engine in page_result:
            found = True
            engine_id = engine.name.split('/')[-1]
            print(f"✅ {engine_id}")
            print(f"   Name: {engine.display_name}")
            print(f"   Type: {engine.solution_type.name}")

            if hasattr(engine, 'data_store_ids') and engine.data_store_ids:
                print(f"   Data Stores: {', '.join(engine.data_store_ids)}")

            print()

        if not found:
            print("⚠️  No engines found.")
            print()
            print("💡 Create one with:")
            print("   python scripts/create_search_engine.py --create")

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Create or list Discovery Engine Search Apps"
    )

    parser.add_argument(
        "--project",
        default="gen-lang-client-0530325234",
        help="GCP Project ID"
    )

    parser.add_argument(
        "--location",
        default="global",
        help="Location (default: global)"
    )

    parser.add_argument(
        "--engine-id",
        default="phoenix-search-engine",
        help="Engine ID to create (default: phoenix-search-engine)"
    )

    parser.add_argument(
        "--data-store",
        default="ds-app-v4-5e020c93",
        help="Data Store ID to use"
    )

    parser.add_argument(
        "--display-name",
        help="Display name for engine (optional)"
    )

    parser.add_argument(
        "--create",
        action="store_true",
        help="Create the engine (default: just list existing)"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing engines"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🚀 PHOENIX - Search Engine Creator")
    print("=" * 60)
    print()

    if args.create:
        create_search_engine(
            project_id=args.project,
            location=args.location,
            engine_id=args.engine_id,
            data_store_id=args.data_store,
            display_name=args.display_name,
        )
    else:
        # Default: list existing
        list_existing_engines(args.project, args.location)

        print()
        print("💡 To create a new engine:")
        print(f"   python scripts/create_search_engine.py --create")


if __name__ == "__main__":
    main()
