"""
Chroma Vector Store Provider

Implements VectorStoreProvider interface for ChromaDB.
Provides local vector storage and similarity search capabilities.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from cerebro.interfaces.vector_store import VectorStoreProvider


class ChromaVectorStoreProvider(VectorStoreProvider):
    """
    Chroma Vector Store Provider
    
    Implements vector storage and retrieval using ChromaDB.
    Supports local persistence and in-memory operation.
    """

    def __init__(
        self,
        persist_directory: str = "./data/vector_db",
        collection_name: str = "phantom_documents",
    ):
        """
        Initialize Chroma Vector Store Provider.
        
        Args:
            persist_directory: Directory for persistent storage
            collection_name: Name of the collection to use
        """
        try:
            import chromadb
        except ImportError:
            raise ImportError(
                "chromadb is required for vector storage. "
                "Install with: pip install chromadb"
            )

        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Create persist directory if it doesn't exist
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize Chroma client with persistence
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]],
        **kwargs
    ) -> int:
        """
        Add documents with their embeddings to the vector store.
        
        Args:
            documents: List of document dictionaries with metadata
            embeddings: List of embedding vectors corresponding to documents
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Number of documents successfully added
        """
        if len(documents) != len(embeddings):
            raise ValueError(
                f"Number of documents ({len(documents)}) must match "
                f"number of embeddings ({len(embeddings)})"
            )

        if not documents:
            return 0

        # Prepare data for Chroma
        ids = []
        metadatas = []
        documents_text = []

        for i, doc in enumerate(documents):
            # Use document ID if available, otherwise generate one
            doc_id = doc.get("id", f"doc_{i}")
            ids.append(doc_id)

            # Extract text content
            text = doc.get("content", doc.get("text", ""))
            documents_text.append(text)

            # Prepare metadata (exclude content to save space)
            metadata = {k: v for k, v in doc.items() if k not in ["content", "text", "id"]}
            metadatas.append(metadata)

        try:
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents_text,
                metadatas=metadatas,
            )
            return len(documents)
        except Exception as e:
            print(f"❌ Error adding documents to Chroma: {e}")
            raise

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query embedding.
        
        Args:
            query_embedding: The query embedding vector
            top_k: Number of top results to return
            **kwargs: Additional provider-specific parameters
            
        Returns:
            List of documents with similarity scores, sorted by relevance
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

            # Transform Chroma results to standard format
            documents = []
            
            if results and results["ids"] and len(results["ids"]) > 0:
                for i, doc_id in enumerate(results["ids"][0]):
                    # Chroma returns distances, convert to similarity (1 - distance for cosine)
                    distance = results["distances"][0][i] if results["distances"] else 0
                    similarity = 1 - distance  # For cosine distance

                    doc = {
                        "id": doc_id,
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "similarity": similarity,
                        "distance": distance,
                    }
                    documents.append(doc)

            return documents
        except Exception as e:
            print(f"❌ Error searching Chroma: {e}")
            raise

    def delete_documents(self, document_ids: List[str]) -> int:
        """
        Delete documents from the vector store.
        
        Args:
            document_ids: List of document IDs to delete
            
        Returns:
            Number of documents successfully deleted
        """
        if not document_ids:
            return 0

        try:
            self.collection.delete(ids=document_ids)
            return len(document_ids)
        except Exception as e:
            print(f"❌ Error deleting documents from Chroma: {e}")
            raise

    def clear(self) -> None:
        """
        Clear all documents from the vector store.
        """
        try:
            # Get all document IDs
            all_docs = self.collection.get()
            if all_docs and all_docs["ids"]:
                self.collection.delete(ids=all_docs["ids"])
        except Exception as e:
            print(f"❌ Error clearing Chroma collection: {e}")
            raise

    def get_document_count(self) -> int:
        """
        Get the total number of documents in the vector store.
        
        Returns:
            Number of documents
        """
        try:
            return self.collection.count()
        except Exception as e:
            print(f"❌ Error getting document count from Chroma: {e}")
            return 0

    def health_check(self) -> bool:
        """
        Check if the vector store is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to get collection count as a health check
            self.collection.count()
            return True
        except Exception as e:
            print(f"❌ Chroma health check failed: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the current collection.
        
        Returns:
            Dictionary with collection metadata
        """
        try:
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory,
            }
        except Exception as e:
            print(f"❌ Error getting collection info: {e}")
            return {}
