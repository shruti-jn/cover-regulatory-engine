"""
Embedding service for generating and managing text embeddings.

This service generates vector embeddings for RAG (Retrieval-Augmented Generation)
and stores them in pgvector for similarity search.
"""

from typing import List, Optional
import hashlib
import structlog

from src.core.config import settings

logger = structlog.get_logger()


class EmbeddingConfig:
    """Configuration for embedding generation."""

    # Default embedding model dimensions
    DEFAULT_DIMENSIONS = settings.VECTOR_DIMENSIONS  # 1536

    # Maximum text length for embedding
    MAX_TEXT_LENGTH = 8192

    # Batch size for bulk embedding operations
    BATCH_SIZE = 100


class EmbeddingService:
    """
    Service for generating text embeddings.

    This is a placeholder implementation. In production, integrate with:
    - OpenAI API (text-embedding-3-small, text-embedding-3-large)
    - Cohere API
    - Local embedding models (sentence-transformers)
    - OpenAI-compatible endpoints
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.dimensions = EmbeddingConfig.DEFAULT_DIMENSIONS
        self._client = None

    async def _get_client(self):
        """Lazy initialization of the embedding client."""
        if self._client is None:
            # Placeholder: In production, initialize actual client
            # For OpenAI:
            # from openai import AsyncOpenAI
            # self._client = AsyncOpenAI(api_key=self.api_key)
            pass
        return self._client

    async def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            model: Model identifier (optional, uses default if not specified)

        Returns:
            Embedding vector as list of floats

        Raises:
            ValueError: If text is empty or too long
            RuntimeError: If embedding generation fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if len(text) > EmbeddingConfig.MAX_TEXT_LENGTH:
            logger.warning(
                "text_truncated_for_embedding",
                original_length=len(text),
                max_length=EmbeddingConfig.MAX_TEXT_LENGTH,
            )
            text = text[: EmbeddingConfig.MAX_TEXT_LENGTH]

        try:
            # Placeholder: In production, call actual embedding API
            # Example for OpenAI:
            # client = await self._get_client()
            # response = await client.embeddings.create(
            #     input=text,
            #     model=model or "text-embedding-3-small"
            # )
            # return response.data[0].embedding

            # For now, return a deterministic placeholder embedding
            # This allows testing without API calls
            logger.warning(
                "using_placeholder_embedding",
                message="Embedding service not configured - returning deterministic placeholder",
            )
            return self._generate_placeholder_embedding(text)

        except Exception as e:
            logger.error(
                "embedding_generation_failed",
                error=str(e),
                text_hash=hashlib.md5(text.encode()).hexdigest()[:8],
            )
            raise RuntimeError(f"Failed to generate embedding: {e}")

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of texts to embed
            model: Model identifier (optional)

        Returns:
            List of embedding vectors
        """
        embeddings = []

        # Process in batches
        for i in range(0, len(texts), EmbeddingConfig.BATCH_SIZE):
            batch = texts[i : i + EmbeddingConfig.BATCH_SIZE]

            try:
                # Placeholder: In production, use batch API
                # Example for OpenAI:
                # client = await self._get_client()
                # response = await client.embeddings.create(
                #     input=batch,
                #     model=model or "text-embedding-3-small"
                # )
                # batch_embeddings = [item.embedding for item in response.data]

                # For now, generate placeholder embeddings
                batch_embeddings = [
                    self._generate_placeholder_embedding(text) for text in batch
                ]
                embeddings.extend(batch_embeddings)

            except Exception as e:
                logger.error(
                    "batch_embedding_generation_failed",
                    error=str(e),
                    batch_size=len(batch),
                    batch_index=i // EmbeddingConfig.BATCH_SIZE,
                )
                raise RuntimeError(f"Failed to generate batch embeddings: {e}")

        return embeddings

    def _generate_placeholder_embedding(self, text: str) -> List[float]:
        """
        Generate a deterministic placeholder embedding for testing.

        This is NOT for production use - it generates pseudo-random
        vectors based on the text hash for testing without API calls.

        Args:
            text: Input text

        Returns:
            Deterministic embedding vector
        """
        import random

        # Use text hash as seed for deterministic output
        text_hash = hashlib.md5(text.encode()).hexdigest()
        seed = int(text_hash[:8], 16)
        rng = random.Random(seed)

        # Generate normalized random vector
        vector = [rng.uniform(-1, 1) for _ in range(self.dimensions)]

        # Normalize to unit length (cosine similarity requires unit vectors)
        magnitude = sum(x**2 for x in vector) ** 0.5
        if magnitude > 0:
            vector = [x / magnitude for x in vector]

        return vector

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> List[str]:
        """
        Split text into chunks for embedding.

        Uses recursive character splitting at natural boundaries
        (paragraphs, sentences, words).

        Args:
            text: Text to chunk
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks in characters

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # Find the end of this chunk
            end = start + chunk_size

            if end >= len(text):
                # Last chunk - take remaining text
                chunks.append(text[start:])
                break

            # Try to find a natural break point
            # Priority: paragraph > sentence > word
            break_point = self._find_break_point(text, end)

            chunk = text[start:break_point]
            chunks.append(chunk)

            # Move start forward with overlap
            start = break_point - chunk_overlap
            if start <= 0:
                start = break_point

        return chunks

    def _find_break_point(self, text: str, target: int) -> int:
        """
        Find a natural break point near the target position.

        Args:
            text: Full text
            target: Target position

        Returns:
            Best break point position
        """
        # Search window around target
        search_start = max(0, target - 100)
        search_end = min(len(text), target + 100)
        search_text = text[search_start:search_end]

        # Look for paragraph break
        paragraph_break = search_text.rfind("\n\n")
        if paragraph_break != -1:
            return search_start + paragraph_break

        # Look for sentence break
        for delimiter in [". ", "! ", "? "]:
            sentence_break = search_text.rfind(delimiter)
            if sentence_break != -1:
                return search_start + sentence_break + 1

        # Look for word break
        word_break = search_text.rfind(" ")
        if word_break != -1:
            return search_start + word_break

        # Fallback: use target
        return target


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the singleton embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
