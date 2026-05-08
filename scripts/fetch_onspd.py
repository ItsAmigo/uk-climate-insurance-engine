"""Download, extract, and ingest the ONS Postcode Directory (ONSPD).

Run this once per quarter when ONS publishes a new release. The geoportal
item ID changes each quarter, so the URL is parametrised.

How to find the URL
-------------------
1. Visit https://geoportal.statistics.gov.uk/ and search for
   "ONS Postcode Directory".
2. Click the latest dated release (e.g. "ONS Postcode Directory (May 2026)").
3. Open the page's item-info JSON via:
       https://www.arcgis.com/sharing/rest/content/items/<ITEM_ID>?f=json
   where <ITEM_ID> is the 32-character hex string in the page URL.
4. The download URL is then:
       https://www.arcgis.com/sharing/rest/content/items/<ITEM_ID>/data
5. Pass that URL to this script via --url (or set ONSPD_URL in .env).

Licence: Open Government Licence v3.0 — Office for National Statistics.
The downloaded archive lives under data/raw/onspd/ which is gitignored.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

from climate_insurance.data.postcode_directory import load_onspd

USER_AGENT = (
    "climate-insurance-research/0.1 "
    "(project-lala portfolio; UK insurance pricing study; "
    "respectful single-shot quarterly download)"
)


def _download(url: str, dest: Path) -> None:
    """Stream the ONSPD ZIP to disk with a descriptive User-Agent."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url}\n  -> {dest}", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as resp, dest.open("wb") as out:
        shutil.copyfileobj(resp, out)
    print(f"Done — {dest.stat().st_size / 1_000_000:.1f} MB", flush=True)


def _extract(zip_path: Path, extract_dir: Path) -> Path:
    """Extract the ZIP and return the path to the UK-wide CSV inside it."""
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)
    # The UK-wide file follows the convention ONSPD_<MMM>_<YYYY>_UK.csv.
    candidates = sorted(extract_dir.rglob("ONSPD_*_UK.csv"))
    if not candidates:
        # Fall back to any single large CSV directly under Data/
        candidates = sorted(extract_dir.rglob("Data/ONSPD_*.csv"))
    if not candidates:
        raise FileNotFoundError(
            f"No ONSPD UK CSV found under {extract_dir}. "
            f"Expected something matching ONSPD_*_UK.csv."
        )
    return candidates[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        default=os.environ.get("ONSPD_URL"),
        help="Direct download URL for the ONSPD ZIP (or set ONSPD_URL in environment / .env).",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw/onspd"),
        help="Where to download and extract the ZIP (default: data/raw/onspd).",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/processed/hazards.duckdb"),
        help="DuckDB database path (default: data/processed/hazards.duckdb).",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Reuse an already-downloaded ZIP in --raw-dir.",
    )
    args = parser.parse_args(argv)

    extract_dir = args.raw_dir / "extracted"

    if not args.skip_download:
        if not args.url:
            parser.error(
                "No URL supplied. Pass --url or set ONSPD_URL. See module "
                "docstring for how to find the URL on geoportal."
            )
        zip_path = args.raw_dir / "ONSPD.zip"
        _download(args.url, zip_path)
    else:
        # Pick up any previously-downloaded ONSPD*.zip in the raw dir.
        candidates = sorted(args.raw_dir.glob("ONSPD*.zip"))
        if not candidates:
            parser.error(
                f"No ONSPD*.zip found in {args.raw_dir}; download first or "
                "drop a release ZIP in that directory."
            )
        zip_path = candidates[-1]
        print(f"Reusing existing ZIP: {zip_path}", flush=True)

    csv_path = _extract(zip_path, extract_dir)
    print(f"Ingesting {csv_path} -> {args.db}", flush=True)
    rows = load_onspd(csv_path, args.db)
    print(f"Loaded {rows:,} active postcodes into {args.db}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
