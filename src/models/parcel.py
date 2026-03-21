"""
Parcel model - Deterministic representation of a physical land parcel.
"""

from uuid import UUID
from typing import TYPE_CHECKING, List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.assessment import Assessment


class Parcel(Base):
    """
    Deterministic representation of a physical land parcel.
    
    Stores parcel geometry using PostGIS native types (not WKT strings).
    Geocoding metadata from GCP includes Place ID and accuracy flags.
    """

    __tablename__ = "parcels"

    # Assessor Parcel Number
    apn: Mapped[str] = mapped_column(index=True, nullable=False)

    # Full address
    address: Mapped[str] = mapped_column(nullable=False)

    # PostGIS spatial boundary - native geometry type, not WKT string
    geometry: Mapped[Geometry] = mapped_column(
        Geometry("POLYGON", srid=4326),
        nullable=False,
    )

    # GCP geocoding metadata (Place ID, accuracy flags, lat/lng)
    geocoding_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    assessments: Mapped[List["Assessment"]] = relationship(
        back_populates="parcel",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Parcel(id={self.id}, apn={self.apn}, address={self.address})>"
