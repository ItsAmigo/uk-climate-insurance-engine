"""Download the BGS Soil Parent Material 1km GeoPackage and ingest to DuckDB.

Source: British Geological Survey, free 1km-resolution release of the Soil
Parent Material Model. Open Government Licence v3.0 with BGS attribution.
The download URL is a stable WordPress media-id endpoint on bgs.ac.uk.

Run this once per BGS release (releases are infrequent — current pinned
version is V1, dated 2019).
"""

from __future__ import annotations

import argparse
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

from climate_insurance.data.bgs_soil_parent_material import load_bgs_spm

USER_AGENT = (
    "climate-insurance-research/0.1 "
    "(project-lala portfolio; UK insurance pricing study; "
    "respectful single-shot one-time download)"
)

# Stable BGS media-id endpoint for the GeoPackage release.
DEFAULT_URL = "https://www.bgs.ac.uk/?wpdmdl=49018"


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url}\n  -> {dest}", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as resp, dest.open("wb") as out:
        shutil.copyfileobj(resp, out)
    print(f"Done - {dest.stat().st_size / 1_000_000:.1f} MB", flush=True)


def _extract(zip_path: Path, extract_dir: Path) -> Path:
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)
    candidates = sorted(extract_dir.rglob("*Parent*Material*1km*.gpkg"))
    if not candidates:
        candidates = sorted(extract_dir.rglob("*.gpkg"))
    if not candidates:
        raise FileNotFoundError(f"No .gpkg file found under {extract_dir}")
    return candidates[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL, help="BGS download URL.")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw/bgs_spm"),
        help="Where to download and extract the ZIP.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/processed/hazards.duckdb"),
        help="DuckDB database path.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Reuse an already-downloaded ZIP / extracted GeoPackage.",
    )
    args = parser.parse_args(argv)

    extract_dir = args.raw_dir / "extracted"

    if not args.skip_download:
        zip_path = args.raw_dir / "SoilParentMaterial1km.zip"
        _download(args.url, zip_path)
    else:
        candidates = sorted(args.raw_dir.glob("SoilParentMaterial*.zip"))
        if not candidates:
            parser.error(
                f"No SoilParentMaterial*.zip in {args.raw_dir}; "
                "download first or drop a release ZIP in that directory."
            )
        zip_path = candidates[-1]
        print(f"Reusing existing ZIP: {zip_path}", flush=True)

    gpkg_path = _extract(zip_path, extract_dir)
    print(f"Ingesting {gpkg_path} -> {args.db}", flush=True)
    rows = load_bgs_spm(gpkg_path, args.db)
    print(f"Loaded {rows:,} 1km soil-parent-material cells into {args.db}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
