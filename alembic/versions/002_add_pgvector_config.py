"""
Add pgvector configuration and utilities.

Revision ID: 002
Revises: 001
Create Date: 2026-03-21 12:30:00.000000
"""

from typing import Sequence, Union

from alembic import op

# Revision identifiers
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add pgvector configuration and utility functions."""

    # Set default HNSW search parameters for the session
    # This affects recall vs speed tradeoff
    op.execute("ALTER DATABASE CURRENT SET hnsw.ef_search = 64")

    # Create a function for efficient batch similarity search
    # This is a helper function that can be used for complex queries
    op.execute("""
        CREATE OR REPLACE FUNCTION search_rules_by_embedding(
            query_embedding vector(1536),
            jurisdiction_filter text DEFAULT NULL,
            domain_filter text DEFAULT NULL,
            similarity_threshold float DEFAULT 0.7,
            max_results int DEFAULT 10
        )
        RETURNS TABLE (
            rule_id uuid,
            domain text,
            rule_type text,
            similarity float,
            document_id uuid
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT
                er.id as rule_id,
                er.domain,
                er.rule_type,
                (1 - (er.embedding <=> query_embedding) / 2)::float as similarity,
                er.document_id
            FROM extracted_rules er
            JOIN ingested_documents doc ON er.document_id = doc.id
            WHERE er.embedding IS NOT NULL
                AND (jurisdiction_filter IS NULL OR doc.jurisdiction = jurisdiction_filter)
                AND (domain_filter IS NULL OR er.domain = domain_filter)
                AND (1 - (er.embedding <=> query_embedding) / 2) >= similarity_threshold
            ORDER BY er.embedding <=> query_embedding
            LIMIT max_results;
        END;
        $$;
    """)

    # Add comment to document the HNSW index configuration
    op.execute("""
        COMMENT ON INDEX idx_extracted_rules_embedding_hnsw IS
        'HNSW index for vector similarity search. Parameters: m=16, ef_construction=64. Uses cosine distance operator (<=>).';
    """)


def downgrade() -> None:
    """Remove pgvector configuration."""

    # Drop the search function
    op.execute("DROP FUNCTION IF EXISTS search_rules_by_embedding(vector, text, text, float, int)")

    # Reset HNSW parameters (optional, usually kept)
    # op.execute("ALTER DATABASE CURRENT RESET hnsw.ef_search")
