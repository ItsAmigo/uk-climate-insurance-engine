# Findings log

Empirical results, sample-postcode validation tables, and one-paragraph
reflections at the end of each phase. Quantitative claims here are
later promoted to `methodology.md` or `model_card.md` once stabilised.

## Format
- `## YYYY-MM-DD — Phase X — Title`
- Tables / figures inline as Markdown; raw data lives in `data/processed/` (not committed).

---

## 2026-05-01 — Phase 0 — Foundation closed
All Phase 0 gates verified and ticked in `docs/phase_gates.md`. `uv sync`
succeeds against the locked dep set; `ruff`, `ruff-format`, `black`, and
`mypy` all pass on the full tree; `pytest` runs 2 smoke tests at 100% line
coverage (well above the 70% floor — note the trivially-satisfied caveat
logged in decisions). Pre-commit hooks installed and exercised against the
fully-staged tree before the initial commit. `docs/data_sources.md` covers
all 13 numbered sources (4 nation-level flood, BGS subsidence, UKCP18, ONSPD,
OS Open, IMD across four nations, flood + wind damage curves, ABI, CCRA3).
Initial commit `da8491d` and tag `v0.1-foundation` recorded on main.

## 2026-05-09 — Phase 1 — Sample-postcode flood-zone hand-validation

Five UK postcodes spanning Zone 1 / Zone 2 / Zone 3, predicted by our
`postcode_to_hazards()` pipeline (ONSPD postcode → coordinate → R-tree
spatial join against EA flood-zone polygons in DuckDB), with the EA's
own classification cross-checked via the official "Check long term flood
risk" service at https://check-long-term-flood-risk.service.gov.uk/postcode.

| Postcode  | Location                                              | Our prediction | EA service says         | Match |
|-----------|-------------------------------------------------------|----------------|-------------------------|-------|
| TA9 3ER   | Highbridge, Somerset Levels (regularly flooded)       | **ZONE_3**     | High risk (rivers/sea)  | ✓     |
| HU4 7BY   | Hull (city below sea level in places)                 | **ZONE_3**     | High risk (rivers/sea)  | ✓     |
| YO1 9SL   | York city centre, immediately west of the river Ouse  | **ZONE_3**     | High risk (rivers/sea)  | ✓     |
| OX14 5JA  | Abingdon, on the river Thames                         | **ZONE_2**     | Medium risk             | ✓     |
| SW1A 1AA  | Buckingham Palace (raised ground above the Thames)    | **ZONE_1**     | Very low risk           | ✓     |

All five predictions match the EA's published classification. (As noted
in `docs/decisions.md`, both our pipeline and the EA web service are
ultimately reading the same Flood Map for Planning polygons published
on the EA ArcGIS Hub — the validation here is therefore confirming that
our ingestion + spatial-index + lookup chain reproduces the canonical
classification, not that we have an independent prediction.)

### Pipeline coverage stats (5,000-postcode random sample)
- 4.6 % of postcodes fall inside Flood Zone 3 (high probability)
- 6.9 % fall inside Flood Zone 2 (medium; superset of Zone 3)
- ≈ 88 % are Zone 1 (low / outside the published flood-risk extents)

These figures align with the EA's own statement that around 5.2 million
English properties are at flood risk from rivers and the sea (~17 % of
all properties); postcodes are denser in cities, many of which are not
on floodplains, so a ~10 % postcode-level hit rate is consistent.

### Initial false-negative (kept as a learning note)
The first five "obvious" test postcodes I picked (SW1A 1AA, YO1 7HH,
TW9 1AB at Kew, M1 1AE, GL1 2HG) all returned ZONE_1 — initially looked
like a model bug. Investigation confirmed the predictions are correct:
postcode centroids of *named-landmark* postcodes (palaces, cathedrals,
gardens) typically sit on the few metres of raised ground that put them
inside the city but outside the floodplain proper. Real flood exposure
shows up when sampling actual residential postcodes (TA9 3ER etc.).

### Pinned data state for this validation
- ONSPD release: February 2026 (1,794,940 active postcodes)
- EA Flood Map for Planning: November 2023 release
  - Zone 2: 552,811 polygons (after one whole-world corrupted polygon
    was filtered by the UK-bbox sanity check in the loader)
  - Zone 3: 230,729 polygons
- BGS Soil Parent Material 1km: V1 2019 release (241,514 cells)
- Database: `data/processed/hazards.duckdb` (~1.5 GB on disk; gitignored)

_(next entry written at the close of Phase 1 once the other 3 nations'
flood data + wind ingestion lands)_
