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

# A spread of locations chosen so we hit Zone 1 / 2 / 3 across England.
# These are starting suggestions; substitute with the EA-website-verified
# results when filling in the findings table.
DEFAULT_POSTCODES: list[str] = [
    "SW1A 1AA",  # Buckingham Palace, central London — expected Zone 1 (raised)
    "YO1 9TR",  # York city centre — known Ouse floodplain, expected Zone 3
    "RG1 8DH",  # Reading, near the Thames — expected Zone 2 or 3
    "M1 1AE",  # Manchester city centre — mostly Zone 1
    "NG1 6HF",  # Nottingham, near River Trent — expected Zone 2 or 3
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
