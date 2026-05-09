"""Tests for the postcode -> HazardProfile composite function.

Builds a single in-memory test fixture that contains all three of:
  - the ONSPD-shape postcode_directory table (one row per fixture postcode)
  - the flood_zone_2 / flood_zone_3 spatial tables
  - the soil_parent_material spatial table

Then exercises the composite end-to-end against postcodes whose location
puts them in known-different hazard combinations.

Layout (lon, lat — WGS84):
  Cell A  (-0.5, 51.5)  inside Z3 + HEAVY clay  -> Z3, HIGH
  Cell B  ( 0.5, 51.5)  inside Z2 + LIGHT sand  -> Z2, LOW
  Cell C  (-0.5, 50.5)  outside Z2/Z3 + MEDIUM  -> Z1, MEDIUM
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

from climate_insurance.data.bgs_soil_parent_material import SPM_TABLE
from climate_insurance.data.ea_flood_zones import (
    load_ea_flood_zones,
)
from climate_insurance.data.postcode_directory import ONSPD_TABLE
from climate_insurance.hazards import (
    FloodZone,
    HazardProfile,
    SubsidenceClass,
    postcode_to_hazards,
)


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


@pytest.fixture()
def hazard_db(tmp_path: Path) -> Path:
    # Flood polygons via the real loader so the table shape is authentic.
    z3_path = tmp_path / "z3.geojson"
    z2_path = tmp_path / "z2.geojson"
    z3_path.write_text(json.dumps(_square(-1.0, 51.0, 0.0, 52.0)), encoding="utf-8")
    z2_path.write_text(json.dumps(_square(0.0, 51.0, 1.0, 52.0)), encoding="utf-8")
    db = tmp_path / "hazards.duckdb"
    load_ea_flood_zones(zone_2_geojson=z2_path, zone_3_geojson=z3_path, db_path=db)

    # SPM + ONSPD tables we set up directly (loaders take real GeoPackage / CSV
    # which is awkward to fabricate in a unit test).
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
            "  ST_GeomFromText('POLYGON((0 51, 1 51, 1 52, 0 52, 0 51))')), "
            "('c','MIXED','LOW','MIXED','MEDIUM','LOAM','DEEP', "
            "  ST_GeomFromText('POLYGON((-1 50, 0 50, 0 51, -1 51, -1 50))'))"
        )
        con.execute(f"CREATE INDEX idx_{SPM_TABLE}_geom ON {SPM_TABLE} USING RTREE (geom)")

        con.execute(f"""
            CREATE TABLE {ONSPD_TABLE} (
                postcode VARCHAR PRIMARY KEY,
                lat DOUBLE,
                lon DOUBLE,
                lsoa11 VARCHAR, lsoa21 VARCHAR, msoa11 VARCHAR,
                lad VARCHAR, ctry VARCHAR
            )
        """)
        # AA1 1AA -> Cell A (Z3 + HEAVY)
        # BB1 1BB -> Cell B (Z2 + LIGHT)
        # CC1 1CC -> Cell C (Z1 + MEDIUM)
        # DD1 1DD -> off-grid (not in ONSPD by design)
        con.execute(
            f"INSERT INTO {ONSPD_TABLE} VALUES "
            "('AA1 1AA', 51.5, -0.5, 'L1', 'L1', 'M1', 'D1', 'E92000001'), "
            "('BB1 1BB', 51.5,  0.5, 'L2', 'L2', 'M2', 'D2', 'E92000001'), "
            "('CC1 1CC', 50.5, -0.5, 'L3', 'L3', 'M3', 'D3', 'E92000001')"
        )
    return db


def test_postcode_in_zone_3_heavy_clay(hazard_db: Path) -> None:
    profile = postcode_to_hazards("AA1 1AA", hazard_db)
    assert profile == HazardProfile(
        flood_zone=FloodZone.ZONE_3,
        subsidence_class=SubsidenceClass.HIGH,
        windstorm_band=None,
    )


def test_postcode_in_zone_2_light_sand(hazard_db: Path) -> None:
    profile = postcode_to_hazards("BB1 1BB", hazard_db)
    assert profile == HazardProfile(
        flood_zone=FloodZone.ZONE_2,
        subsidence_class=SubsidenceClass.LOW,
        windstorm_band=None,
    )


def test_postcode_outside_flood_medium_soil(hazard_db: Path) -> None:
    profile = postcode_to_hazards("CC1 1CC", hazard_db)
    assert profile == HazardProfile(
        flood_zone=FloodZone.ZONE_1,
        subsidence_class=SubsidenceClass.MEDIUM,
        windstorm_band=None,
    )


def test_postcode_not_in_directory_returns_none(hazard_db: Path) -> None:
    """Valid postcode syntax, but no entry in the ONSPD fixture -> None."""
    assert postcode_to_hazards("DD1 1DD", hazard_db) is None


def test_invalid_postcode_raises(hazard_db: Path) -> None:
    with pytest.raises(ValueError):
        postcode_to_hazards("not a postcode", hazard_db)


def test_windstorm_is_none_for_now(hazard_db: Path) -> None:
    """Until the wind data ingestion lands, every profile reports None for wind."""
    profile = postcode_to_hazards("AA1 1AA", hazard_db)
    assert profile is not None
    assert profile.windstorm_band is None
