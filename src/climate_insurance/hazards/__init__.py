"""Hazard exposure — postcode → flood / subsidence / wind risk profile.

Phase 1 work in progress. Public API grows as ingestion lands.
"""

from .flood import lookup_flood_zone, lookup_postcode_flood_zone
from .lookup import lookup_postcode_coordinate
from .postcode import is_valid_postcode, normalize_postcode, parse_postcode
from .subsidence import (
    lookup_postcode_subsidence_class,
    lookup_subsidence_class,
)
from .types import Coordinate, FloodZone, Postcode, SubsidenceClass

__all__ = [
    "Coordinate",
    "FloodZone",
    "Postcode",
    "SubsidenceClass",
    "is_valid_postcode",
    "lookup_flood_zone",
    "lookup_postcode_coordinate",
    "lookup_postcode_flood_zone",
    "lookup_postcode_subsidence_class",
    "lookup_subsidence_class",
    "normalize_postcode",
    "parse_postcode",
]
