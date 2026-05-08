# Decision log

Every non-trivial choice goes here as a dated entry. One paragraph per decision.

**Format:** `## YYYY-MM-DD — Title` followed by *what was considered*, *what
was chosen*, *why*. New entries at the top.

---

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
