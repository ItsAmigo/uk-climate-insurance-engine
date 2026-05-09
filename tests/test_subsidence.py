"""Tests for the BGS-SPM-driven subsidence-risk lookup.

Two test groups:
1. Pure-function tests of the dominant-class rule against the actual
   compound-soil-group strings the BGS data uses.
2. Integration tests with synthetic GeoJSON polygons stuffed into the SPM
   table directly (bypassing the loader's BNG-to-WGS84 reprojection because
   the loader's GeoPackage input format is awkward to fabricate in tests).
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from climate_insurance.data.bgs_soil_parent_material import SPM_TABLE
from climate_insurance.hazards import (
    Coordinate,
    SubsidenceClass,
    lookup_subsidence_class,
)
from climate_insurance.hazards.subsidence import _subsidence_class_from_soil_group

# Real soil_group values pulled from the actual BGS SPM 1km dataset.
_DOMINANT_RULE_CASES = [
    # heavy first -> HIGH
    ("HEAVY", SubsidenceClass.HIGH),
    ("HEAVY TO MEDIUM", SubsidenceClass.HIGH),
    ("HEAVY TO MEDIUM(SANDY) TO LIGHT(SANDY)", SubsidenceClass.HIGH),
    ("HEAVY AND MEDIUM", SubsidenceClass.HIGH),
    # light first AND no heavy mentioned -> LOW
    ("LIGHT", SubsidenceClass.LOW),
    ("LIGHT(SANDY)", SubsidenceClass.LOW),
    ("LIGHT(SANDY) TO MEDIUM(SANDY)", SubsidenceClass.LOW),
    ("LIGHT TO MEDIUM", SubsidenceClass.LOW),
    ("LIGHT(SILTY) TO MEDIUM(SILTY)", SubsidenceClass.LOW),
    # light first BUT heavy mentioned -> MEDIUM (mixed)
    ("LIGHT(SANDY) TO MEDIUM(SANDY) TO HEAVY", SubsidenceClass.MEDIUM),
    ("LIGHT(SILTY) TO MEDIUM(SILTY) TO HEAVY", SubsidenceClass.MEDIUM),
    # medium first -> MEDIUM
    ("MEDIUM", SubsidenceClass.MEDIUM),
    ("MEDIUM TO HEAVY", SubsidenceClass.MEDIUM),
    ("MEDIUM TO LIGHT(SILTY) TO HEAVY", SubsidenceClass.MEDIUM),
    ("MEDIUM(SILTY)", SubsidenceClass.MEDIUM),
    # special / fallback
    ("ALL", SubsidenceClass.MEDIUM),
    ("NA", SubsidenceClass.MEDIUM),
    ("", SubsidenceClass.MEDIUM),
    (None, SubsidenceClass.MEDIUM),
]


@pytest.mark.parametrize("soil_group,expected", _DOMINANT_RULE_CASES)
def test_dominant_class_rule(soil_group: str | None, expected: SubsidenceClass) -> None:
    assert _subsidence_class_from_soil_group(soil_group) is expected


def _make_spm_db(tmp_path: Path) -> Path:
    """Create a synthetic SPM table with three small WGS84 squares.

    Layout (lon, lat):
      HEAVY clay area:   [-1.0, 0.0] x [51.0, 52.0]
      LIGHT sand area:   [ 0.0, 1.0] x [51.0, 52.0]
      MEDIUM mix area:   [-1.0, 0.0] x [50.0, 51.0]
    Anywhere outside falls back to MEDIUM (no row matches).
    """
    db = tmp_path / "hazards.duckdb"
    with duckdb.connect(str(db)) as con:
        con.execute("INSTALL spatial; LOAD spatial")
        con.execute(
            f"""
            CREATE TABLE {SPM_TABLE} (
                uid VARCHAR,
                esb_desc VARCHAR,
                carbonate VARCHAR,
                grainsize VARCHAR,
                soil_group VARCHAR,
                soil_tex VARCHAR,
                soil_depth VARCHAR,
                geom GEOMETRY
            )
            """
        )
        con.execute(
            f"INSERT INTO {SPM_TABLE} VALUES "
            "('a','CLAY','LOW','ARGILLACEOUS','HEAVY','CLAY','DEEP', "
            "  ST_GeomFromText('POLYGON((-1 51, 0 51, 0 52, -1 52, -1 51))')), "
            "('b','SAND','NONE','ARENACEOUS','LIGHT(SANDY)','SAND','DEEP', "
            "  ST_GeomFromText('POLYGON((0 51, 1 51, 1 52, 0 52, 0 51))')), "
            "('c','MIXED','LOW','MIXED (ARGILLIC-ARENACEOUS)','MEDIUM TO HEAVY','LOAM','DEEP', "
            "  ST_GeomFromText('POLYGON((-1 50, 0 50, 0 51, -1 51, -1 50))'))"
        )
        con.execute(f"CREATE INDEX idx_{SPM_TABLE}_geom ON {SPM_TABLE} USING RTREE (geom)")
    return db


@pytest.fixture()
def spm_db(tmp_path: Path) -> Path:
    return _make_spm_db(tmp_path)


def test_lookup_inside_heavy_clay_area_returns_high(spm_db: Path) -> None:
    coord = Coordinate(lat=51.5, lon=-0.5)
    assert lookup_subsidence_class(coord, spm_db) is SubsidenceClass.HIGH


def test_lookup_inside_light_sand_area_returns_low(spm_db: Path) -> None:
    coord = Coordinate(lat=51.5, lon=0.5)
    assert lookup_subsidence_class(coord, spm_db) is SubsidenceClass.LOW


def test_lookup_inside_mixed_area_returns_medium(spm_db: Path) -> None:
    coord = Coordinate(lat=50.5, lon=-0.5)
    assert lookup_subsidence_class(coord, spm_db) is SubsidenceClass.MEDIUM


def test_lookup_outside_grid_falls_back_to_medium(spm_db: Path) -> None:
    """A coordinate outside any SPM polygon (e.g. Northern Ireland) -> MEDIUM."""
    coord = Coordinate(lat=54.6, lon=-5.93)  # Belfast, no GB SPM coverage in fixture
    assert lookup_subsidence_class(coord, spm_db) is SubsidenceClass.MEDIUM
