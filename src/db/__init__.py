"""
Database module exports.
"""

from src.db.base import Base
from src.db.session import (
    engine,
    AsyncSessionLocal,
    get_db,
    init_db,
    close_db,
    create_indexes,
)
from src.db.vector import (
    VectorSearchConfig,
    VectorSearchResult,
    search_similar_rules,
    get_rules_by_embedding_id,
    update_rule_embedding,
    bulk_update_embeddings,
    create_hnsw_index,
    set_search_ef,
    should_use_halfvec,
)

__all__ = [
    "Base",
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "init_db",
    "close_db",
    "create_indexes",
    "VectorSearchConfig",
    "VectorSearchResult",
    "search_similar_rules",
    "get_rules_by_embedding_id",
    "update_rule_embedding",
    "bulk_update_embeddings",
    "create_hnsw_index",
    "set_search_ef",
    "should_use_halfvec",
]
