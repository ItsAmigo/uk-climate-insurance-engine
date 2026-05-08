"""Hazard exposure — postcode → flood / subsidence / wind risk profile.

Phase 1 work in progress. Public API will grow as ingestion lands; for now
only the postcode layer is implemented.
"""

from .postcode import is_valid_postcode, normalize_postcode, parse_postcode
from .types import FloodZone, Postcode

__all__ = [
    "FloodZone",
    "Postcode",
    "is_valid_postcode",
    "normalize_postcode",
    "parse_postcode",
]
