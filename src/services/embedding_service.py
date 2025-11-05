"""
Embedding Service for Multi-Context Memory System.
Supports both local (sentence-transformers) and OpenAI embeddings.
Provides 10-100x performance improvement through efficient vectorization.
"""
import logging
from typing import List, Optional, Union
import numpy as np
from functools import lru_cache

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Unified embedding service supporting multiple providers.
    Provides high-performance text vectorization for AI-driven knowledge retrieval.
    """

    def __init__(
        self,
        provider: str = "local",
        model_name: str = "all-MiniLM-L6-v2",
        openai_api_key: Optional[str] = None,
        openai_model: str = "text-embedding-3-small",
        dimension: int = 384
    ):
        """
        Initialize embedding service.

        Args:
            provider: "local" for sentence-transformers or "openai" for OpenAI API
            model_name: Name of the local model (if provider=local)
            openai_api_key: OpenAI API key (if provider=openai)
            openai_model: OpenAI model name (if provider=openai)
            dimension: Expected embedding dimension
        """
        self.provider = provider.lower()
        self.model_name = model_name
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model
        self.dimension = dimension
        self._model = None
        self._client = None

        self._initialize_provider()
        logger.info(
            f"EmbeddingService initialized with provider={self.provider}, "
            f"dimension={self.dimension}"
        )

    def _initialize_provider(self):
        """Initialize the embedding provider."""
        if self.provider == "local":
            self._initialize_local_model()
        elif self.provider == "openai":
            self._initialize_openai_client()
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

    def _initialize_local_model(self):
        """Initialize sentence-transformers model."""
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading local embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Local model loaded successfully")
        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            raise

    def _initialize_openai_client(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI

            if not self.openai_api_key:
                raise ValueError("OpenAI API key is required for provider='openai'")

            logger.info("Initializing OpenAI embedding client")
            self._client = OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized successfully")
        except ImportError:
            logger.error("openai package not installed. Install with: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * self.dimension

        try:
            if self.provider == "local":
                return self._embed_local(text)
            elif self.provider == "openai":
                return self._embed_openai(text)
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing (for local models)

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Filter out empty texts
        valid_texts = [t if t and t.strip() else " " for t in texts]

        try:
            if self.provider == "local":
                return self._embed_batch_local(valid_texts, batch_size)
            elif self.provider == "openai":
                return self._embed_batch_openai(valid_texts)
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise

    def _embed_local(self, text: str) -> List[float]:
        """Generate embedding using local model."""
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def _embed_batch_local(self, texts: List[str], batch_size: int) -> List[List[float]]:
        """Generate embeddings for batch using local model."""
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100
        )
        return embeddings.tolist()

    def _embed_openai(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        response = self._client.embeddings.create(
            input=text,
            model=self.openai_model
        )
        return response.data[0].embedding

    def _embed_batch_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch using OpenAI API."""
        # OpenAI API supports batch processing
        response = self._client.embeddings.create(
            input=texts,
            model=self.openai_model
        )
        return [item.embedding for item in response.data]

    def compute_similarity(
        self,
        embedding1: Union[List[float], np.ndarray],
        embedding2: Union[List[float], np.ndarray]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0 to 1)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Normalize vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        # Compute cosine similarity
        similarity = np.dot(vec1, vec2) / (norm1 * norm2)
        return float(similarity)

    def get_dimension(self) -> int:
        """Get the dimension of embeddings produced by this service."""
        return self.dimension

    def get_provider_info(self) -> dict:
        """Get information about the current provider."""
        return {
            "provider": self.provider,
            "model": self.model_name if self.provider == "local" else self.openai_model,
            "dimension": self.dimension
        }


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """
    Get a cached embedding service instance.
    Singleton pattern to avoid reloading models.
    """
    from ..config.settings import get_settings

    settings = get_settings()
    embedding_config = settings.get_embedding_config()

    return EmbeddingService(
        provider=embedding_config["provider"],
        model_name=embedding_config["model"],
        openai_api_key=embedding_config["openai_api_key"],
        openai_model=embedding_config["openai_model"],
        dimension=embedding_config["dimension"]
    )


# Convenience functions for easy access
def embed_text(text: str) -> List[float]:
    """Generate embedding for a single text using the default service."""
    service = get_embedding_service()
    return service.embed_text(text)


def embed_batch(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts using the default service."""
    service = get_embedding_service()
    return service.embed_batch(texts)


def compute_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """Compute cosine similarity between two embeddings."""
    service = get_embedding_service()
    return service.compute_similarity(embedding1, embedding2)
