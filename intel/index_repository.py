#!/usr/bin/env python3
"""
INDEX REPOSITORY - Bulk import repo content into Discovery Engine Data Store

Extracts code, docs, and metadata from a Git repository and imports into
Discovery Engine for searchable knowledge base.
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict
import hashlib
from datetime import datetime
from google.cloud import discoveryengine_v1
from google.api_core import exceptions
import time


class RepositoryIndexer:
    """Index Git repository into Discovery Engine."""

    # File extensions to index
    CODE_EXTENSIONS = {
        '.py', '.rs', '.go', '.js', '.ts', '.tsx', '.jsx',
        '.c', '.cpp', '.h', '.hpp', '.java', '.kt',
        '.nix', '.sh', '.bash', '.zsh',
        '.toml', '.yaml', '.yml', '.json',
    }

    DOC_EXTENSIONS = {
        '.md', '.txt', '.rst', '.adoc',
    }

    SKIP_DIRS = {
        '.git', 'node_modules', 'target', 'dist', 'build',
        '__pycache__', '.nix-pip', '.direnv', 'result',
        'vendor', '.cache', '.next', 'coverage',
    }

    MAX_FILE_SIZE = 1_000_000  # 1MB per file (Discovery Engine limit)
    MAX_DOCUMENTS = 10_000     # Limit for initial indexing

    def __init__(
        self,
        project_id: str,
        location: str,
        data_store_id: str,
    ):
        self.project_id = project_id
        self.location = location
        self.data_store_id = data_store_id
        self.client = discoveryengine_v1.DocumentServiceClient()

    def scan_repository(self, repo_path: Path) -> List[Dict]:
        """Scan repository and extract documents."""

        print(f"📂 Scanning repository: {repo_path}")
        print()

        documents = []
        files_processed = 0
        files_skipped = 0

        for file_path in repo_path.rglob('*'):
            # Skip directories
            if file_path.is_dir():
                continue

            # Skip excluded directories
            if any(skip_dir in file_path.parts for skip_dir in self.SKIP_DIRS):
                files_skipped += 1
                continue

            # Check extension
            ext = file_path.suffix.lower()
            if ext not in self.CODE_EXTENSIONS and ext not in self.DOC_EXTENSIONS:
                files_skipped += 1
                continue

            # Check file size
            try:
                size = file_path.stat().st_size
                if size > self.MAX_FILE_SIZE or size == 0:
                    files_skipped += 1
                    continue
            except:
                files_skipped += 1
                continue

            # Read file content
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
            except Exception as e:
                files_skipped += 1
                continue

            # Create document
            relative_path = file_path.relative_to(repo_path)
            doc_id = hashlib.sha256(str(relative_path).encode()).hexdigest()[:32]

            # Determine category
            category = "documentation" if ext in self.DOC_EXTENSIONS else "code"

            document = {
                "id": doc_id,
                "struct_data": {
                    "title": str(relative_path),
                    "content": content,
                    "file_path": str(relative_path),
                    "file_type": ext[1:],  # Remove leading dot
                    "category": category,
                    "repo_name": repo_path.name,
                    "size_bytes": size,
                    "indexed_at": datetime.now().isoformat(),
                },
                "json_data": json.dumps({
                    "path": str(relative_path),
                    "type": ext[1:],
                    "category": category,
                    "content": content[:500],  # Preview
                }),
            }

            documents.append(document)
            files_processed += 1

            # Progress
            if files_processed % 100 == 0:
                print(f"   Processed: {files_processed} files (skipped: {files_skipped})")

            # Limit total documents
            if files_processed >= self.MAX_DOCUMENTS:
                print(f"   ⚠️  Reached limit of {self.MAX_DOCUMENTS} documents")
                break

        print()
        print(f"✅ Scanning complete:")
        print(f"   Files indexed: {files_processed}")
        print(f"   Files skipped: {files_skipped}")
        print(f"   Total documents: {len(documents)}")
        print()

        return documents

    def import_documents(self, documents: List[Dict], batch_size: int = 100):
        """Import documents into Discovery Engine via batch API."""

        print(f"📤 Importing documents to Discovery Engine...")
        print(f"   Data Store: {self.data_store_id}")
        print(f"   Total documents: {len(documents)}")
        print(f"   Batch size: {batch_size}")
        print()

        # Parent branch
        parent = (
            f"projects/{self.project_id}/"
            f"locations/{self.location}/"
            f"dataStores/{self.data_store_id}/"
            f"branches/default_branch"
        )

        # Process in batches
        total_batches = (len(documents) + batch_size - 1) // batch_size
        successful = 0
        failed = 0

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_num = (i // batch_size) + 1

            print(f"   Batch {batch_num}/{total_batches} ({len(batch)} docs)...", end=" ")

            try:
                # Convert to Discovery Engine documents
                de_documents = []
                for doc in batch:
                    de_doc = discoveryengine_v1.Document(
                        id=doc["id"],
                        json_data=doc["json_data"],
                    )
                    # Add struct_data if supported
                    # de_doc.struct_data = doc["struct_data"]  # May not be supported
                    de_documents.append(de_doc)

                # Import documents (async operation)
                request = discoveryengine_v1.ImportDocumentsRequest(
                    parent=parent,
                    inline_source=discoveryengine_v1.ImportDocumentsRequest.InlineSource(
                        documents=de_documents
                    ),
                    reconciliation_mode=discoveryengine_v1.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
                )

                operation = self.client.import_documents(request=request)

                # Don't wait for completion (can take hours)
                print("✅ Submitted")
                successful += len(batch)

                # Rate limiting
                time.sleep(1)

            except exceptions.InvalidArgument as e:
                print(f"❌ Invalid: {e}")
                failed += len(batch)

            except Exception as e:
                print(f"❌ Error: {type(e).__name__}")
                failed += len(batch)

        print()
        print(f"📊 Import summary:")
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")
        print()
        print(f"⏳ Note: Indexing happens asynchronously and may take 30-60 minutes.")
        print(f"   Check status in GCP Console:")
        print(f"   https://console.cloud.google.com/gen-app-builder/data-stores")
        print()

    def index_repository(self, repo_path: Path, batch_size: int = 100, auto_yes: bool = False):
        """Full indexing workflow."""

        if not repo_path.exists():
            print(f"❌ Repository not found: {repo_path}")
            return

        if not repo_path.is_dir():
            print(f"❌ Not a directory: {repo_path}")
            return

        print("=" * 60)
        print("🚀 REPOSITORY INDEXER - Discovery Engine")
        print("=" * 60)
        print()

        # Scan
        documents = self.scan_repository(repo_path)

        if not documents:
            print("❌ No documents found to index")
            return

        # Preview
        print(f"📄 Sample documents:")
        for doc in documents[:3]:
            struct_data = doc["struct_data"]
            print(f"   • {struct_data['file_path']} ({struct_data['file_type']}, {struct_data['size_bytes']} bytes)")
        print()

        # Confirm
        if not auto_yes:
            print(f"⚠️  About to import {len(documents)} documents.")
            print(f"   This will consume Discovery Engine quota.")
            print()
            response = input("Continue? [y/N]: ")

            if response.lower() != 'y':
                print("❌ Cancelled")
                return
        else:
            print(f"✅ Auto-confirmed: importing {len(documents)} documents")
            print()

        # Import
        self.import_documents(documents, batch_size)

        print(f"✅ Repository indexed!")
        print()
        print(f"🎯 NEXT STEPS:")
        print()
        print(f"1. Wait 30-60 minutes for indexing to complete")
        print()
        print(f"2. Test search:")
        print(f"   pxq 'explain the main architecture'")
        print()
        print(f"3. Execute strategy:")
        print(f"   python scripts/strategy_optimizer.py")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Index Git repository into Discovery Engine Data Store"
    )

    parser.add_argument(
        "repo_path",
        type=Path,
        help="Path to repository to index"
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
        "--data-store",
        default="ds-app-v4-5e020c93",
        help="Data Store ID"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for imports (default: 100)"
    )

    parser.add_argument(
        "--max-docs",
        type=int,
        default=10000,
        help="Maximum documents to index (default: 10000)"
    )

    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Auto-confirm import (skip prompt)"
    )

    args = parser.parse_args()

    # Update max docs if specified
    RepositoryIndexer.MAX_DOCUMENTS = args.max_docs

    # Create indexer
    indexer = RepositoryIndexer(
        project_id=args.project,
        location=args.location,
        data_store_id=args.data_store,
    )

    # Index repository
    indexer.index_repository(args.repo_path, args.batch_size, args.yes)


if __name__ == "__main__":
    main()
