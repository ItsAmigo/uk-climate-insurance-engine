"""Stream-convert a multi-GB GeoJSON FeatureCollection to NDJSON.

The streaming download writes per-page NDJSON and stitches into a single
GeoJSON FeatureCollection at the end. That FeatureCollection is the
canonical on-disk artefact for inspection / sharing, but DuckDB's
`read_json` cannot handle it without materialising the whole 2-2.5 GB
JSON object in memory (which OOMs on a 16 GB machine).

This script reverses the stitch: read the FeatureCollection character by
character and write each Feature as one line of NDJSON. Constant memory.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_CHUNK = 1 << 20  # 1 MiB


def stream_convert(geojson_path: Path, ndjson_path: Path) -> int:
    """Convert `geojson_path` (FeatureCollection) to `ndjson_path` (one Feature per line).

    Reads the source in 1-MiB binary chunks and walks each chunk once,
    tracking object-brace depth + quote state to slice out one Feature
    object at a time. Constant memory; multi-GB files complete in
    ~1-2 minutes per GB.
    """
    written = 0
    with geojson_path.open("rb") as src, ndjson_path.open("wb") as dst:
        head = src.read(_CHUNK)
        marker = b'"features":'
        idx = head.find(marker)
        if idx < 0:
            # Marker straddled an unlikely-to-be-multi-MB boundary; bail
            # rather than implement marker streaming for an edge case that
            # doesn't occur in practice for this dataset shape.
            raise ValueError(f"No `features` array found in first 1 MiB of {geojson_path}")
        idx = head.index(b"[", idx) + 1  # advance past the `[`
        chunk = head[idx:]

        feature_buf = bytearray()
        depth = 0
        in_string = False
        escape = False
        done = False

        while chunk:
            for byte in chunk:
                if depth == 0 and not in_string:
                    # Whitespace / comma between features at depth 0 — skip.
                    if byte in (0x20, 0x09, 0x0A, 0x0D, 0x2C):  # ' ', tab, \n, \r, ','
                        continue
                    if byte == 0x5D:  # ']'  end of features array
                        done = True
                        break
                    if byte != 0x7B:  # '{'
                        raise ValueError(
                            f"Expected '{{' starting feature, got {bytes([byte])!r} "
                            f"after writing {written} features"
                        )

                feature_buf.append(byte)
                if escape:
                    escape = False
                elif byte == 0x5C and in_string:  # backslash
                    escape = True
                elif byte == 0x22:  # double quote
                    in_string = not in_string
                elif not in_string:
                    if byte == 0x7B:  # '{'
                        depth += 1
                    elif byte == 0x7D:  # '}'
                        depth -= 1
                        if depth == 0:
                            dst.write(feature_buf)
                            dst.write(b"\n")
                            written += 1
                            feature_buf.clear()
                            if written % 50_000 == 0:
                                print(f"  {written:,} features written", flush=True)
            if done:
                break
            chunk = src.read(_CHUNK)

    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("geojson", type=Path, help="Source GeoJSON FeatureCollection")
    parser.add_argument(
        "--ndjson",
        type=Path,
        default=None,
        help="Destination NDJSON (default: same path with .ndjson extension)",
    )
    args = parser.parse_args(argv)

    src = args.geojson
    dst = args.ndjson or src.with_suffix(".ndjson")
    print(f"Converting {src} -> {dst}", flush=True)
    n = stream_convert(src, dst)
    print(f"Wrote {n:,} features.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
