"""Flood-zone lookup for England (Environment Agency Flood Map for Planning).

Given a WGS84 coordinate, returns the EA flood zone:
- ZONE_3 if the point lies inside any Flood Zone 3 polygon (high probability)
- ZONE_2 if it lies inside any Flood Zone 2 polygon but not Zone 3
- ZONE_1 otherwise (low probability — implicit default for everywhere outside
  Zones 2 and 3)

Phase 1 covers England only. Wales / Scotland / NI loaders land in
subsequent slices and feed into the same logical FloodZone enum after
harmonisation.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from climate_insurance.data.ea_flood_zones import (
    FLOOD_ZONE_2_TABLE,
    FLOOD_ZONE_3_TABLE,
)
from climate_insurance.hazards.lookup import lookup_postcode_coordinate

from .types import Coordinate, FloodZone, Postcode


def lookup_flood_zone(coordinate: Coordinate, db_path: Path) -> FloodZone:
    """Return the EA flood zone covering `coordinate`.

    Zone 3 takes precedence over Zone 2 (Zone 3 is a subset of areas the EA
    consider at higher probability of flooding). Default is Zone 1.
    """
    with duckdb.connect(str(db_path), read_only=True) as con:
        con.execute("LOAD spatial")
        point_wkt = f"POINT({coordinate.lon} {coordinate.lat})"
        in_zone_3 = con.execute(
            f"SELECT 1 FROM {FLOOD_ZONE_3_TABLE} "
            f"WHERE ST_Contains(geom, ST_GeomFromText(?)) LIMIT 1",
            [point_wkt],
        ).fetchone()
        if in_zone_3 is not None:
            return FloodZone.ZONE_3
        in_zone_2 = con.execute(
            f"SELECT 1 FROM {FLOOD_ZONE_2_TABLE} "
            f"WHERE ST_Contains(geom, ST_GeomFromText(?)) LIMIT 1",
            [point_wkt],
        ).fetchone()
        if in_zone_2 is not None:
            return FloodZone.ZONE_2
    return FloodZone.ZONE_1


def lookup_postcode_flood_zone(postcode: str | Postcode, db_path: Path) -> FloodZone | None:
    """End-to-end: postcode -> coordinate -> flood zone.

    Returns None if the postcode is not in the loaded ONSPD directory; raises
    ValueError if `postcode` is not a syntactically valid UK postcode.
    """
    coord = lookup_postcode_coordinate(postcode, db_path)
    if coord is None:
        return None
    return lookup_flood_zone(coord, db_path)


__all__ = ["lookup_flood_zone", "lookup_postcode_flood_zone"]
