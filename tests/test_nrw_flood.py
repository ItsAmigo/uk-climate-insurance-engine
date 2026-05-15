"""Tests for the NRW flood-zone loader and the multi-nation lookup union.

NRW's source data is a single combined layer carrying both Zones 2 and 3
in a `risk` attribute (`"Flood Zone 2"` / `"Flood Zone 3"`). The loader
splits these into separate DuckDB tables, mirroring the EA schema so the
lookup can union across nations.

Synthetic layout used by these tests (lon, lat — WGS84):
    NRW Zone 3:  [-4.0, -3.0] x [51.0, 52.0]    (Wales-ish box A)
    NRW Zone 2:  [-5.0, -2.0] x [50.0, 53.0]    (larger, contains Zone 3)

This is geographically west of the EA fixture box so the two-nation
union test can place a single point in each without collision.
"""

from __future__ import annotations

import json
from pathlib import Path

from climate_insurance.data.ea_flood_zones import load_ea_flood_zones
from climate_insurance.data.nrw_flood_zones import (
    NRW_FLOOD_ZONE_2_TABLE,
    NRW_FLOOD_ZONE_3_TABLE,
    load_nrw_flood_zones,
)
from climate_insurance.hazards import (
    Coordinate,
    FloodZone,
    lookup_flood_zone,
)


def _feature(min_lon: float, min_lat: float, max_lon: float, max_lat: float, risk: str) -> dict:
    return {
        "type": "Feature",
        "properties": {"risk": risk, "risk_cy": "Parth Llifogydd"},
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


def _nrw_collection() -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            _feature(-4.0, 51.0, -3.0, 52.0, "Flood Zone 3"),
            _feature(-5.0, 50.0, -2.0, 53.0, "Flood Zone 2"),
        ],
    }


def test_loader_splits_combined_layer_by_risk(tmp_path: Path) -> None:
    src = tmp_path / "nrw.geojson"
    src.write_text(json.dumps(_nrw_collection()), encoding="utf-8")
    db = tmp_path / "hazards.duckdb"
    counts = load_nrw_flood_zones(source_path=src, db_path=db)
    assert counts == {NRW_FLOOD_ZONE_2_TABLE: 1, NRW_FLOOD_ZONE_3_TABLE: 1}


def test_lookup_returns_zone_3_inside_nrw_zone_3(tmp_path: Path) -> None:
    src = tmp_path / "nrw.geojson"
    src.write_text(json.dumps(_nrw_collection()), encoding="utf-8")
    db = tmp_path / "hazards.duckdb"
    load_nrw_flood_zones(source_path=src, db_path=db)
    coord = Coordinate(lat=51.5, lon=-3.5)
    assert lookup_flood_zone(coord, db) is FloodZone.ZONE_3


def test_lookup_returns_zone_2_inside_nrw_zone_2_only(tmp_path: Path) -> None:
    src = tmp_path / "nrw.geojson"
    src.write_text(json.dumps(_nrw_collection()), encoding="utf-8")
    db = tmp_path / "hazards.duckdb"
    load_nrw_flood_zones(source_path=src, db_path=db)
    # Point is inside the Zone 2 box but outside the Zone 3 box.
    coord = Coordinate(lat=50.5, lon=-2.5)
    assert lookup_flood_zone(coord, db) is FloodZone.ZONE_2


def test_lookup_returns_zone_1_outside_any_nrw_polygon(tmp_path: Path) -> None:
    src = tmp_path / "nrw.geojson"
    src.write_text(json.dumps(_nrw_collection()), encoding="utf-8")
    db = tmp_path / "hazards.duckdb"
    load_nrw_flood_zones(source_path=src, db_path=db)
    coord = Coordinate(lat=51.5, lon=0.5)  # east of Wales fixture box
    assert lookup_flood_zone(coord, db) is FloodZone.ZONE_1


def test_lookup_unions_ea_and_nrw_tables(tmp_path: Path) -> None:
    """A DB carrying both EA and NRW tables must answer correctly for points
    in either nation, using the same `lookup_flood_zone` call.
    """
    # EA fixture: Zone 3 = [-1, 0] x [51, 52]
    ea_z3 = tmp_path / "ea_z3.geojson"
    ea_z2 = tmp_path / "ea_z2.geojson"
    ea_z3.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [_feature(-1.0, 51.0, 0.0, 52.0, "ignored-for-ea")],
            }
        ),
        encoding="utf-8",
    )
    ea_z2.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [_feature(-2.0, 50.0, 1.0, 53.0, "ignored-for-ea")],
            }
        ),
        encoding="utf-8",
    )
    nrw_src = tmp_path / "nrw.geojson"
    nrw_src.write_text(json.dumps(_nrw_collection()), encoding="utf-8")

    db = tmp_path / "hazards.duckdb"
    load_ea_flood_zones(zone_2_geojson=ea_z2, zone_3_geojson=ea_z3, db_path=db)
    load_nrw_flood_zones(source_path=nrw_src, db_path=db)

    # English point inside EA Zone 3
    assert lookup_flood_zone(Coordinate(lat=51.5, lon=-0.5), db) is FloodZone.ZONE_3
    # Welsh point inside NRW Zone 3
    assert lookup_flood_zone(Coordinate(lat=51.5, lon=-3.5), db) is FloodZone.ZONE_3
    # Welsh point inside NRW Zone 2 only
    assert lookup_flood_zone(Coordinate(lat=50.5, lon=-2.5), db) is FloodZone.ZONE_2


def test_loader_idempotent_on_rerun(tmp_path: Path) -> None:
    src = tmp_path / "nrw.geojson"
    src.write_text(json.dumps(_nrw_collection()), encoding="utf-8")
    db = tmp_path / "hazards.duckdb"
    a = load_nrw_flood_zones(source_path=src, db_path=db)
    b = load_nrw_flood_zones(source_path=src, db_path=db)
    assert a == b
