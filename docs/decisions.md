# Decision log

Every non-trivial choice goes here as a dated entry. One paragraph per decision.

**Format:** `## YYYY-MM-DD — Title` followed by *what was considered*, *what
was chosen*, *why*. New entries at the top.

---

## 2026-05-15 — Wales flood source: NRW Flood Map for Planning via DataMapWales WFS
Considered three ways to obtain Welsh flood-zone polygons: (a) the Flood
Risk Assessment Wales (FRAW) layer — NRW's newer post-2020 *risk-of-flooding*
product that bands locations into High/Medium/Low after accounting for
defences, (b) the older Flood Map for Planning (FMP) Zones 2 & 3 — the
direct semantic twin of the EA dataset we already ingested for England,
or (c) the surface-water and small-watercourses layer. Chose (b),
specifically the `inspire-nrw:NRW_FLOODZONE_RIVERS_SEAS_MERGED` layer
served from `https://datamap.gov.wales/geoserver/ows`. Rationale:
zone-equivalence with EA is the cleanest harmonisation — the `risk`
attribute carries the literal strings *"Flood Zone 2"* and *"Flood Zone 3"*
which parse straight onto our `FloodZone` enum with no judgement calls.
FRAW (a) was rejected because mapping "High / Medium / Low" onto EA zone
semantics requires assumptions about defended-vs-undefended state that
would diverge across the four nations and bury a methodological
inconsistency in the model. Surface water (c) was excluded for the same
reason it's excluded for EA: the Flood Map for Planning scope doesn't
include surface-water flooding. The WFS supports server-side reprojection
to EPSG:4326 via `srsName=EPSG:4326`, so unlike the BGS pipeline we
avoid a client-side `ST_Transform` step at ingest.

## 2026-05-09 — Spatial backend: DuckDB `spatial` extension (not PostGIS)
Considered: PostGIS (the production-grade spatial database, used by every
serious GIS team) vs DuckDB's first-party `spatial` extension. PostGIS is
more battle-tested for huge concurrent workloads, but it requires running
a separate Postgres server, managing migrations, and adds operational
overhead that doesn't pay off until Phase 3 when the API needs concurrent
reads. DuckDB-spatial is built into the same in-process database we
already use for ONSPD, supports R-tree indexes, GeoJSON / GeoPackage
ingest, and the full `ST_*` query vocabulary we need (`ST_Contains`,
`ST_Point`, `ST_GeomFromGeoJSON`). Chose DuckDB-spatial. Phase 3 will
revisit when we move to Postgres for the API; the spatial query patterns
translate one-to-one to PostGIS so the cutover is safe.

## 2026-05-09 — EA flood-zone source: ArcGIS Hub Feature Service, paginated
Considered three ways to obtain the Environment Agency Flood Map for
Planning data: (a) the Defra Data Services Platform UI (the "official"
front door, but JavaScript-only and offers no programmatic download
URL), (b) the EA's ArcGIS Hub Feature Service (the canonical hosted
copy, Open Government Licence, public, paginated query API), or
(c) third-party Esri UK republications (ambiguous freshness, may be
stale). Chose (b) — the EA's own Hub Feature Service at
`services1.arcgis.com/JZM7qJpmv7vJ0Hzx`. The Feature Service has no
single-download URL because the dataset is too large for synchronous
export, so we paginate through the `query` endpoint at 2000 features
per call (~400 calls, ~25-30 min total) with a polite 0.2s sleep
between calls. This is reproducible from a public repo without browser
automation, scraping JavaScript, or relying on a third party.

## 2026-05-09 — Subsidence dominant-class rule: first-listed SOIL_GROUP token
Considered three ways to map BGS SPM `SOIL_GROUP` (which uses compound
descriptions like "MEDIUM TO LIGHT(SILTY) TO HEAVY") to a 3-level
subsidence-risk class: (a) dominant-class rule reading the *first* token
in the compound, (b) any-mention-of-HEAVY-equals-HIGH conservative rule,
(c) literature-cited mapping from a published UK geotech paper. Chose
(a). Rationale: BGS lists tokens in dominance order per the SPM user
guide, so the first token is by definition the prevalent grain class for
that 1 km cell. The rule is deterministic, lives in code at
`hazards/subsidence._subsidence_class_from_soil_group`, and the entire
methodology fits in a paragraph in `methodology.md`. Conservative rule
(b) was rejected because it would over-flag every cell that has *any*
heavy clay content, inflating the subsidence-claim pool well above what
ABI aggregate stats show. Literature mapping (c) was rejected for now
because no UK paper directly maps BGS SPM tokens — would require ~30 min
of search and may not exist; we can revisit if a reviewer asks.

## 2026-05-09 — Subsidence-data REVERSAL: BGS SPM 1km, not DEFRA Soilscapes
Reverses the 2026-05-08 decision below. The earlier decision claimed
"Soilscapes is fully open under OGL v3.0", but on actually checking the
data.gov.uk record and the Cranfield LandIS terms, Soilscapes is
**Cranfield-owned** and the licence explicitly says *"Soilscapes is not
intended as a means for supporting … commercial activities"* with a
required licensing agreement. A portfolio project explicitly built to
land a commercial-industry job is borderline non-compliant.

Switched to **BGS Soil Parent Material 1km** as the subsidence proxy. The
1 km free release is genuinely Open Government Licence v3.0, hosted
directly by BGS at a stable WordPress media-id endpoint
(`https://www.bgs.ac.uk/?wpdmdl=49018`), and covers Great Britain
(England + Wales + Scotland; Northern Ireland is not covered, falls back
to MEDIUM in the lookup). The relevant attribute is `SOIL_GROUP` which
uses HEAVY/MEDIUM/LIGHT shorthand mapping closely to clay-driven
shrink-swell potential.

Trade-offs: SPM is a simpler categorical classification than Soilscapes
(HEAVY/MEDIUM/LIGHT vs Soilscapes' detailed soil-association classes),
but the subsidence question only needs grain-class-driven shrink-swell
risk anyway, so the simpler categorical input is fit-for-purpose. The
SOIL_GROUP -> SubsidenceClass mapping rule is logged separately above.

## 2026-05-09 — Coordinate reference system: WGS84 (EPSG:4326) end-to-end
Considered: ingest in British National Grid (EPSG:27700, the EA's
native CRS) and reproject at lookup time vs request `outSR=4326` from
the Feature Service so data arrives in WGS84 already. The ONSPD
coordinates are in WGS84, so reprojecting on ingest aligns everything
in a single coordinate system from the start. The accuracy loss in
reprojection is well under the resolution of the postcode-centroid
input. Chose ingest-time reprojection via `outSR=4326`. The choice
also makes downstream display on web maps (which expect WGS84) free.

## 2026-05-08 — Subsidence data source: DEFRA Soilscapes (not BGS GeoSure)
Considered: BGS GeoSure (richest UK subsidence dataset, scores shrink-swell
clay risk directly) vs DEFRA Soilscapes (broader soil-type classification,
not subsidence-specific). GeoSure is the better signal but its licence
permits viewing only — the underlying numbers cannot be redistributed
without a paid commercial licence, which would prevent publishing the
ingestion code on a public GitHub repo and would compromise the "anyone
can reproduce this pipeline" portfolio story. Soilscapes is fully open
under OGL v3.0. Chose Soilscapes: the portfolio value of a fully
reproducible open pipeline outweighs the resolution loss, and the
methodology write-up will be explicit that subsidence is approximated
from soil type rather than measured from a subsidence-specific model. If
the project later attracts funding for a paid GeoSure licence, the
ingestion layer can swap sources behind the same `subsidence_class`
interface without touching downstream code.

## 2026-05-08 — Pinned ONSPD release: February 2026; refresh via parametrised URL
Considered: hardcoding a download URL in the loader vs parametrising it via
CLI argument / env var. Chose parametrised because the geoportal item ID
changes every quarter — hardcoding would mean a code change every refresh.
The fetch script (`scripts/fetch_onspd.py`) takes `--url` (or reads
`ONSPD_URL` from env), the data source documentation in
`docs/data_sources.md` records the *current* pinned release for
reproducibility, and the loader itself is source-agnostic (takes a CSV
path, knows nothing about URLs). Currently pinned: ONSPD February 2026,
ArcGIS Hub item `3080229224424c9cb53c0b48f5a64d27`, 1,794,940 active
postcodes loaded.

## 2026-05-08 — ONSPD column-naming convention: post-2024 `<year>cd` form
Considered: writing the loader against the older `lsoa11` / `oslaua` /
`ctry` names (still seen in tutorials and many open-source projects) vs
the current `lsoa11cd` / `lad25cd` / `ctry25cd` form. Chose the current
form because (a) it's what the actual Feb 2026 file ships with, and (b)
the year suffix on `lad25cd` and `ctry25cd` is a real signal — the LAD
and country boundary sets are versioned and the projection-layer code
(Phase 3) will need to know which vintage. The mapping into our internal
`postcode_directory` table re-aliases to short names (`lad`, `ctry`)
because we don't expose the year boundary in the public API.

## 2026-05-08 — Postcode-handling layer is pure-code, lives in `hazards/postcode.py`
Considered: bundling postcode normalisation into the spatial-lookup
function vs splitting it into its own pure-Python module. Chose split
because (a) postcode parsing has zero dependency on the loaded hazard
data, so it can ship and be tested before any ingestion lands, and (b)
the normalisation rules (uppercase, single space, GIR special case) are
well-defined regex logic that benefits from focused property-based tests
in isolation. The function returns a typed `Postcode` dataclass instead
of a raw string so the rest of the pipeline can rely on a validated
shape rather than re-parsing strings.

---

## 2026-04-30 — pyproject `package = true` with src/ layout via hatchling
Considered: flat layout (simpler) vs src/ layout (best practice for libraries
because it forces the test runner to import from the installed package, not
from the repo root). Chose src/ layout via hatchling because it eliminates a
class of "tests pass on my machine because they accidentally imported from the
source tree" bugs. CI would catch this either way, but the discipline starts
on day one.

## 2026-04-30 — DuckDB as the Phase 1 analytical store; Postgres added in Phase 3
Considered: Postgres from day one (consistency, but heavy ops cost), DuckDB-only
(delightful local but not multi-reader), SQLite (too feature-poor for spatial).
Chose DuckDB for Phase 1 because hazard ingestion is offline batch work with one
writer and no concurrent reads needed. Postgres becomes mandatory in Phase 3
when the API needs concurrent reads and we want a real client/server boundary.
The DuckDB analytics layer survives that transition (dbt-core + DuckDB adapter
on derived parquet).

## 2026-04-30 — uv for project + dependency management (not pip / poetry / hatch alone)
Considered: pip + venv (familiar but slow and lock-files awkward), poetry
(mature but slower than uv and adds another resolver), Hatch (good but split
between project mgmt and env mgmt), and uv. Chose uv because it resolves and
installs an order of magnitude faster than poetry, has first-class dependency-group
support (PEP 735), and is the de facto standard for new Python projects in
2026. Trade-off: uv is younger and the lock format is its own; we accept this
for the speed and ergonomics. CLAUDE.md hard rule reflects this.

## 2026-04-30 — Both ruff (lint + format) AND black in pre-commit, despite overlap
Considered: ruff-format only (faster), black only (more conservative), both
(overlap risk). Chose both because the prompt mandates it and because they are
configured to identical settings (line length 100, double quotes), so they
should produce the same output. If they fight in practice, drop ruff-format
and keep ruff for lint + black for format. Logged so the future self does not
re-litigate the choice.

## 2026-04-30 — Initial `--cov-fail-under=70` from Phase 0
Considered: lower threshold for Phase 0 (fewer real lines yet) vs the prompt's
70%. Kept 70% because all Phase 0 source modules are placeholders with zero
executable statements (just docstrings or constants), so coverage is trivially
satisfied. Phase 1+ modules will have to clear the bar honestly.

## 2026-04-30 — psycopg2-binary listed in core deps from Phase 0
Considered: defer Postgres deps to Phase 3 (smaller install) vs install up
front. Chose up front to keep `uv sync` reproducible across phases — adding
heavy native deps mid-project frequently causes lockfile churn on Windows
where psycopg2-binary needs vendored OpenSSL.
