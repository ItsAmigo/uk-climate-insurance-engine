"""Environment Agency Flood Map for Planning loader.

The EA publishes Flood Zones 2 and 3 polygons for England via an ArcGIS
Feature Service. We ingest pre-downloaded GeoJSON files into DuckDB tables
indexed with an R-tree spatial index for fast point-in-polygon queries.

Why GeoJSON in / DuckDB spatial out
-----------------------------------
GeoJSON is the simplest format ArcGIS exports and the simplest format
DuckDB's `spatial` extension reads. It's roughly 3x larger than a
GeoPackage on disk but trivially streamable. Once loaded into DuckDB the
geometry column is stored compactly and the R-tree index makes point
lookups O(log N) regardless of polygon count.

Source CRS (BNG, EPSG:27700) vs internal CRS (WGS84, EPSG:4326)
---------------------------------------------------------------
We request `outSR=4326` from the Feature Service so the GeoJSON arrives
already in WGS84 (lat/lon) — the same coordinate system as the ONSPD
postcode coordinates. No reprojection needed at ingest. The reprojection
decision is logged in `docs/decisions.md`.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

FLOOD_ZONE_2_TABLE = "flood_zone_2"
FLOOD_ZONE_3_TABLE = "flood_zone_3"


def _load_zone(con: duckdb.DuckDBPyConnection, geojson_path: Path, table: str) -> int:
    """Drop + recreate `table` from a GeoJSON FeatureCollection of polygons."""
    if not geojson_path.exists():
        raise FileNotFoundError(f"GeoJSON not found at {geojson_path}")
    con.execute(f"DROP TABLE IF EXISTS {table}")
    con.execute(
        f"""
        CREATE TABLE {table} AS
        SELECT
            ROW_NUMBER() OVER () AS feature_id,
            ST_GeomFromGeoJSON(geom_json) AS geom
        FROM (
            SELECT json(features.feature->'geometry')::VARCHAR AS geom_json
            FROM (
                SELECT unnest(features) AS feature
                FROM read_json(?, format='auto', maximum_object_size=2000000000)
            ) AS features
            WHERE features.feature->>'geometry' IS NOT NULL
        )
        """,
        [str(geojson_path)],
    )
    con.execute(f"CREATE INDEX idx_{table}_geom ON {table} USING RTREE (geom)")
    row = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    assert row is not None
    return int(row[0])


def load_ea_flood_zones(
    *,
    zone_2_geojson: Path,
    zone_3_geojson: Path,
    db_path: Path,
) -> dict[str, int]:
    """Ingest both Zone 2 and Zone 3 GeoJSON files into DuckDB.

    Returns a dict mapping table name → row count. Idempotent.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db_path)) as con:
        con.execute("INSTALL spatial")
        con.execute("LOAD spatial")
        z3 = _load_zone(con, zone_3_geojson, FLOOD_ZONE_3_TABLE)
        z2 = _load_zone(con, zone_2_geojson, FLOOD_ZONE_2_TABLE)
    return {FLOOD_ZONE_2_TABLE: z2, FLOOD_ZONE_3_TABLE: z3}


__all__ = ["FLOOD_ZONE_2_TABLE", "FLOOD_ZONE_3_TABLE", "load_ea_flood_zones"]
