# Methodology

This document is the canonical record of analytical choices in the Climate
Insurance Engine. Each section is filled out as the corresponding phase is
completed. Every numerical claim cites a source.

## 1. Scope and intended use

The engine produces a postcode-level *current-state hazard exposure* for
residential property in the United Kingdom, projects that exposure
forward to 2030 / 2050 / 2070 under three IPCC AR6 climate scenarios
(SSP1-2.6, SSP2-4.5, SSP5-8.5), translates exposure to expected
loss-cost using published damage curves, and audits the resulting
premium distribution for fairness with respect to the UK Indices of
Multiple Deprivation.

**Intended use.** Portfolio demonstration of UK insurance pricing
methodology and Consumer Duty thinking, aimed at graduate-level roles
in insurance pricing and consulting analytics. Not a regulated pricing
tool; not for use in actual underwriting decisions.

**Explicit non-goals.** We are *consumers* of UKCP18 and IPCC AR6
outputs, not climate modellers (CLAUDE.md hard rule 8). Damage curves
come from published peer-reviewed literature (CLAUDE.md hard rule 9).
Subsidence is modelled as a clay-shrink-swell proxy from the BGS Soil
Parent Material map; we do not attempt to model landslip, soluble-rock
collapse, or compressible-ground subsidence (those would require the
licensed BGS GeoSure product). The pricing layer is a frequency-severity
plus Tweedie GBM family — not a full reserving system, no IBNR, no
investment-income offset.

## 2. Hazard data

This section covers the Phase 1 hazard-ingestion layer: data sources,
coordinate-reference choices, the spatial-index design, the
classification rules used to map raw data into the public
`HazardProfile` shape, and the sample-postcode validation.

### 2.1 Data sources and pinned releases

| Layer | Source | Release | Licence | Records |
|---|---|---|---|---|
| Postcode → coordinate | ONS Postcode Directory | February 2026 | OGL v3.0 | 1,794,940 active UK postcodes |
| England flood zones | Environment Agency Flood Map for Planning (Rivers and Sea), ArcGIS Hub Feature Service | November 2023 | OGL v3.0 | 230,729 Zone-3 + 552,811 Zone-2 polygons |
| Subsidence proxy (GB) | British Geological Survey Soil Parent Material 1km | V1, 2019 | OGL v3.0 | 241,514 1km grid cells |
| Wales / Scotland / NI flood zones | Natural Resources Wales / SEPA / DfI Rivers | _(pending — Phase 1 follow-up slice)_ | OGL v3.0 | _(pending)_ |
| Wind | _(pending — Phase 1 follow-up slice)_ | — | — | — |

Per-source licence terms, attribution strings, refresh cadence, and
gotchas live in `docs/data_sources.md`. The ONSPD is updated quarterly;
the EA flood map and BGS SPM are updated infrequently. The pinned
release column is the version active at the time of writing — refresh
commands (`make ingest-onspd`, `make ingest-ea-flood`,
`make ingest-bgs-spm`) live in the Makefile and update the local
`data/processed/hazards.duckdb` warehouse from the latest release each
source publishes.

### 2.2 Coordinate reference system

All geometries in the warehouse are stored in **WGS84 geographic
coordinates (EPSG:4326)** in `(longitude, latitude)` axis order. This
matches the coordinate system used by the ONSPD postcode centroids,
GeoJSON in general, and every web-mapping library we will use in
Phase 4 (MapLibre GL JS, Leaflet). Data sourced in other projections
(notably the EA Feature Service and the BGS SPM, both native British
National Grid / EPSG:27700) is reprojected at ingest:

- **EA flood polygons.** We pass `outSR=4326` to the ArcGIS query API,
  so polygons arrive in WGS84 and require no further transformation.
- **BGS Soil Parent Material.** Reprojected in DuckDB at ingest using
  `ST_Transform(geom, 'EPSG:27700', 'EPSG:4326')` followed by
  `ST_FlipCoordinates`. The flip is required because EPSG:4326's
  authority-defined axis order is `(latitude, longitude)`, opposite to
  the `(longitude, latitude)` convention every other layer uses; without
  it, point-in-polygon hits would be silently wrong.

The decision to standardise on WGS84 end-to-end is logged in
`docs/decisions.md` (2026-05-09).

### 2.3 Spatial backend

We use DuckDB with its first-party `spatial` extension as the
analytical store. R-tree indexes are built on every polygon table
(`CREATE INDEX ... USING RTREE (geom)`), which makes point-in-polygon
lookups O(log N) regardless of the underlying polygon count — a
single-postcode query against the 783,540 EA flood polygons returns in
single-digit milliseconds.

PostGIS would be a defensible alternative but introduces a separate
Postgres server and migration overhead that doesn't pay off until
Phase 3, when the API needs concurrent reads. The DuckDB-spatial query
vocabulary (`ST_Contains`, `ST_GeomFromText`, `ST_Transform`,
`ST_GeomFromGeoJSON`) is one-to-one with PostGIS, so the cutover at
Phase 3 will not require any lookup-code rewrites. Decision logged
in `docs/decisions.md` (2026-05-09).

### 2.4 Classification rules

The public `HazardProfile` exposes three coarse categorical fields:
`flood_zone` (`ZONE_1` / `ZONE_2` / `ZONE_3`), `subsidence_class`
(`LOW` / `MEDIUM` / `HIGH`), and `windstorm_band` (`None` until the
wind-data slice lands). The mapping from raw layers to these enums is
deliberately simple and documented in code:

**Flood zones (`hazards/flood.py`).** A postcode coordinate is queried
against the EA Zone 3 polygons first; if any contain the point, the
result is `ZONE_3` (high probability — more than 1-in-100 annual
chance from rivers, or 1-in-200 from the sea, per the EA scheme).
Otherwise the Zone 2 polygons are queried; if any contain the point,
the result is `ZONE_2` (medium — 1-in-1,000 to 1-in-100). Otherwise
the result is `ZONE_1` (low — outside the published zones; this is
the implicit default rather than a separately-loaded layer because
`ZONE_1` is by definition "everything else").

The Zone 3-takes-precedence rule reflects the EA's own scheme: Zone 3
is a stricter subset of areas the EA consider at higher probability,
so wherever both apply, Zone 3 is the load-bearing classification.

**Subsidence (`hazards/subsidence.py`).** The BGS SPM `SOIL_GROUP`
field uses a HEAVY / MEDIUM / LIGHT shorthand for grain-class
dominance, often as compound descriptions like `"MEDIUM TO LIGHT(SILTY)
TO HEAVY"` listing the constituent classes in dominance order. We
classify each cell by reading the **first-listed token only** (the
dominant grain class for that cell):

- `HIGH` if the dominant token starts with `"HEAVY"`. Heavy clays
  drive the bulk of UK subsidence claims through shrink-swell.
- `LOW` if the dominant token starts with `"LIGHT"` AND no `"HEAVY"`
  appears anywhere in the description. Sandy soils have negligible
  shrink-swell potential.
- `MEDIUM` otherwise. Covers `"MEDIUM"`-dominant cells, mixed-class
  cells where any `"HEAVY"` is present in the trailing tokens (mixed
  clay-sand), and the special `"PEAT"` and `"ALL"` and `"NA"` cases
  (peat is a compressibility risk rather than a shrink-swell risk; we
  bucket it as `MEDIUM` and flag the limitation).

The mapping function (`_subsidence_class_from_soil_group`) lives in
code rather than the database, so the methodology can be changed in a
single-line edit with no data re-ingest required. The choice of
"dominant-class" over "any-mention-of-HEAVY" or "literature-cited
mapping" is logged in `docs/decisions.md` (2026-05-09); briefly, the
dominant-class rule is deterministic, faithful to the BGS user-guide
documentation of token ordering, and avoids the over-flagging that a
conservative any-HEAVY-equals-HIGH rule would produce.

**Coverage gap.** BGS SPM does not cover Northern Ireland. The lookup
function returns `SubsidenceClass.MEDIUM` for any coordinate outside
the loaded grid as a neutral fallback rather than raising or returning
None — neutral is the least-misleading default in the absence of data.
This is a known limitation; a future slice could substitute a
Northern-Ireland-specific source (e.g. the Geological Survey of
Northern Ireland's GSNI BedrockGeology), at which point the fallback
narrows to "outside both GB and NI coverage", which would only ever
fire for offshore coordinates.

### 2.5 Data-quality filtering

Two corruption patterns in the EA flood data required loader-level
filtering, each visible in `data/ea_flood_zones.py`:

1. **All-null coordinate arrays** (e.g.
   `{"coordinates": [[[null, null, ...]]]}`). These crash
   `ST_GeomFromGeoJSON` on parse. Filtered by string match
   (`json_extract_string(geometry, '$') NOT LIKE '%null%'`) before
   the geometry constructor sees them.
2. **All-null parsed silently into a planet-spanning polygon**
   (`POLYGON((-180 -90, ..., 180 90))`). Exactly one such row exists
   in the November 2023 Zone 2 release. Filtered by a UK bounding-box
   sanity check on the parsed envelope: every polygon's
   `ST_XMin` / `ST_XMax` must lie in `[-10, 5]` and every `ST_YMin` /
   `ST_YMax` in `[49, 62]`.

Cumulative loss from these filters is well under 0.1 % of features in
either zone. Records dropped: 325 of 231,054 in Zone 3, 347 of 553,158
in Zone 2.

### 2.6 Memory + format choices for the EA ingest

The EA Feature Service has no single-file bulk download — extraction
must paginate the `query` endpoint at the API limit of 2,000 features
per request. A full pull of both zones is ≈ 400 paginated requests
across ≈ 25–30 minutes of wall time (`scripts/fetch_ea_flood_zones.py`,
0.2-second courtesy sleep between requests).

DuckDB's `read_json` materialises the whole JSON object before
unnesting, which OOMs on the resulting 2.0 GB Zone 3 and 2.5 GB
Zone 2 GeoJSON files (the per-object `maximum_object_size` parameter
caps at 4 GB anyway, set by a UINT32 ceiling). The loader therefore
prefers a per-feature **NDJSON** form (one Feature per line) read via
`read_ndjson` in constant memory. The streaming download writes NDJSON
directly during the paginated pull; a separate `geojson_to_ndjson.py`
script can re-derive NDJSON from a previously-stitched FeatureCollection
in ≈ 30 seconds per GB if needed.

For real-data ingest the script also passes `memory_limit='10GB'` and
`threads=1` to DuckDB. Single-threaded keeps the parse-side memory
multiplier in check; tests that load tiny synthetic fixtures pass no
memory tuning so they remain fast and portable.

### 2.7 Hand-validation results

Five UK postcodes spanning Zone 1 / 2 / 3, predicted by the
`postcode_to_hazards()` pipeline and cross-checked against the EA's
official "Check long term flood risk" service at
https://check-long-term-flood-risk.service.gov.uk/postcode :

| Postcode  | Location                                           | Predicted | EA service | Match |
|-----------|----------------------------------------------------|-----------|------------|-------|
| TA9 3ER   | Highbridge, Somerset Levels                        | ZONE_3    | High       | ✓     |
| HU4 7BY   | Hull (city below sea level in places)              | ZONE_3    | High       | ✓     |
| YO1 9SL   | York city centre, immediately west of the Ouse     | ZONE_3    | High       | ✓     |
| OX14 5JA  | Abingdon-on-Thames                                 | ZONE_2    | Medium     | ✓     |
| SW1A 1AA  | Buckingham Palace (raised above the Thames)        | ZONE_1    | Very low   | ✓     |

Both sides of the comparison ultimately read the same EA polygons, so
this is a pipeline-correctness check rather than an independent
prediction. Pipeline-correctness is the load-bearing claim — it
confirms the ingest, reprojection, R-tree index, and lookup chain
together reproduce the canonical classification.

A 5,000-postcode random-sample check returned 4.6 % of postcodes in
Zone 3 and 6.9 % in Zone 2. These figures are consistent with the EA's
public statement that approximately 5.2 million English properties
(≈ 17 % of all properties) are at flood risk from rivers and the sea —
postcode-level density in cities (which are often not on floodplains)
brings the postcode-level hit rate below the property-level figure.
The full validation entry is in `docs/findings.md` (2026-05-09).

### 2.8 Property-based tests

`tests/test_hazard_properties.py` encodes four invariants the
downstream pricing layer will rely on:

1. `int(FloodZone.ZONE_1) < int(FloodZone.ZONE_2) < int(FloodZone.ZONE_3)` —
   the enum ordering is the contract LightGBM monotonic constraints
   will pin.
2. `int(SubsidenceClass.LOW) < int(SubsidenceClass.MEDIUM) < int(SubsidenceClass.HIGH)` —
   same contract for subsidence.
3. The subsidence dominant-class rule is monotonic in `"HEAVY"` content:
   adding `" TO HEAVY"` to any `SOIL_GROUP` string never lowers the
   resulting class. (Verified by Hypothesis across the four dominant-
   token bases the BGS data uses.)
4. Lookup idempotency: querying the same postcode (or coordinate)
   twice returns the same result. (Verified by Hypothesis across
   normalisation-equivalent postcode forms and across uniformly-sampled
   UK coordinates.)

## 3. Current-state risk model
_(Phase 2 — exposure data choice, frequency-severity vs Tweedie, monotonic
constraints on hazard features, validation strategy, ABI sanity-check rule)_

## 4. Climate scenarios and forward projections
_(Phase 3 — UKCP18 subset chosen, SSP-to-RCP mapping, downscaling approach,
damage-curve choices with citations)_

## 5. Productionisation
_(Phase 4 — API contract, caching strategy, frontend interactions, deployment
topology, rollback plan)_

## 6. Fairness analysis
_(Phase 5 — IMD harmonisation across the four nations, fairness metric definitions,
Consumer Duty linkage)_

## 7. Validation against industry aggregates
_(Phase 2 + 6 — ABI comparison rule: divergence > 20% triggers a documented
explanation per CLAUDE.md hard rule 4)_

## 8. Limitations
_(Phase 6 — known biases, data gaps, model assumptions, what we are NOT modelling)_

## 9. Glossary cross-reference
See [CLAUDE.md](../CLAUDE.md) "Vocabulary glossary" section.
