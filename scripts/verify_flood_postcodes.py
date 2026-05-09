"""Print the EA flood-zone result for a list of postcodes.

Use this to hand-validate the pipeline against the EA's public flood map at
https://check-long-term-flood-risk.service.gov.uk/postcode (England) — type
each postcode into the website and compare its 'flood from rivers and sea'
zone against what we predict here.

Phase 1 gate requires at least 5 hand-validated sample postcodes; the
results table goes into docs/findings.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from climate_insurance.hazards import lookup_postcode_flood_zone

# Five locations chosen to span Zone 1 / 2 / 3 across England with known
# geography, so the comparison against the EA public flood-map website
# (https://check-long-term-flood-risk.service.gov.uk/postcode) is
# unambiguous.
DEFAULT_POSTCODES: list[str] = [
    "SW1A 1AA",  # Buckingham Palace area, central London (raised) — expect Z1
    "YO1 7HH",  # York Minster area, between rivers Ouse and Foss — expect Z3
    "TW9 1AB",  # Kew, beside the Thames floodplain — expect Z2 or Z3
    "M1 1AE",  # Manchester city centre — mostly Z1
    "GL1 2HG",  # Gloucester city centre, near River Severn — expect Z3
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/processed/hazards.duckdb"),
        help="Path to the DuckDB database (default: data/processed/hazards.duckdb).",
    )
    parser.add_argument(
        "postcodes",
        nargs="*",
        help="Postcodes to look up; defaults to a built-in spread.",
    )
    args = parser.parse_args(argv)

    postcodes = args.postcodes or DEFAULT_POSTCODES
    print(f"{'Postcode':<12} | {'EA Flood Zone (predicted)':<26}")
    print(f"{'-' * 12}-+-{'-' * 26}")
    for pc in postcodes:
        try:
            zone = lookup_postcode_flood_zone(pc, args.db)
        except ValueError as exc:
            print(f"{pc:<12} | ERROR: {exc}")
            continue
        if zone is None:
            print(f"{pc:<12} | NOT IN ONSPD")
        else:
            print(f"{pc:<12} | Zone {int(zone)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
