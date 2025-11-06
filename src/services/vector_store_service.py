"""
MCP Multi-Context Memory System
Copyright (c) 2024 VoiceLessQ
https://github.com/VoiceLessQ/multi-context-memory

This file is part of the MCP Multi-Context Memory System.
Licensed under the MIT License. See LICENSE file in the project root.

Project Fingerprint: 7a8f9b3c-mcpmem-voicelessq-2024
Original Author: VoiceLessQ
"""

"""
Vector Store Service using ChromaDB for high-performance similarity search.
Provides 10-100x performance improvement for AI-driven knowledge retrieval.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
import uuid

logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    ChromaDB-based vector store for efficient semantic search.
    Optimized for AI-driven knowledge retrieval with automatic persistence.
    """

    def __init__(
        self,
        persist_directory: str = "./data/chroma",
        collection_name: str = "knowledge_base",
        embedding_function=None
    ):
        """
        Initialize vector store service.

        Args:
            persist_directory: Directory for ChromaDB persistence
            collection_name: Name of the collection
            embedding_function: Optional custom embedding function
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._embedding_function = embedding_function

        self._initialize_client()
        logger.info(
            f"VectorStoreService initialized with collection={self.collection_name}, "
            f"persist_directory={self.persist_directory}"
        )

    def _initialize_client(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Create persistent client
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self._embedding_function,
                metadata={"description": "AI-driven knowledge retrieval system"}
            )

            logger.info(f"ChromaDB collection '{self.collection_name}' ready")
            logger.info(f"Current collection size: {self._collection.count()} items")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """
        Add documents to the vector store.

        Args:
            documents: List of text documents
            metadatas: Optional metadata for each document
            ids: Optional custom IDs (auto-generated if not provided)
            embeddings: Optional pre-computed embeddings

        Returns:
            List of document IDs
        """
        if not documents:
            return []

        try:
            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in documents]

            # Prepare metadata
            if metadatas is None:
                metadatas = [{} for _ in documents]

            # Add to collection
            if embeddings is not None:
                self._collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
            else:
                self._collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )

            logger.info(f"Added {len(documents)} documents to collection")
            return ids

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise

    def search(
        self,
        query: str,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
        query_embedding: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Search for similar documents.

        Args:
            query: Query text
            n_results: Number of results to return
            where: Metadata filter conditions
            where_document: Document content filter conditions
            query_embedding: Optional pre-computed query embedding

        Returns:
            Dictionary with ids, documents, metadatas, and distances
        """
        try:
            if query_embedding is not None:
                results = self._collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where,
                    where_document=where_document
                )
            else:
                results = self._collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where,
                    where_document=where_document
                )

            # Format results
            formatted_results = {
                "ids": results["ids"][0] if results["ids"] else [],
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "count": len(results["ids"][0]) if results["ids"] else 0
            }

            logger.info(f"Search returned {formatted_results['count']} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def search_with_scores(
        self,
        query: str,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        query_embedding: Optional[List[float]] = None
    ) -> List[Tuple[str, Dict[str, Any], float]]:
        """
        Search and return results with similarity scores.

        Args:
            query: Query text
            n_results: Number of results
            where: Metadata filters
            query_embedding: Optional pre-computed query embedding

        Returns:
            List of tuples (document, metadata, similarity_score)
        """
        results = self.search(
            query=query,
            n_results=n_results,
            where=where,
            query_embedding=query_embedding
        )

        # Convert distances to similarity scores
        # ChromaDB uses L2 (Euclidean) distance by default
        # For normalized embeddings: distance = sqrt(2*(1-cosine_similarity))
        # Therefore: cosine_similarity = 1 - (distance^2 / 2)
        # But we use a simpler formula: similarity = 1 / (1 + distance)
        scored_results = []
        for i in range(results["count"]):
            doc = results["documents"][i]
            metadata = results["metadatas"][i]
            distance = results["distances"][i]

            # Convert L2 distance to similarity score (0-1 range)
            # Lower distance = higher similarity
            similarity = 1.0 / (1.0 + distance)

            scored_results.append((doc, metadata, similarity))

        return scored_results

    def update_document(
        self,
        document_id: str,
        document: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ):
        """
        Update a document in the vector store.

        Args:
            document_id: ID of the document to update
            document: Updated document text
            metadata: Updated metadata
            embedding: Updated embedding
        """
        try:
            update_params = {"ids": [document_id]}

            if document is not None:
                update_params["documents"] = [document]
            if metadata is not None:
                update_params["metadatas"] = [metadata]
            if embedding is not None:
                update_params["embeddings"] = [embedding]

            self._collection.update(**update_params)
            logger.info(f"Updated document: {document_id}")

        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            raise

    def delete_documents(self, ids: List[str]):
        """
        Delete documents from the vector store.

        Args:
            ids: List of document IDs to delete
        """
        try:
            self._collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents")
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID.

        Args:
            document_id: Document ID

        Returns:
            Dictionary with document data or None if not found
        """
        try:
            results = self._collection.get(ids=[document_id])

            if results["ids"]:
                return {
                    "id": results["ids"][0],
                    "document": results["documents"][0],
                    "metadata": results["metadatas"][0]
                }
            return None

        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            raise

    def count(self) -> int:
        """Get the total number of documents in the collection."""
        return self._collection.count()

    def clear(self):
        """Clear all documents from the collection."""
        try:
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.create_collection(
                name=self.collection_name,
                embedding_function=self._embedding_function,
                metadata={"description": "AI-driven knowledge retrieval system"}
            )
            logger.info("Collection cleared")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        return {
            "name": self.collection_name,
            "count": self.count(),
            "persist_directory": self.persist_directory,
            "metadata": self._collection.metadata
        }


# Global instance cache
_vector_store_instance = None


def get_vector_store() -> VectorStoreService:
    """
    Get a cached vector store instance.
    Singleton pattern to maintain single ChromaDB connection.
    """
    global _vector_store_instance

    if _vector_store_instance is None:
        from ..config.settings import get_settings

        settings = get_settings()
        chroma_config = settings.get_chroma_config()

        if not chroma_config["enabled"]:
            logger.warning("Chroma vector store is disabled in settings")
            return None

        _vector_store_instance = VectorStoreService(
            persist_directory=chroma_config["persist_directory"],
            collection_name=chroma_config["collection_name"]
        )

    return _vector_store_instance


def reset_vector_store():
    """Reset the global vector store instance."""
    global _vector_store_instance
    _vector_store_instance = None
