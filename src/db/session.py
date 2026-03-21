"""
Database session configuration with async SQLAlchemy 2.0.

Uses asyncpg driver exclusively - BANNED: psycopg2 or psycopg2-binary.
"""

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import Index

from src.core.config import settings
from src.db.base import Base

# Create async engine with asyncpg driver
# Uses postgresql+asyncpg:// dialect as required
database_url = settings.async_database_url

engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    future=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db():
    """
    Dependency that provides a database session.
    
    Yields an async session and ensures proper cleanup.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_indexes():
    """
    Create additional database indexes including spatial indexes.
    
    GiST indexes are created for all geometry columns as required.
    """
    from geoalchemy2 import Geometry
    
    async with engine.begin() as conn:
        # Create GiST spatial indexes on geometry columns
        for table_name, table in Base.metadata.tables.items():
            for column in table.columns:
                if isinstance(column.type, Geometry):
                    index_name = f"idx_{table_name}_{column.name}_gist"
                    # Create GiST index using raw SQL
                    await conn.execute(
                        f"""
                        CREATE INDEX IF NOT EXISTS {index_name}
                        ON {table_name}
                        USING GIST ({column.name})
                        """
                    )


async def init_db():
    """
    Initialize the database.
    
    Creates all tables and indexes.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create spatial indexes
    await create_indexes()


async def close_db():
    """Close database connections."""
    await engine.dispose()
