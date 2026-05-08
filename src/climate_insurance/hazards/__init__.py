"""Hazard exposure — postcode → flood / subsidence / wind risk profile.

Phase 1 work in progress. Public API grows as ingestion lands.
"""

from .lookup import lookup_postcode_coordinate
from .postcode import is_valid_postcode, normalize_postcode, parse_postcode
from .types import Coordinate, FloodZone, Postcode

__all__ = [
    "Coordinate",
    "FloodZone",
    "Postcode",
    "is_valid_postcode",
    "lookup_postcode_coordinate",
    "normalize_postcode",
    "parse_postcode",
]
