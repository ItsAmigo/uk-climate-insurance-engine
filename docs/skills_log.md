# Skills log

A running tally of new tools / libraries / concepts encountered each session
and the problem each one solved. Append to this at the end of every session.

## Format
**YYYY-MM-DD — Phase X — Topic**
- What it is
- What problem it solved
- Where to learn more

---

## 2026-04-30 — Phase 0 — `uv`
- Astral's drop-in replacement for pip / venv / pip-tools / poetry — handles
  project init, dependency resolution, lock files, and venv creation.
- Solved: deciding the dependency-management tool for the project. uv handled
  it all without juggling three CLIs.
- Reference: https://docs.astral.sh/uv/

## 2026-04-30 — Phase 0 — Pre-commit framework + ruff + black + mypy stack
- Pre-commit runs lint / format / type checks before each `git commit`,
  catching style and typing regressions at the moment they happen.
- Solved: enforcing the CLAUDE.md hard rule that no untyped code lands on
  main, without relying on memory.
- Reference: https://pre-commit.com/

## 2026-04-30 — Phase 0 — Python `src/` layout vs flat layout
- The src/ layout makes pytest / mypy import from the *installed* package, not
  from the working directory, eliminating a class of "passes locally, fails in
  CI" bugs.
- Solved: choosing a project layout that scales beyond Phase 0.
- Reference: PyPA packaging guide on src vs flat layouts.

## 2026-05-01 — Phase 0 — Phase-gate verification workflow
- The discipline of running each tool the gate names (`uv sync`, `ruff`,
  `ruff format --check`, `black --check`, `mypy`, `pytest`, `pre-commit run`)
  against a fully-staged tree before tagging — instead of trusting that
  scaffolded config implies passing config.
- Solved: catching the failure-mode where pre-commit's `--all-files` silently
  skips because nothing is git-tracked yet; staging first then re-running
  exercises every hook against real content.
- Reference: pre-commit docs §"Filtering files with types" + git's two-step
  index model.

## 2026-05-15 — Phase 1 — OGC WFS GetFeature pagination (vs ArcGIS REST)
- DataMapWales serves NRW data via a standards-compliant GeoServer WFS
  (`service=WFS&version=2.0.0&request=GetFeature&typeNames=...`), paginated
  with `startIndex` + `count`, with server-side reprojection via `srsName`.
- Solved: pulling Welsh Flood Map for Planning polygons without having to
  client-side reproject from BNG (EPSG:27700) — the WFS honours
  `srsName=EPSG:4326`, so the GeoJSON response arrives in WGS84 already
  aligned with our ONSPD pipeline. Notably simpler than the EA's
  ArcGIS REST `query?resultOffset=...&resultRecordCount=...` pattern.
- Reference: https://docs.geoserver.org/main/en/user/services/wfs/reference.html#getfeature

## 2026-05-15 — Phase 1 — Catalog-aware UNION ALL lookups in DuckDB
- DuckDB's `information_schema.tables` lets a single SQL function check
  which optional tables exist at call time and stitch only those into a
  `UNION ALL`. Used here to make `lookup_flood_zone` query EA tables on
  one machine and EA + NRW tables on another without breaking either.
- Solved: the awkward fork between "production DB" (all four nations
  loaded) and test fixtures (typically only one nation), without
  branching per environment in the application code.
- Reference: https://duckdb.org/docs/sql/information_schema

_(append one entry per session)_
