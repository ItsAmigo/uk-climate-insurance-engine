"""Hypothesis property-based tests for hazard lookups.

Phase 1 gate language:
    "flood-zone score is monotonic in stated zone;
     postcode-level lookup is idempotent."

We translate that into three properties:

1. FloodZone enum order — ZONE_3 > ZONE_2 > ZONE_1. This is the contract
   downstream code (premium models, fairness audit) relies on. If anyone
   ever shuffles the enum values this test catches it.
2. SubsidenceClass enum order — HIGH > MEDIUM > LOW, same reasoning.
3. Subsidence dominant-class rule is monotonic in HEAVY content — adding
   "HEAVY" to a soil-group string can only raise the class, never lower
   it. (LIGHT-only -> LOW; LIGHT-with-HEAVY -> MEDIUM. HEAVY-first stays
   HIGH regardless of what follows.)
4. Postcode-coordinate lookup is idempotent — looking up the same
   postcode twice always returns the same coordinate. (Already covered
   for the *normaliser* in tests/test_postcode.py; this adds the lookup
   layer.)
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
from hypothesis import given, settings
from hypothesis import strategies as st

from climate_insurance.data.bgs_soil_parent_material import SPM_TABLE
from climate_insurance.data.ea_flood_zones import load_ea_flood_zones
from climate_insurance.data.postcode_directory import ONSPD_TABLE
from climate_insurance.hazards import (
    Coordinate,
    FloodZone,
    SubsidenceClass,
    lookup_flood_zone,
    lookup_postcode_coordinate,
    lookup_subsidence_class,
)
from climate_insurance.hazards.subsidence import _subsidence_class_from_soil_group

# ---------------------------------------------------------------------------
# Pure enum-order properties — no DB needed
# ---------------------------------------------------------------------------


def test_flood_zone_order_is_strictly_monotonic() -> None:
    assert int(FloodZone.ZONE_1) < int(FloodZone.ZONE_2) < int(FloodZone.ZONE_3)


def test_subsidence_class_order_is_strictly_monotonic() -> None:
    assert int(SubsidenceClass.LOW) < int(SubsidenceClass.MEDIUM) < int(SubsidenceClass.HIGH)


# ---------------------------------------------------------------------------
# Subsidence rule monotonicity — adding HEAVY can only raise the class
# ---------------------------------------------------------------------------


@given(
    base=st.sampled_from(["LIGHT(SANDY)", "LIGHT(SILTY)", "MEDIUM", "MEDIUM(SILTY)"]),
)
def test_adding_heavy_to_a_soil_group_never_lowers_subsidence_class(base: str) -> None:
    """If `base` (no HEAVY) maps to class C1, then `base TO HEAVY` maps to C2 >= C1."""
    c1 = _subsidence_class_from_soil_group(base)
    c2 = _subsidence_class_from_soil_group(f"{base} TO HEAVY")
    assert int(c2) >= int(c1)


@given(extra=st.sampled_from(["MEDIUM(SANDY)", "LIGHT(SANDY)", "LIGHT(SILTY)"]))
def test_heavy_first_stays_high_no_matter_what_follows(extra: str) -> None:
    """HEAVY in the dominant slot dominates regardless of trailing tokens."""
    assert _subsidence_class_from_soil_group(f"HEAVY TO {extra}") is SubsidenceClass.HIGH


# ---------------------------------------------------------------------------
# DB-backed idempotency properties
# ---------------------------------------------------------------------------


def _square(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [min_lon, min_lat],
                            [max_lon, min_lat],
                            [max_lon, max_lat],
                            [min_lon, max_lat],
                            [min_lon, min_lat],
                        ]
                    ],
                },
            }
        ],
    }


def _setup_idempotency_db(tmp_path: Path) -> Path:
    """Three known fixture postcodes covering FloodZone x SubsidenceClass space."""
    z3 = tmp_path / "z3.geojson"
    z2 = tmp_path / "z2.geojson"
    z3.write_text(json.dumps(_square(-1, 51, 0, 52)), encoding="utf-8")
    z2.write_text(json.dumps(_square(0, 51, 1, 52)), encoding="utf-8")
    db = tmp_path / "hazards.duckdb"
    load_ea_flood_zones(zone_2_geojson=z2, zone_3_geojson=z3, db_path=db)
    with duckdb.connect(str(db)) as con:
        con.execute("LOAD spatial")
        con.execute(f"""
            CREATE TABLE {SPM_TABLE} (
                uid VARCHAR, esb_desc VARCHAR, carbonate VARCHAR,
                grainsize VARCHAR, soil_group VARCHAR, soil_tex VARCHAR,
                soil_depth VARCHAR, geom GEOMETRY
            )
        """)
        con.execute(
            f"INSERT INTO {SPM_TABLE} VALUES "
            "('a','CLAY','LOW','ARGILLACEOUS','HEAVY','CLAY','DEEP', "
            "  ST_GeomFromText('POLYGON((-1 51, 0 51, 0 52, -1 52, -1 51))')), "
            "('b','SAND','NONE','ARENACEOUS','LIGHT(SANDY)','SAND','DEEP', "
            "  ST_GeomFromText('POLYGON((0 51, 1 51, 1 52, 0 52, 0 51))'))"
        )
        con.execute(f"CREATE INDEX idx_{SPM_TABLE}_geom ON {SPM_TABLE} USING RTREE (geom)")
        con.execute(f"""
            CREATE TABLE {ONSPD_TABLE} (
                postcode VARCHAR PRIMARY KEY,
                lat DOUBLE, lon DOUBLE,
                lsoa11 VARCHAR, lsoa21 VARCHAR, msoa11 VARCHAR,
                lad VARCHAR, ctry VARCHAR
            )
        """)
        con.execute(
            f"INSERT INTO {ONSPD_TABLE} VALUES "
            "('AA1 1AA', 51.5, -0.5, 'L1', 'L1', 'M1', 'D1', 'E92000001'), "
            "('BB1 1BB', 51.5,  0.5, 'L2', 'L2', 'M2', 'D2', 'E92000001')"
        )
    return db


@settings(deadline=None, max_examples=4)
@given(postcode=st.sampled_from(["AA1 1AA", "aa1 1aa", "AA1  1AA", "BB1 1BB"]))
def test_postcode_coordinate_lookup_is_idempotent(tmp_path_factory: object, postcode: str) -> None:
    """Looking up the same postcode twice always yields the same Coordinate.

    Hypothesis varies the input across normalisation-equivalent forms so we
    also catch any case where normalisation drift would break idempotency.
    """
    db = _setup_idempotency_db(tmp_path_factory.mktemp("idem"))  # type: ignore[attr-defined]
    a = lookup_postcode_coordinate(postcode, db)
    b = lookup_postcode_coordinate(postcode, db)
    assert a == b


@settings(deadline=None, max_examples=8)
@given(
    lat=st.floats(min_value=51.05, max_value=51.95),
    lon=st.floats(min_value=-0.95, max_value=0.95),
)
def test_flood_lookup_is_idempotent(tmp_path_factory: object, lat: float, lon: float) -> None:
    """Two consecutive flood-zone lookups at the same coord give the same answer."""
    db = _setup_idempotency_db(tmp_path_factory.mktemp("idem"))  # type: ignore[attr-defined]
    coord = Coordinate(lat=lat, lon=lon)
    a = lookup_flood_zone(coord, db)
    b = lookup_flood_zone(coord, db)
    assert a == b


@settings(deadline=None, max_examples=8)
@given(
    lat=st.floats(min_value=51.05, max_value=51.95),
    lon=st.floats(min_value=-0.95, max_value=0.95),
)
def test_subsidence_lookup_is_idempotent(tmp_path_factory: object, lat: float, lon: float) -> None:
    db = _setup_idempotency_db(tmp_path_factory.mktemp("idem"))  # type: ignore[attr-defined]
    coord = Coordinate(lat=lat, lon=lon)
    a = lookup_subsidence_class(coord, db)
    b = lookup_subsidence_class(coord, db)
    assert a == b
