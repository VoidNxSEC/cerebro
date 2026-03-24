#!/usr/bin/env python3
"""
Vertex AI Data Store Management

Consolidated from manage_datastores.py (root and cerebro/)
"""
import os
import sys
from typing import List, Optional
from dataclasses import dataclass

from google.cloud import discoveryengine_v1beta as discoveryengine
from google.api_core import exceptions
from google.auth import default


@dataclass
class DataStore:
    """Data Store information"""
    id: str
    display_name: str
    content_config: str
    industry_vertical: str
    full_name: str


class DataStoreManager:
    """Manages Vertex AI Search Data Stores"""

    def __init__(self, project_id: Optional[str] = None, location: str = "global"):
        """
        Initialize DataStoreManager

        Args:
            project_id: GCP project ID (auto-detected if None)
            location: GCP location (default: global)
        """
        if project_id is None:
            _, project_id = default()

        self.project_id = project_id
        self.location = location
        self.parent = f"projects/{project_id}/locations/{location}/collections/default_collection"

        # Setup client
        client_options = None
        if location != "global":
            api_endpoint = f"{location}-discoveryengine.googleapis.com"
            client_options = {"api_endpoint": api_endpoint}

        self.client = discoveryengine.DataStoreServiceClient(client_options=client_options)

    def list(self) -> List[DataStore]:
        """
        List all data stores in the project

        Returns:
            List of DataStore objects
        """
        try:
            request = discoveryengine.ListDataStoresRequest(parent=self.parent)
            response = self.client.list_data_stores(request=request)

            data_stores = []
            for ds in response:
                data_stores.append(DataStore(
                    id=ds.name.split('/')[-1],
                    display_name=ds.display_name,
                    content_config=str(ds.content_config),
                    industry_vertical=str(ds.industry_vertical),
                    full_name=ds.name
                ))

            return data_stores

        except exceptions.PermissionDenied as e:
            raise PermissionError(f"No permission to list data stores: {e}")
        except Exception as e:
            raise RuntimeError(f"Error listing data stores: {e}")

    def get(self, data_store_id: str) -> Optional[DataStore]:
        """
        Get a specific data store by ID

        Args:
            data_store_id: Data store ID

        Returns:
            DataStore object or None if not found
        """
        data_stores = self.list()
        for ds in data_stores:
            if ds.id == data_store_id:
                return ds
        return None

    def create(
        self,
        data_store_id: str,
        display_name: str = "Phantom Data Store",
        industry_vertical: str = "GENERIC",
        content_config: str = "CONTENT_REQUIRED"
    ) -> DataStore:
        """
        Create a new data store

        Args:
            data_store_id: Unique ID for the data store
            display_name: Human-readable name
            industry_vertical: Industry type (GENERIC, RETAIL, etc.)
            content_config: Content configuration (CONTENT_REQUIRED, etc.)

        Returns:
            Created DataStore object

        Raises:
            FileExistsError: If data store already exists
            RuntimeError: If creation fails
        """
        try:
            # Map string industry vertical to enum
            industry_map = {
                "GENERIC": discoveryengine.IndustryVertical.GENERIC,
                "RETAIL": discoveryengine.IndustryVertical.RETAIL,
            }

            # Map string content config to enum
            content_map = {
                "CONTENT_REQUIRED": discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
                "PUBLIC_WEBSITE": discoveryengine.DataStore.ContentConfig.PUBLIC_WEBSITE,
            }

            data_store = discoveryengine.DataStore(
                display_name=display_name,
                industry_vertical=industry_map.get(industry_vertical, discoveryengine.IndustryVertical.GENERIC),
                content_config=content_map.get(content_config, discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED),
                solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
            )

            request = discoveryengine.CreateDataStoreRequest(
                parent=self.parent,
                data_store=data_store,
                data_store_id=data_store_id,
            )

            operation = self.client.create_data_store(request=request)
            response = operation.result(timeout=120)

            return DataStore(
                id=response.name.split('/')[-1],
                display_name=response.display_name,
                content_config=str(response.content_config),
                industry_vertical=str(response.industry_vertical),
                full_name=response.name
            )

        except exceptions.AlreadyExists:
            raise FileExistsError(f"Data store '{data_store_id}' already exists")
        except Exception as e:
            raise RuntimeError(f"Error creating data store: {e}")

    def delete(self, data_store_id: str) -> None:
        """
        Delete a data store

        Args:
            data_store_id: Data store ID to delete

        Raises:
            FileNotFoundError: If data store doesn't exist
            RuntimeError: If deletion fails
        """
        try:
            name = f"{self.parent}/dataStores/{data_store_id}"
            request = discoveryengine.DeleteDataStoreRequest(name=name)

            operation = self.client.delete_data_store(request=request)
            operation.result(timeout=120)

        except exceptions.NotFound:
            raise FileNotFoundError(f"Data store '{data_store_id}' not found")
        except Exception as e:
            raise RuntimeError(f"Error deleting data store: {e}")


def main():
    """CLI entry point for data store management"""
    print("="*60)
    print("📦 PHANTOM - Data Store Management")
    print("="*60)

    try:
        manager = DataStoreManager()

        print(f"\n🎯 Project: {manager.project_id}")
        print(f"📍 Location: {manager.location}")
        print(f"📂 Parent: {manager.parent}")

        # List existing
        print("\n📚 Existing Data Stores:")
        data_stores = manager.list()

        if not data_stores:
            print("  (No data stores found)")

            print("\n💡 Would you like to create a test data store? (y/n)")
            response = input(">>> ").strip().lower()

            if response == 'y':
                print("\n🔨 Creating data store 'test-search-datastore'...")
                print("  ⏳ This may take a few seconds...")

                ds = manager.create(
                    data_store_id="test-search-datastore",
                    display_name="Test Search DataStore"
                )

                print(f"  ✅ Data Store created: {ds.id}")
                print("\n" + "="*60)
                print("✅ NEXT STEP: Populate the data store")
                print("="*60)
                print(f"\n📝 Save this ID for queries:")
                print(f"   export DATA_STORE_ID='{ds.id}'")
                print("\n🔧 To add documents:")
                print("   1. Via Console: https://console.cloud.google.com/gen-app-builder")
                print("   2. Via API: phantom knowledge import")
        else:
            for ds in data_stores:
                print(f"\n  📦 {ds.display_name}")
                print(f"     ID: {ds.id}")
                print(f"     Type: {ds.content_config}")
                print(f"     Industry: {ds.industry_vertical}")

            print("\n✅ You have data stores configured!")
            print("📝 Use one of them for queries")

        print("\n" + "="*60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 FIX: Verify that the API is enabled:")
        print(f"   gcloud services enable discoveryengine.googleapis.com")
        sys.exit(1)


if __name__ == "__main__":
    main()
