"""British Geological Survey Soil Parent Material (1km) loader.

Source: BGS Soil Parent Material Model, free 1km-resolution release. Open
Government Licence v3.0 with BGS attribution. Six attribute layers in the
GeoPackage all share the same schema; we ingest a single canonical layer
('Soil Texture' by default) and keep the columns relevant to subsidence:

- `SOIL_GROUP`: shorthand for grain-class makeup (HEAVY / MEDIUM / LIGHT,
  often as compound descriptions like "MEDIUM TO HEAVY"). The single most
  useful field for shrink-swell subsidence risk.
- `SOIL_TEX`: free-text texture (e.g. "CLAY TO LOAM", "PEAT").
- `PMM_GRAIN`: BGS grain-size class (ARGILLACEOUS / ARENACEOUS / etc.).
- `ESB_DESC`: European Soil Bureau parent-material description.
- `PMM1K_UID`: unique 1km-cell ID (handy for joins and citation).

Source CRS: OSGB36 / British National Grid (EPSG:27700). We reproject to
WGS84 (EPSG:4326) at ingest using DuckDB's ST_Transform, then flip to
(lon, lat) ordering with ST_FlipCoordinates so the geometries align with
the rest of our pipeline (which uses ST_Point(lon, lat)).
"""

from __future__ import annotations

from pathlib import Path

import duckdb

SPM_TABLE = "soil_parent_material"
SPM_LAYER = "Soil Texture"  # any single layer suffices; all six share schema


def load_bgs_spm(gpkg_path: Path, db_path: Path) -> int:
    """Ingest the BGS SPM 1km GeoPackage into DuckDB.

    Returns the row count loaded. Idempotent — drops + recreates the table.
    """
    if not gpkg_path.exists():
        raise FileNotFoundError(f"BGS SPM GeoPackage not found at {gpkg_path}")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(db_path)) as con:
        con.execute("INSTALL spatial")
        con.execute("LOAD spatial")
        con.execute(f"DROP TABLE IF EXISTS {SPM_TABLE}")
        con.execute(
            f"""
            CREATE TABLE {SPM_TABLE} AS
            SELECT
                PMM1K_UID    AS uid,
                ESB_DESC     AS esb_desc,
                CARB_CNTNT   AS carbonate,
                PMM_GRAIN    AS grainsize,
                SOIL_GROUP   AS soil_group,
                SOIL_TEX     AS soil_tex,
                SOIL_DEPTH   AS soil_depth,
                ST_FlipCoordinates(
                    ST_Transform(geom, 'EPSG:27700', 'EPSG:4326')
                ) AS geom
            FROM ST_Read(?, layer = ?)
            """,
            [str(gpkg_path), SPM_LAYER],
        )
        con.execute(f"CREATE INDEX idx_{SPM_TABLE}_geom ON {SPM_TABLE} USING RTREE (geom)")
        row = con.execute(f"SELECT COUNT(*) FROM {SPM_TABLE}").fetchone()
        assert row is not None
        return int(row[0])


__all__ = ["SPM_LAYER", "SPM_TABLE", "load_bgs_spm"]
