"""
Service layer exports.
"""

from src.services.embeddings import (
    EmbeddingConfig,
    EmbeddingService,
    get_embedding_service,
)

__all__ = [
    "EmbeddingConfig",
    "EmbeddingService",
    "get_embedding_service",
]
