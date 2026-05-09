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


def _load_zone(con: duckdb.DuckDBPyConnection, source_path: Path, table: str) -> int:
    """Drop + recreate `table` from a GeoJSON FeatureCollection or NDJSON file.

    NDJSON (one Feature per line) is preferred for files larger than ~1.5 GB
    because DuckDB's `read_json` has a per-object size limit that the
    multi-GB single-FeatureCollection form trips. The fetch script writes
    NDJSON during streaming and only stitches into a FeatureCollection at
    the end as a courtesy; this loader reads either form transparently.

    Detection is by extension: `.ndjson` or `.jsonl` -> per-line read,
    everything else -> single FeatureCollection read.
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Source not found at {source_path}")
    con.execute(f"DROP TABLE IF EXISTS {table}")

    if source_path.suffix.lower() in {".ndjson", ".jsonl"}:
        # One JSON Feature per line — no per-object size limit issues.
        # The EA dataset has a handful of corrupted features:
        #  (a) all-null coordinates -> crash ST_GeomFromGeoJSON
        #  (b) all-null parsed silently into a planet-spanning POLYGON
        # Filter (a) up-front by string match; filter (b) post-parse by
        # UK bounding-box check on the resulting envelope.
        # First pass: stream-load all parsed geoms into a temporary table.
        # Second pass: copy to the final table, applying the UK-bbox sanity
        # filter. Splitting the work avoids the double materialisation a
        # single-query CTE would force.
        con.execute(f"DROP TABLE IF EXISTS {table}_raw")
        con.execute(
            f"""
            CREATE TABLE {table}_raw AS
            SELECT ST_GeomFromGeoJSON(json_extract_string(geometry, '$')) AS geom
            FROM read_ndjson(?, ignore_errors=true, maximum_object_size=200000000)
            WHERE geometry IS NOT NULL
              AND json_extract_string(geometry, '$') NOT LIKE '%null%'
            """,
            [str(source_path)],
        )
        con.execute(f"""
            CREATE TABLE {table} AS
            SELECT ROW_NUMBER() OVER () AS feature_id, geom
            FROM {table}_raw
            WHERE ST_XMin(geom) BETWEEN -10 AND 5
              AND ST_XMax(geom) BETWEEN -10 AND 5
              AND ST_YMin(geom) BETWEEN 49 AND 62
              AND ST_YMax(geom) BETWEEN 49 AND 62
            """)
        con.execute(f"DROP TABLE {table}_raw")
    else:
        # 4 GB - 1 byte is the DuckDB UINT32 ceiling for this parameter.
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
                    FROM read_json(?, format='auto', maximum_object_size=4000000000)
                ) AS features
                WHERE features.feature->>'geometry' IS NOT NULL
            )
            """,
            [str(source_path)],
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
    memory_limit: str | None = None,
    threads: int | None = None,
) -> dict[str, int]:
    """Ingest both Zone 2 and Zone 3 GeoJSON files into DuckDB.

    Returns a dict mapping table name → row count. Idempotent.

    `memory_limit` and `threads` are optional DuckDB tuning parameters for
    the real multi-GB ingest. Tests should leave them unset (defaults).
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db_path)) as con:
        con.execute("INSTALL spatial")
        con.execute("LOAD spatial")
        # Streaming-friendly setting that's safe everywhere.
        con.execute("SET preserve_insertion_order=false")
        if memory_limit is not None:
            con.execute(f"SET memory_limit='{memory_limit}'")
        if threads is not None:
            con.execute(f"SET threads={int(threads)}")
        z3 = _load_zone(con, zone_3_geojson, FLOOD_ZONE_3_TABLE)
        z2 = _load_zone(con, zone_2_geojson, FLOOD_ZONE_2_TABLE)
    return {FLOOD_ZONE_2_TABLE: z2, FLOOD_ZONE_3_TABLE: z3}


__all__ = ["FLOOD_ZONE_2_TABLE", "FLOOD_ZONE_3_TABLE", "load_ea_flood_zones"]
