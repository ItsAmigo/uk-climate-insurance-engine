"""Download Natural Resources Wales Flood Map for Planning and ingest to DuckDB.

Source: NRW Flood Map for Planning Zones 2 and 3, served via DataMapWales'
GeoServer WFS at
    https://datamap.gov.wales/geoserver/ows
under the Open Government Licence v3.0. We pull the combined
`inspire-nrw:NRW_FLOODZONE_RIVERS_SEAS_MERGED` layer (which carries both
zones in a single `risk` attribute), request `srsName=EPSG:4326` for
WGS84 output, and paginate with WFS 2.0 `startIndex` / `count` params.

Wales is far smaller than England (no half-million-polygon layer), so a
full pull is a handful of pages rather than hundreds.

CLAUDE.md compliance:
- Hard rule 2 (no aggressive scraping): respectful 0.2s sleep between
  pages; named user-agent string for source attribution.
- Hard rule 8 (no climate model output): we ingest the published
  flood-zone polygons only; UKCP18 is applied separately in Phase 3.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from climate_insurance.data.nrw_flood_zones import load_nrw_flood_zones

USER_AGENT = (
    "climate-insurance-research/0.1 "
    "(project-lala portfolio; UK insurance pricing study; "
    "respectful paginated download)"
)

BASE_URL = "https://datamap.gov.wales/geoserver/ows"
TYPE_NAME = "inspire-nrw:NRW_FLOODZONE_RIVERS_SEAS_MERGED"
PAGE_SIZE = 1000
SLEEP_SECONDS = 0.2


def _fetch_features(out_path: Path) -> int:
    """Stream NRW flood-zone features into a line-delimited JSON file.

    Each page response is a GeoJSON FeatureCollection. We write features
    one-per-line so the loader's NDJSON path can read in constant memory.
    Resumable: counts existing lines on restart.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    staging = out_path.with_suffix(".ndjson")
    start = 0
    if staging.exists():
        start = sum(1 for _ in staging.open(encoding="utf-8"))
        print(f"  resuming at startIndex {start:,}", flush=True)

    written = start
    with staging.open("a", encoding="utf-8") as ndjson:
        while True:
            params = {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeNames": TYPE_NAME,
                "outputFormat": "application/json",
                "srsName": "EPSG:4326",
                "startIndex": str(start),
                "count": str(PAGE_SIZE),
            }
            url = f"{BASE_URL}?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    page = json.loads(r.read().decode("utf-8"))
            except Exception as exc:
                print(f"  page {start} ERROR: {exc}; sleeping 5s and retrying", flush=True)
                time.sleep(5)
                continue
            chunk: list[dict[str, Any]] = page.get("features", [])
            for feat in chunk:
                ndjson.write(json.dumps(feat))
                ndjson.write("\n")
            ndjson.flush()
            start += len(chunk)
            written += len(chunk)
            print(f"  fetched {start:,} features", flush=True)
            if len(chunk) < PAGE_SIZE:
                break
            time.sleep(SLEEP_SECONDS)

    print(f"  stitching to {out_path}", flush=True)
    with out_path.open("w", encoding="utf-8") as out, staging.open(encoding="utf-8") as nd:
        out.write('{"type":"FeatureCollection","features":[')
        first = True
        for line in nd:
            line = line.strip()
            if not line:
                continue
            if not first:
                out.write(",")
            out.write(line)
            first = False
        out.write("]}")
    staging.unlink()
    print(f"  TOTAL {written:,} features -> {out_path}", flush=True)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw/nrw_flood_zones"),
        help="Where to write the GeoJSON file (default: data/raw/nrw_flood_zones).",
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
        help="Reuse existing GeoJSON in --raw-dir; just ingest into DuckDB.",
    )
    args = parser.parse_args(argv)

    geojson_path = args.raw_dir / "nrw_flood_zones.geojson"

    if not args.skip_download:
        _fetch_features(geojson_path)
    else:
        if not geojson_path.exists():
            parser.error(f"--skip-download set but {geojson_path} does not exist")
        print(f"Reusing existing {geojson_path}", flush=True)

    ndjson_path = geojson_path.with_suffix(".ndjson")
    ingest_path = ndjson_path if ndjson_path.exists() else geojson_path
    print(f"Ingesting {ingest_path} -> {args.db}", flush=True)

    counts = load_nrw_flood_zones(
        source_path=ingest_path,
        db_path=args.db,
        memory_limit="10GB",
        threads=1,
    )
    for table, n in counts.items():
        print(f"  {table}: {n:,} polygons", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
