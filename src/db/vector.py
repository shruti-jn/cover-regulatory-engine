"""
pgvector configuration and vector search utilities for RAG embeddings.

Uses HNSW indexes with cosine distance for similarity search.
"""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector

from src.models.extracted_rule import ExtractedRule
from src.core.config import settings


class VectorSearchConfig:
    """Configuration for vector search operations."""

    # HNSW index parameters (per guidelines: m=16, ef_construction=64)
    HNSW_M = settings.HNSW_M  # 16
    HNSW_EF_CONSTRUCTION = settings.HNSW_EF_CONSTRUCTION  # 64

    # Default ef_search for queries (higher = more accurate but slower)
    DEFAULT_EF_SEARCH = 64

    # Maximum dimensions before switching to halfvec
    HALFVEC_THRESHOLD = 2000

    # Default embedding dimensions
    VECTOR_DIMENSIONS = settings.VECTOR_DIMENSIONS  # 1536


class VectorSearchResult:
    """Result of a vector similarity search."""

    def __init__(self, rule: ExtractedRule, similarity: float):
        self.rule = rule
        self.similarity = similarity

    def __repr__(self) -> str:
        return f"<VectorSearchResult(rule_id={self.rule.id}, similarity={self.similarity:.4f})>"


async def search_similar_rules(
    session: AsyncSession,
    query_embedding: List[float],
    jurisdiction: Optional[str] = None,
    domain: Optional[str] = None,
    limit: int = 10,
    min_similarity: float = 0.7,
) -> List[VectorSearchResult]:
    """
    Search for similar rules using cosine distance.

    Uses the cosine distance operator (<=>) for vector similarity search.
    Results are ordered by similarity (highest first).

    Args:
        session: Database session
        query_embedding: The query embedding vector
        jurisdiction: Optional jurisdiction filter
        domain: Optional domain filter (zoning, setback, height, etc.)
        limit: Maximum number of results
        min_similarity: Minimum similarity threshold (0.0 to 1.0)

    Returns:
        List of VectorSearchResult ordered by similarity
    """
    # Convert distance to similarity (cosine distance ranges 0-2, similarity is 1 - distance/2)
    # But pgvector cosine distance is actually 1 - cosine_similarity, so:
    # distance 0 = identical (similarity 1.0)
    # distance 2 = opposite (similarity -1.0, but we clip to 0)
    max_distance = 2 * (1 - min_similarity)

    # Build the query
    query = select(
        ExtractedRule,
        (1 - func.coalesce(ExtractedRule.embedding.cosine_distance(query_embedding), 2) / 2).label("similarity"),
    )

    # Add filters
    if jurisdiction:
        query = query.join(ExtractedRule.document).where(
            ExtractedRule.document.has(jurisdiction=jurisdiction)
        )

    if domain:
        query = query.where(ExtractedRule.domain == domain)

    # Only rules with embeddings
    query = query.where(ExtractedRule.embedding.is_not(None))

    # Order by similarity (using cosine distance operator <=>)
    query = query.order_by(
        ExtractedRule.embedding.cosine_distance(query_embedding)
    )

    # Limit results
    query = query.limit(limit)

    # Execute query
    result = await session.execute(query)
    rows = result.all()

    # Convert to search results
    search_results = []
    for rule, similarity in rows:
        # Clip similarity to 0-1 range
        clipped_similarity = max(0.0, min(1.0, float(similarity)))
        if clipped_similarity >= min_similarity:
            search_results.append(VectorSearchResult(rule, clipped_similarity))

    return search_results


async def get_rules_by_embedding_id(
    session: AsyncSession,
    embedding_ids: List[UUID],
) -> List[ExtractedRule]:
    """
    Retrieve rules by their embedding IDs.

    Args:
        session: Database session
        embedding_ids: List of rule IDs to retrieve

    Returns:
        List of ExtractedRule objects
    """
    query = select(ExtractedRule).where(ExtractedRule.id.in_(embedding_ids))
    result = await session.execute(query)
    return list(result.scalars().all())


async def update_rule_embedding(
    session: AsyncSession,
    rule_id: UUID,
    embedding: List[float],
) -> None:
    """
    Update the embedding vector for a rule.

    Args:
        session: Database session
        rule_id: Rule ID to update
        embedding: New embedding vector
    """
    rule = await session.get(ExtractedRule, rule_id)
    if rule:
        rule.embedding = embedding
        await session.commit()


async def bulk_update_embeddings(
    session: AsyncSession,
    embeddings_data: List[Tuple[UUID, List[float]]],
) -> int:
    """
    Update embeddings for multiple rules in bulk.

    Args:
        session: Database session
        embeddings_data: List of (rule_id, embedding) tuples

    Returns:
        Number of rules updated
    """
    updated_count = 0
    for rule_id, embedding in embeddings_data:
        rule = await session.get(ExtractedRule, rule_id)
        if rule:
            rule.embedding = embedding
            updated_count += 1

    await session.commit()
    return updated_count


async def create_hnsw_index(
    session: AsyncSession,
    table_name: str = "extracted_rules",
    column_name: str = "embedding",
    m: int = VectorSearchConfig.HNSW_M,
    ef_construction: int = VectorSearchConfig.HNSW_EF_CONSTRUCTION,
) -> None:
    """
    Create an HNSW index on the embedding column.

    Note: This is typically done in migrations, but this function
    allows runtime index creation for new tables or reindexing.

    Args:
        session: Database session
        table_name: Name of the table
        column_name: Name of the vector column
        m: HNSW m parameter (number of connections per layer)
        ef_construction: HNSW ef_construction parameter
    """
    index_name = f"idx_{table_name}_{column_name}_hnsw"

    # Drop existing index if exists
    await session.execute(text(f"DROP INDEX IF EXISTS {index_name}"))

    # Create HNSW index with cosine distance operator
    await session.execute(text(f"""
        CREATE INDEX {index_name}
        ON {table_name}
        USING hnsw ({column_name} vector_cosine_ops)
        WITH (m = {m}, ef_construction = {ef_construction})
    """))

    await session.commit()


async def set_search_ef(
    session: AsyncSession,
    ef_search: int = VectorSearchConfig.DEFAULT_EF_SEARCH,
) -> None:
    """
    Set the ef_search parameter for HNSW index queries.

    Higher values improve recall but increase search time.
    This is session-local and affects the current connection only.

    Args:
        session: Database session
        ef_search: ef_search parameter value
    """
    await session.execute(text(f"SET hnsw.ef_search = {ef_search}"))


def should_use_halfvec(dimensions: int) -> bool:
    """
    Determine if halfvec should be used based on embedding dimensions.

    Per guidelines: Use halfvec type if embedding dimensions exceed 2000.

    Args:
        dimensions: Number of embedding dimensions

    Returns:
        True if halfvec should be used
    """
    return dimensions > VectorSearchConfig.HALFVEC_THRESHOLD
