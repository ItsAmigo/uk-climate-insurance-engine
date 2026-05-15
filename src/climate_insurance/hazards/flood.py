"""Flood-zone lookup across the UK.

Given a WGS84 coordinate, returns the flood zone:
- ZONE_3 if the point lies inside any Zone 3 polygon  (high probability)
- ZONE_2 if it lies inside any Zone 2 polygon but not Zone 3
- ZONE_1 otherwise  (low probability — implicit default outside zones 2 and 3)

Each nation's ingestion populates its own pair of tables:
- England:          `flood_zone_2`,     `flood_zone_3`      (EA)
- Wales:            `nrw_flood_zone_2`, `nrw_flood_zone_3`  (NRW)
- Scotland, NI:     to land in subsequent slices

The lookup queries every table that exists in the DuckDB catalog at call
time, so test fixtures that load only one nation's polygons continue to
work and adding the next nation's loader is a strictly additive change.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from climate_insurance.data.ea_flood_zones import (
    FLOOD_ZONE_2_TABLE,
    FLOOD_ZONE_3_TABLE,
)
from climate_insurance.data.nrw_flood_zones import (
    NRW_FLOOD_ZONE_2_TABLE,
    NRW_FLOOD_ZONE_3_TABLE,
)
from climate_insurance.hazards.lookup import lookup_postcode_coordinate

from .types import Coordinate, FloodZone, Postcode

_ZONE_2_TABLES = (FLOOD_ZONE_2_TABLE, NRW_FLOOD_ZONE_2_TABLE)
_ZONE_3_TABLES = (FLOOD_ZONE_3_TABLE, NRW_FLOOD_ZONE_3_TABLE)


def _existing_tables(con: duckdb.DuckDBPyConnection, candidates: tuple[str, ...]) -> list[str]:
    """Return the subset of `candidates` that exist as base tables in the DB."""
    rows = con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'main' AND table_name = ANY(?)",
        [list(candidates)],
    ).fetchall()
    found = {r[0] for r in rows}
    return [t for t in candidates if t in found]


def _any_contains(con: duckdb.DuckDBPyConnection, tables: list[str], point_wkt: str) -> bool:
    """True if `point_wkt` lies inside any geometry across `tables`."""
    if not tables:
        return False
    union_sql = " UNION ALL ".join(
        f"SELECT 1 FROM {t} WHERE ST_Contains(geom, ST_GeomFromText(?))" for t in tables
    )
    row = con.execute(f"{union_sql} LIMIT 1", [point_wkt] * len(tables)).fetchone()
    return row is not None


def lookup_flood_zone(coordinate: Coordinate, db_path: Path) -> FloodZone:
    """Return the flood zone covering `coordinate`.

    Zone 3 takes precedence over Zone 2 across all loaded nations.
    Default is Zone 1 (no Zone 2 or Zone 3 polygon contains the point).
    """
    with duckdb.connect(str(db_path), read_only=True) as con:
        con.execute("LOAD spatial")
        point_wkt = f"POINT({coordinate.lon} {coordinate.lat})"
        z3 = _existing_tables(con, _ZONE_3_TABLES)
        if _any_contains(con, z3, point_wkt):
            return FloodZone.ZONE_3
        z2 = _existing_tables(con, _ZONE_2_TABLES)
        if _any_contains(con, z2, point_wkt):
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
