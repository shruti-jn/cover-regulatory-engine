"""
SQLAlchemy 2.0 base configuration.
"""

from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    id: int = mapped_column(Integer, primary_key=True, index=True)
