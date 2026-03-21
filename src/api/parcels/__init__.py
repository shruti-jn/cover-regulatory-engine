"""
Parcel API routes.

Exports:
- router: Main parcels router
- internal_router: Internal geocoding endpoints
"""

from src.api.parcels.routes import router, internal_router

__all__ = ["router", "internal_router"]
