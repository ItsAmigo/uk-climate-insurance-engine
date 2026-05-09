"""Tests for the EA flood-zone loader and lookup functions.

Uses synthetic GeoJSON polygons rather than the real ~785k-feature EA
dataset. The shapes are simple squares chosen so each test point sits
unambiguously inside zero, one, or both zones.

Layout (lon, lat — WGS84):
    Zone 3:  [-1.0, 0.0] x [51.0, 52.0]   (central UK box)
    Zone 2:  [-2.0, 1.0] x [50.0, 53.0]   (larger, contains Zone 3)

Test points:
    P_z3       (-0.5, 51.5)  — inside both Zone 2 and Zone 3 -> Zone 3 wins
    P_z2_only  (-1.5, 52.5)  — inside Zone 2 only            -> Zone 2
    P_z1       ( 0.5, 50.5)  — outside both, inside Zone 2 hit-test envelope but actually outside both -> Zone 1
    P_z1_far   (-3.0, 49.6)  — outside both, valid UK coord  -> Zone 1
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from climate_insurance.data.ea_flood_zones import load_ea_flood_zones
from climate_insurance.hazards import (
    Coordinate,
    FloodZone,
    lookup_flood_zone,
)


def _square_geojson(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> dict:
    """Build a single-polygon FeatureCollection."""
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
def flood_db(tmp_path: Path) -> Path:
    z3_path = tmp_path / "flood_zone_3.geojson"
    z2_path = tmp_path / "flood_zone_2.geojson"
    z3_path.write_text(json.dumps(_square_geojson(-1.0, 51.0, 0.0, 52.0)), encoding="utf-8")
    z2_path.write_text(json.dumps(_square_geojson(-2.0, 50.0, 1.0, 53.0)), encoding="utf-8")
    db = tmp_path / "hazards.duckdb"
    counts = load_ea_flood_zones(zone_2_geojson=z2_path, zone_3_geojson=z3_path, db_path=db)
    assert counts == {"flood_zone_2": 1, "flood_zone_3": 1}
    return db


def test_point_inside_zone_3_returns_zone_3(flood_db: Path) -> None:
    coord = Coordinate(lat=51.5, lon=-0.5)
    assert lookup_flood_zone(coord, flood_db) is FloodZone.ZONE_3


def test_point_in_zone_2_only_returns_zone_2(flood_db: Path) -> None:
    coord = Coordinate(lat=52.5, lon=-1.5)
    assert lookup_flood_zone(coord, flood_db) is FloodZone.ZONE_2


def test_point_outside_both_returns_zone_1(flood_db: Path) -> None:
    coord = Coordinate(lat=49.6, lon=-3.0)
    assert lookup_flood_zone(coord, flood_db) is FloodZone.ZONE_1


def test_zone_3_precedence_over_zone_2(flood_db: Path) -> None:
    """Same point as test_point_inside_zone_3 — both zones contain it; Zone 3 must win."""
    coord = Coordinate(lat=51.5, lon=-0.5)
    assert lookup_flood_zone(coord, flood_db) is not FloodZone.ZONE_2


def test_loader_raises_for_missing_zone_3(tmp_path: Path) -> None:
    z2 = tmp_path / "z2.geojson"
    z2.write_text(json.dumps(_square_geojson(-1.0, 51.0, 0.0, 52.0)), encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        load_ea_flood_zones(
            zone_2_geojson=z2,
            zone_3_geojson=tmp_path / "missing.geojson",
            db_path=tmp_path / "hazards.duckdb",
        )


def test_loader_is_idempotent(flood_db: Path, tmp_path: Path) -> None:
    """Re-running the loader against the same fixtures must produce the same row counts."""
    z3 = tmp_path / "flood_zone_3.geojson"
    z2 = tmp_path / "flood_zone_2.geojson"
    counts2 = load_ea_flood_zones(zone_2_geojson=z2, zone_3_geojson=z3, db_path=flood_db)
    assert counts2 == {"flood_zone_2": 1, "flood_zone_3": 1}
