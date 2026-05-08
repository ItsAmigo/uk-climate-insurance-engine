"""ONS Postcode Directory (ONSPD) loader.

The ONSPD is a quarterly CSV release from the Office for National Statistics
mapping every UK postcode to coordinates and to the official statistical-area
codes (LSOA, MSOA, LAD, country). We ingest it into a DuckDB table called
`postcode_directory` keyed by the normalised postcode.

This module is deliberately source-agnostic — it takes a path to a CSV that
the caller has already obtained. The fetch step lives in `scripts/fetch_onspd.py`
and is parametrised by URL because the geoportal item ID changes every
quarter.

Schema notes
------------
The ONSPD ships ~50 columns; we only persist the handful needed for the
postcode-to-hazard pipeline. Documented at
https://geoportal.statistics.gov.uk/ → "ONS Postcode Directory User Guide".

We filter out terminated postcodes (`doterm` non-null) — those are no longer
in use and would contaminate any current-state risk lookup. Northern-Ireland
postcodes that lack a published LSOA equivalent retain a NULL in the lsoa
column; downstream code must tolerate that.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

ONSPD_TABLE = "postcode_directory"

# ONSPD columns we keep. Names follow the post-2024 convention with explicit
# `<year>cd` suffixes (e.g. lsoa11cd, lad25cd). Documented in the ONSPD user
# guide shipped inside each release ZIP.
_KEEP_COLUMNS = [
    "pcds",  # postcode in standard variable-length form, e.g. "SW1A 1AA"
    "doterm",  # date of termination (yyyymm); non-null = postcode no longer in use
    "lat",  # WGS84 latitude
    "long",  # WGS84 longitude (ONSPD uses "long" not "lon")
    "lsoa11cd",  # 2011 Lower-Layer Super Output Area code
    "lsoa21cd",  # 2021 LSOA (England, Wales, NI; Scotland uses Data Zones here)
    "msoa11cd",  # 2011 Middle-Layer SOA
    "lad25cd",  # 2025 Local Authority District code
    "ctry25cd",  # 2025 country code (E92000001 = England, etc.)
]


def load_onspd(csv_path: Path, db_path: Path) -> int:
    """Ingest an ONSPD release CSV into DuckDB.

    Returns the row count of currently-active (non-terminated) postcodes loaded.
    Idempotent: drops and recreates the table on each call so re-runs against
    a newer ONSPD release produce a clean state.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"ONSPD CSV not found at {csv_path}")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(db_path)) as con:
        con.execute(f"DROP TABLE IF EXISTS {ONSPD_TABLE}")
        # read_csv_auto sniffs the schema from the header; ignore_errors skips
        # malformed rows (NI rows occasionally lack optional fields).
        con.execute(
            f"""
            CREATE TABLE {ONSPD_TABLE} AS
            SELECT
                regexp_replace(upper(trim(pcds)), '\\s+', ' ', 'g') AS postcode,
                CAST(lat AS DOUBLE) AS lat,
                CAST("long" AS DOUBLE) AS lon,
                lsoa11cd AS lsoa11,
                lsoa21cd AS lsoa21,
                msoa11cd AS msoa11,
                lad25cd AS lad,
                ctry25cd AS ctry
            FROM read_csv_auto(?, header = TRUE, ignore_errors = TRUE, all_varchar = TRUE)
            WHERE (doterm IS NULL OR trim(doterm) = '')
              AND lat IS NOT NULL
              AND "long" IS NOT NULL
              AND TRY_CAST(lat AS DOUBLE) BETWEEN 49.5 AND 61.0
              AND TRY_CAST("long" AS DOUBLE) BETWEEN -8.7 AND 2.1
            """,
            [str(csv_path)],
        )
        con.execute(
            f"CREATE UNIQUE INDEX idx_{ONSPD_TABLE}_postcode " f"ON {ONSPD_TABLE}(postcode)"
        )
        result = con.execute(f"SELECT COUNT(*) FROM {ONSPD_TABLE}").fetchone()
        assert result is not None  # COUNT(*) always returns a row
        return int(result[0])


__all__ = ["ONSPD_TABLE", "load_onspd"]
