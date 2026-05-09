"""Postcode-to-coordinate lookup against an ingested ONSPD table."""

from __future__ import annotations

from pathlib import Path

import duckdb

from climate_insurance.data.postcode_directory import ONSPD_TABLE

from .postcode import parse_postcode
from .types import Coordinate, Postcode


def lookup_postcode_coordinate(postcode: str | Postcode, db_path: Path) -> Coordinate | None:
    """Return the WGS84 coordinate for `postcode`, or None if not in the directory.

    Accepts either a raw string (which gets normalised + validated here) or an
    already-parsed `Postcode`. Raises `ValueError` if the input cannot be
    parsed as a valid UK postcode.
    """
    parsed = postcode if isinstance(postcode, Postcode) else parse_postcode(postcode)
    with duckdb.connect(str(db_path), read_only=True) as con:
        row = con.execute(
            f"SELECT lat, lon FROM {ONSPD_TABLE} WHERE postcode = ?",
            [parsed.normalized],
        ).fetchone()
    if row is None:
        return None
    return Coordinate(lat=float(row[0]), lon=float(row[1]))


__all__ = ["lookup_postcode_coordinate"]
