"""
User model - System user for authentication and feedback tracking.
"""

from uuid import UUID
from typing import TYPE_CHECKING, List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ENUM

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.feedback import Feedback


class UserRole(str, ENUM):
    """User role enum."""
    ADMIN = "ADMIN"
    USER = "USER"


class User(Base):
    """
    System user for authentication and feedback tracking.
    
    Users can provide feedback on assessments and have different permission levels.
    """

    __tablename__ = "users"

    # User email (unique identifier for login)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # User role for authorization
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=UserRole.USER,
    )

    # Relationships
    feedback: Mapped[List["Feedback"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
