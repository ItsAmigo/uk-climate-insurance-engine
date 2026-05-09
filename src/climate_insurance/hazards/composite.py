"""Composite postcode -> full-hazard-profile lookup.

Wraps the per-hazard lookups (flood, subsidence, eventually wind) into a
single entry point that orchestrates the database calls and returns a
`HazardProfile` populated with everything we know about that postcode.

Wind is intentionally returned as `None` until the wind-data ingestion
slice lands; the API contract is "None = not yet modelled" rather than
"no wind risk".
"""

from __future__ import annotations

from pathlib import Path

from .flood import lookup_flood_zone
from .lookup import lookup_postcode_coordinate
from .subsidence import lookup_subsidence_class
from .types import HazardProfile, Postcode


def postcode_to_hazards(postcode: str | Postcode, db_path: Path) -> HazardProfile | None:
    """Return the full hazard profile for `postcode`, or None if unknown.

    None means the postcode parsed successfully but is not in the loaded
    ONS Postcode Directory. A `ValueError` is raised if the input is not a
    syntactically valid UK postcode.
    """
    coord = lookup_postcode_coordinate(postcode, db_path)
    if coord is None:
        return None
    return HazardProfile(
        flood_zone=lookup_flood_zone(coord, db_path),
        subsidence_class=lookup_subsidence_class(coord, db_path),
        windstorm_band=None,
    )


__all__ = ["postcode_to_hazards"]
