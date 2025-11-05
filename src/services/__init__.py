"""
Services module for Multi-Context Memory System.
Provides high-performance services for AI-driven knowledge retrieval.
"""

from .embedding_service import (
    EmbeddingService,
    get_embedding_service,
    embed_text,
    embed_batch,
    compute_similarity
)

from .vector_store_service import (
    VectorStoreService,
    get_vector_store,
    reset_vector_store
)

from .cache_service import (
    CacheService,
    get_cache_service,
    reset_cache_service,
    cached,
    cache_key
)

from .knowledge_retrieval_service import (
    KnowledgeRetrievalService,
    get_knowledge_retrieval_service,
    reset_knowledge_retrieval_service
)

__all__ = [
    # Embedding Service
    "EmbeddingService",
    "get_embedding_service",
    "embed_text",
    "embed_batch",
    "compute_similarity",

    # Vector Store Service
    "VectorStoreService",
    "get_vector_store",
    "reset_vector_store",

    # Cache Service
    "CacheService",
    "get_cache_service",
    "reset_cache_service",
    "cached",
    "cache_key",

    # Knowledge Retrieval Service
    "KnowledgeRetrievalService",
    "get_knowledge_retrieval_service",
    "reset_knowledge_retrieval_service",
]
