"""Natural Resources Wales Flood Map for Planning loader.

NRW's equivalent of the EA Flood Zones is published via DataMapWales'
GeoServer WFS. Layer `inspire-nrw:NRW_FLOODZONE_RIVERS_SEAS_MERGED`
combines fluvial and tidal flood zones in a single feature collection,
with a `risk` attribute carrying the literal strings "Flood Zone 2" /
"Flood Zone 3".

Two tables are produced (`nrw_flood_zone_2`, `nrw_flood_zone_3`) so
the lookup layer can union them with the EA tables without touching
existing England-only code paths.

Source CRS handling
-------------------
The WFS supports server-side reprojection — the fetch script requests
`srsName=EPSG:4326`, so the GeoJSON arrives in WGS84 lat/lon. No
client-side `ST_Transform` step at ingest, unlike the BGS pipeline.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

NRW_FLOOD_ZONE_2_TABLE = "nrw_flood_zone_2"
NRW_FLOOD_ZONE_3_TABLE = "nrw_flood_zone_3"

_RISK_ZONE_2 = "Flood Zone 2"
_RISK_ZONE_3 = "Flood Zone 3"


def _load_combined(
    con: duckdb.DuckDBPyConnection,
    source_path: Path,
    zone_2_table: str,
    zone_3_table: str,
) -> tuple[int, int]:
    """Split a single NRW NDJSON / GeoJSON file into Zone 2 and Zone 3 tables.

    Detects format by extension (`.ndjson` / `.jsonl` -> per-line read,
    everything else -> single FeatureCollection read). The UK-bbox sanity
    filter catches any parse-time corruption — same defensive layer used
    by the EA loader.
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Source not found at {source_path}")
    con.execute(f"DROP TABLE IF EXISTS {zone_2_table}")
    con.execute(f"DROP TABLE IF EXISTS {zone_3_table}")
    con.execute("DROP TABLE IF EXISTS nrw_flood_raw")

    if source_path.suffix.lower() in {".ndjson", ".jsonl"}:
        con.execute(
            """
            CREATE TABLE nrw_flood_raw AS
            SELECT
                json_extract_string(properties, '$.risk') AS risk,
                ST_GeomFromGeoJSON(json_extract_string(geometry, '$')) AS geom
            FROM read_ndjson(?, ignore_errors=true, maximum_object_size=200000000)
            WHERE geometry IS NOT NULL
              AND json_extract_string(geometry, '$') NOT LIKE '%null%'
            """,
            [str(source_path)],
        )
    else:
        con.execute(
            """
            CREATE TABLE nrw_flood_raw AS
            SELECT
                json_extract_string(feature->'properties', '$.risk') AS risk,
                ST_GeomFromGeoJSON(json(feature->'geometry')::VARCHAR) AS geom
            FROM (
                SELECT unnest(features) AS feature
                FROM read_json(?, format='auto', maximum_object_size=4000000000)
            )
            WHERE feature->>'geometry' IS NOT NULL
            """,
            [str(source_path)],
        )

    bbox_clause = (
        "ST_XMin(geom) BETWEEN -10 AND 5 "
        "AND ST_XMax(geom) BETWEEN -10 AND 5 "
        "AND ST_YMin(geom) BETWEEN 49 AND 62 "
        "AND ST_YMax(geom) BETWEEN 49 AND 62"
    )

    con.execute(f"""
        CREATE TABLE {zone_2_table} AS
        SELECT ROW_NUMBER() OVER () AS feature_id, geom
        FROM nrw_flood_raw
        WHERE risk = '{_RISK_ZONE_2}' AND {bbox_clause}
        """)
    con.execute(f"""
        CREATE TABLE {zone_3_table} AS
        SELECT ROW_NUMBER() OVER () AS feature_id, geom
        FROM nrw_flood_raw
        WHERE risk = '{_RISK_ZONE_3}' AND {bbox_clause}
        """)
    con.execute("DROP TABLE nrw_flood_raw")

    con.execute(f"CREATE INDEX idx_{zone_2_table}_geom ON {zone_2_table} USING RTREE (geom)")
    con.execute(f"CREATE INDEX idx_{zone_3_table}_geom ON {zone_3_table} USING RTREE (geom)")

    z2 = con.execute(f"SELECT COUNT(*) FROM {zone_2_table}").fetchone()
    z3 = con.execute(f"SELECT COUNT(*) FROM {zone_3_table}").fetchone()
    assert z2 is not None and z3 is not None
    return int(z2[0]), int(z3[0])


def load_nrw_flood_zones(
    *,
    source_path: Path,
    db_path: Path,
    memory_limit: str | None = None,
    threads: int | None = None,
) -> dict[str, int]:
    """Ingest the combined NRW Zone 2 / Zone 3 file into DuckDB.

    Returns a dict mapping table name → row count. Idempotent.

    `memory_limit` and `threads` are optional DuckDB tuning parameters;
    Welsh data volume is modest so defaults are normally fine.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db_path)) as con:
        con.execute("INSTALL spatial")
        con.execute("LOAD spatial")
        con.execute("SET preserve_insertion_order=false")
        if memory_limit is not None:
            con.execute(f"SET memory_limit='{memory_limit}'")
        if threads is not None:
            con.execute(f"SET threads={int(threads)}")
        z2, z3 = _load_combined(con, source_path, NRW_FLOOD_ZONE_2_TABLE, NRW_FLOOD_ZONE_3_TABLE)
    return {NRW_FLOOD_ZONE_2_TABLE: z2, NRW_FLOOD_ZONE_3_TABLE: z3}


__all__ = [
    "NRW_FLOOD_ZONE_2_TABLE",
    "NRW_FLOOD_ZONE_3_TABLE",
    "load_nrw_flood_zones",
]
