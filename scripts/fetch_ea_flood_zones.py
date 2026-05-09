"""Download Environment Agency Flood Zones 2 + 3 (England) and ingest to DuckDB.

Source: Environment Agency Flood Map for Planning (Rivers and Sea), published
on the EA's own ArcGIS Hub at
    https://services1.arcgis.com/JZM7qJpmv7vJ0Hzx/arcgis/rest/services/Flood_Map_for_Planning/FeatureServer
under the Open Government Licence v3.0. We exclude the climate-change
overlay (CLAUDE.md hard rule 8) and pull each zone via paginated GeoJSON
queries with `outSR=4326` so the response arrives in WGS84 ready for our
ONSPD-coordinate-aligned pipeline.

Layer indices on the FeatureServer:
- 1 = Flood_Zone_3 (~231 k features)
- 2 = Flood_Zone_2 (~553 k features)

The query API returns at most 2000 features per call, so a full pull is
~400 paginated requests across ~25-30 minutes on a typical home connection.
We sleep 0.2 s between requests as a courtesy.
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

from climate_insurance.data.ea_flood_zones import load_ea_flood_zones

USER_AGENT = (
    "climate-insurance-research/0.1 "
    "(project-lala portfolio; UK insurance pricing study; "
    "respectful paginated quarterly download)"
)

BASE_URL = (
    "https://services1.arcgis.com/JZM7qJpmv7vJ0Hzx/"
    "arcgis/rest/services/Flood_Map_for_Planning/FeatureServer"
)
PAGE_SIZE = 2000
SLEEP_SECONDS = 0.2

LAYERS = {
    "flood_zone_3": 1,
    "flood_zone_2": 2,
}


def _fetch_layer(layer_id: int, label: str, out_path: Path) -> int:
    """Stream features from the Feature Service into a per-page line-delimited
    JSON file, then stitch into a single GeoJSON FeatureCollection at the end.

    Streaming via NDJSON keeps memory usage flat regardless of feature count
    (the EA Zone 2 layer is 553k features ~ multi-GB of JSON which would not
    fit comfortably in RAM). The final GeoJSON file is what the loader reads;
    the `.ndjson` staging file is removed once the merge succeeds.
    """
    print(f"==> {label} (layer {layer_id})", flush=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    staging = out_path.with_suffix(".ndjson")
    offset = 0
    if staging.exists():
        # Resume: count lines already written; assume each is one feature.
        offset = sum(1 for _ in staging.open(encoding="utf-8"))
        print(f"  resuming at offset {offset:,}", flush=True)

    written = offset
    with staging.open("a", encoding="utf-8") as ndjson:
        while True:
            params = {
                "where": "1=1",
                "outFields": "*",
                "returnGeometry": "true",
                "outSR": "4326",
                "resultOffset": str(offset),
                "resultRecordCount": str(PAGE_SIZE),
                "f": "geojson",
            }
            url = f"{BASE_URL}/{layer_id}/query?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    page = json.loads(r.read().decode("utf-8"))
            except Exception as exc:
                print(f"  page {offset} ERROR: {exc}; sleeping 5s and retrying", flush=True)
                time.sleep(5)
                continue
            chunk: list[dict[str, Any]] = page.get("features", [])
            for feat in chunk:
                ndjson.write(json.dumps(feat))
                ndjson.write("\n")
            ndjson.flush()
            offset += len(chunk)
            written += len(chunk)
            if offset % 20_000 == 0 or len(chunk) < PAGE_SIZE:
                print(f"  {label}: {offset:,} features", flush=True)
            if len(chunk) < PAGE_SIZE:
                break
            time.sleep(SLEEP_SECONDS)

    # Stitch NDJSON into a single GeoJSON FeatureCollection on disk.
    print(f"  {label}: stitching to {out_path}", flush=True)
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
    print(f"  {label}: TOTAL {written:,} features -> {out_path}", flush=True)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw/ea_flood_zones"),
        help="Where to write the GeoJSON files (default: data/raw/ea_flood_zones).",
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

    geojson_paths: dict[str, Path] = {label: args.raw_dir / f"{label}.geojson" for label in LAYERS}

    if not args.skip_download:
        for label, layer_id in LAYERS.items():
            _fetch_layer(layer_id, label, geojson_paths[label])
    else:
        for _label, p in geojson_paths.items():
            if not p.exists():
                parser.error(f"--skip-download set but {p} does not exist")
            print(f"Reusing existing {p}", flush=True)

    # Prefer NDJSON if available — DuckDB's read_json can't stream the
    # multi-GB single-FeatureCollection form without OOMing. The
    # geojson_to_ndjson script (or future fetcher) writes per-feature lines
    # that read_ndjson handles in constant memory.
    ingest_paths: dict[str, Path] = {}
    for label, p in geojson_paths.items():
        ndjson = p.with_suffix(".ndjson")
        if ndjson.exists():
            print(f"Using NDJSON form: {ndjson}", flush=True)
            ingest_paths[label] = ndjson
        else:
            ingest_paths[label] = p

    print(f"Ingesting -> {args.db}", flush=True)
    counts = load_ea_flood_zones(
        zone_2_geojson=ingest_paths["flood_zone_2"],
        zone_3_geojson=ingest_paths["flood_zone_3"],
        db_path=args.db,
        memory_limit="10GB",
        threads=1,
    )
    for table, n in counts.items():
        print(f"  {table}: {n:,} polygons", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
