"""Hazard exposure — postcode → flood / subsidence / wind risk profile.

Phase 1 work in progress. Public API grows as ingestion lands.
"""

from .flood import lookup_flood_zone, lookup_postcode_flood_zone
from .lookup import lookup_postcode_coordinate
from .postcode import is_valid_postcode, normalize_postcode, parse_postcode
from .types import Coordinate, FloodZone, Postcode

__all__ = [
    "Coordinate",
    "FloodZone",
    "Postcode",
    "is_valid_postcode",
    "lookup_flood_zone",
    "lookup_postcode_coordinate",
    "lookup_postcode_flood_zone",
    "normalize_postcode",
    "parse_postcode",
]
