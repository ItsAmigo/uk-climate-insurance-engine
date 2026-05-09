"""Subsidence-risk lookup using the BGS Soil Parent Material 1km dataset.

The `SOIL_GROUP` field in BGS SPM gives a clay/sand/silt grain-class
shorthand for each 1km cell, often as a compound description like
"MEDIUM TO LIGHT(SILTY) TO HEAVY". We classify each cell into a
`SubsidenceClass` (LOW / MEDIUM / HIGH) using a deterministic
**dominant-class rule** documented in `docs/methodology.md`:

- HIGH if the *first-listed* class in `SOIL_GROUP` starts with "HEAVY"
  (BGS lists classes in dominance order, so the first entry is the most
  prevalent grain class for that cell). Heavy clays drive the bulk of UK
  subsidence claims via shrink-swell.
- LOW if the dominant class is "LIGHT" (sandy or silty) AND there is no
  mention of "HEAVY" anywhere in the description. Sandy soils are
  essentially free of shrink-swell risk.
- MEDIUM otherwise — covers mixed-class cells, "MEDIUM" dominant cells,
  and the special "PEAT" / "ALL" cases (peat is a compressibility
  problem, not strictly shrink-swell, but still a foundation risk).

This mapping lives in code (`_subsidence_class_from_soil_group`) and is
re-applied at every lookup, so changing the methodology is a one-place
edit with no data re-ingest required.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from climate_insurance.data.bgs_soil_parent_material import SPM_TABLE
from climate_insurance.hazards.lookup import lookup_postcode_coordinate

from .types import Coordinate, Postcode, SubsidenceClass


def _subsidence_class_from_soil_group(soil_group: str | None) -> SubsidenceClass:
    """Apply the dominant-class rule. Returns MEDIUM for missing data."""
    if soil_group is None:
        return SubsidenceClass.MEDIUM
    text = soil_group.strip().upper()
    if not text or text == "NA":
        return SubsidenceClass.MEDIUM
    # First-listed class is dominant per BGS user guide.
    dominant = text.split(" TO ", 1)[0].split(" AND ", 1)[0].strip()
    if dominant.startswith("HEAVY"):
        return SubsidenceClass.HIGH
    if dominant.startswith("LIGHT") and "HEAVY" not in text:
        return SubsidenceClass.LOW
    return SubsidenceClass.MEDIUM


def lookup_subsidence_class(coordinate: Coordinate, db_path: Path) -> SubsidenceClass:
    """Return the subsidence-risk class for `coordinate`.

    The BGS SPM only covers Great Britain; coordinates outside the loaded
    grid (mainly Northern Ireland) fall back to MEDIUM as a neutral default.
    """
    point_wkt = f"POINT({coordinate.lon} {coordinate.lat})"
    with duckdb.connect(str(db_path), read_only=True) as con:
        con.execute("LOAD spatial")
        row = con.execute(
            f"SELECT soil_group FROM {SPM_TABLE} "
            f"WHERE ST_Contains(geom, ST_GeomFromText(?)) LIMIT 1",
            [point_wkt],
        ).fetchone()
    if row is None:
        return SubsidenceClass.MEDIUM
    return _subsidence_class_from_soil_group(row[0])


def lookup_postcode_subsidence_class(
    postcode: str | Postcode, db_path: Path
) -> SubsidenceClass | None:
    """End-to-end: postcode -> coordinate -> subsidence class.

    Returns None if the postcode is not in the loaded ONSPD directory; raises
    ValueError if `postcode` is not a syntactically valid UK postcode.
    """
    coord = lookup_postcode_coordinate(postcode, db_path)
    if coord is None:
        return None
    return lookup_subsidence_class(coord, db_path)


__all__ = [
    "lookup_postcode_subsidence_class",
    "lookup_subsidence_class",
]
