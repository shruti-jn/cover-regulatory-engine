"""
Initial migration - Create all tables with PostGIS and pgvector support.

Revision ID: 001
Revises:
Create Date: 2026-03-21 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2
import pgvector.sqlalchemy

# Revision identifiers
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables with PostGIS and pgvector support."""
    
    # Enable required extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("role", sa.String(20), nullable=False, default="USER"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create parcels table
    op.create_table(
        "parcels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("apn", sa.String(), nullable=False, index=True),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("geometry", geoalchemy2.Geometry("POLYGON", srid=4326), nullable=False),
        sa.Column("geocoding_metadata", postgresql.JSONB, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create spatial index on parcels.geometry
    op.execute("CREATE INDEX IF NOT EXISTS idx_parcels_geometry_gist ON parcels USING GIST (geometry)")
    
    # Create ingested_documents table
    op.create_table(
        "ingested_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("jurisdiction", sa.String(100), nullable=False, index=True),
        sa.Column("source_url", sa.String(1000), nullable=False),
        sa.Column("version_hash", sa.String(32), nullable=False, index=True),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("metadata", postgresql.JSONB, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create extracted_rules table
    op.create_table(
        "extracted_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("domain", sa.String(50), nullable=False, index=True),
        sa.Column("rule_type", sa.String(50), nullable=False, index=True),
        sa.Column("constraint_value", postgresql.JSONB, nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=False, default=50.0),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(1536), nullable=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ingested_documents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create HNSW index on embeddings for vector search
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_extracted_rules_embedding_hnsw
        ON extracted_rules
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)
    
    # Create rule_provenance table
    op.create_table(
        "rule_provenance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("excerpt", sa.Text, nullable=False),
        sa.Column("page_number", sa.Integer, nullable=True),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("extracted_rules.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ingested_documents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create assessments table
    op.create_table(
        "assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("scenario_hash", sa.String(), nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("parcel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("parcels.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create parcel_constraints table
    op.create_table(
        "parcel_constraints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("scenario_hash", sa.String(), nullable=False, index=True),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("provenance_state", sa.String(50), nullable=False, default="deterministic", index=True),
        sa.Column("evidence", postgresql.JSONB, default=list),
        sa.Column("derived_geometry", geoalchemy2.Geometry("POLYGON", srid=4326), nullable=True),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("extracted_rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("extracted_rules.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create spatial index on parcel_constraints.derived_geometry
    op.execute("CREATE INDEX IF NOT EXISTS idx_parcel_constraints_derived_geometry_gist ON parcel_constraints USING GIST (derived_geometry)")
    
    # Create feedback table
    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("comment", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create ingestion_pipeline_status table
    op.create_table(
        "ingestion_pipeline_status",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("status", sa.String(50), nullable=False, default="IDLE", index=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("documents_processed", sa.Integer, nullable=False, default=0),
        sa.Column("error_count", sa.Integer, nullable=False, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    """Drop all tables."""
    
    # Drop tables in reverse dependency order
    op.drop_table("feedback")
    op.drop_table("parcel_constraints")
    op.drop_table("assessments")
    op.drop_table("rule_provenance")
    op.drop_table("extracted_rules")
    op.drop_table("ingested_documents")
    op.drop_table("ingestion_pipeline_status")
    op.drop_table("parcels")
    op.drop_table("users")
    
    # Drop extensions (optional - usually kept)
    # op.execute("DROP EXTENSION IF EXISTS vector")
    # op.execute("DROP EXTENSION IF EXISTS postgis")
