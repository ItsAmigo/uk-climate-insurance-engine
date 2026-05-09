"""Tests for the ONSPD loader and the postcode-coordinate lookup.

Uses a tiny synthetic CSV with the ONSPD column shape — no real data
fetched, no network calls.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from climate_insurance.data.postcode_directory import load_onspd
from climate_insurance.hazards import (
    Coordinate,
    Postcode,
    lookup_postcode_coordinate,
)

# Minimal subset of ONSPD columns + a few extras to mimic the real shape.
# Real-world rows include: SW1A 1AA (Buckingham Palace area), M1 1AE
# (central Manchester), G2 8DL (Glasgow), BT1 5GS (Belfast).
# Plus: one terminated postcode, one with bogus lat/lon.
_SYNTHETIC_CSV = (
    "pcd,pcds,doterm,lat,long,lsoa11cd,lsoa21cd,msoa11cd,lad25cd,ctry25cd,osgrdind\n"
    "SW1A1AA,SW1A 1AA,,51.501009,-0.141588,E01004736,E01004736,E02000977,E09000033,E92000001,1\n"
    "M1  1AE,M1 1AE,,53.479324,-2.241502,E01005181,E01005181,E02001034,E08000003,E92000001,1\n"
    "G2  8DL,G2 8DL,,55.860916,-4.255920,S01010267,,S02001752,S12000049,S92000003,1\n"
    "BT1 5GS,BT1 5GS,,54.601890,-5.926720,,N00000001,,N09000003,N92000002,1\n"
    "OL5 9AB,OL5 9AB,201503,53.000000,-1.500000,E01005000,E01005000,E02000999,E08000999,E92000001,1\n"
    "ZZ1 9ZZ,ZZ1 9ZZ,,99.999999,-0.100000,E01000000,E01000000,E02000000,E09000000,E92000001,1\n"
)


@pytest.fixture()
def onspd_csv(tmp_path: Path) -> Path:
    path = tmp_path / "ONSPD_TEST_UK.csv"
    path.write_text(_SYNTHETIC_CSV, encoding="utf-8")
    return path


@pytest.fixture()
def onspd_db(tmp_path: Path, onspd_csv: Path) -> Path:
    db = tmp_path / "hazards.duckdb"
    load_onspd(onspd_csv, db)
    return db


def test_load_onspd_returns_active_postcode_count(onspd_csv: Path, tmp_path: Path) -> None:
    db = tmp_path / "hazards.duckdb"
    rows = load_onspd(onspd_csv, db)
    # 6 input rows: 1 terminated, 1 with bad lat → 4 expected.
    assert rows == 4


def test_load_onspd_filters_terminated_postcodes(onspd_db: Path) -> None:
    coord = lookup_postcode_coordinate("OL5 9AB", onspd_db)
    assert coord is None


def test_load_onspd_filters_invalid_coordinates(onspd_db: Path) -> None:
    coord = lookup_postcode_coordinate("ZZ1 9ZZ", onspd_db)
    assert coord is None


def test_lookup_returns_coordinate_for_known_postcode(onspd_db: Path) -> None:
    coord = lookup_postcode_coordinate("SW1A 1AA", onspd_db)
    assert coord is not None
    assert coord == Coordinate(lat=51.501009, lon=-0.141588)


def test_lookup_normalises_input(onspd_db: Path) -> None:
    """A lowercase, no-space input must resolve the same as the canonical form."""
    assert lookup_postcode_coordinate("sw1a1aa", onspd_db) == Coordinate(
        lat=51.501009, lon=-0.141588
    )


def test_lookup_accepts_postcode_dataclass(onspd_db: Path) -> None:
    pc = Postcode(outward="M1", inward="1AE")
    coord = lookup_postcode_coordinate(pc, onspd_db)
    assert coord is not None
    assert coord.lat == pytest.approx(53.479324)
    assert coord.lon == pytest.approx(-2.241502)


def test_lookup_returns_none_for_unknown_postcode(onspd_db: Path) -> None:
    assert lookup_postcode_coordinate("ZZ99 9ZZ", onspd_db) is None


def test_lookup_raises_on_invalid_input(onspd_db: Path) -> None:
    with pytest.raises(ValueError):
        lookup_postcode_coordinate("not a postcode", onspd_db)


def test_load_onspd_is_idempotent(onspd_csv: Path, tmp_path: Path) -> None:
    """Running the loader twice should leave the same table state."""
    db = tmp_path / "hazards.duckdb"
    first = load_onspd(onspd_csv, db)
    second = load_onspd(onspd_csv, db)
    assert first == second


def test_load_onspd_raises_for_missing_csv(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_onspd(tmp_path / "missing.csv", tmp_path / "hazards.duckdb")
