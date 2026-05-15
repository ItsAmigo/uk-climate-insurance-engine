# Phase gates — definition of done

This project is milestone-gated, not time-bound. A phase advances only when
EVERY box below is ticked. The student decides pace; the gate decides readiness.

After ticking a phase complete:
- Tag the release: `git tag v0.X-<phase-name>` (e.g., `v0.2-hazards`).
- Append a closing reflection to `docs/findings.md`.
- Append the new tools / concepts learned to `docs/skills_log.md`.

---

## Phase 0 — Foundation
- [x] Repo scaffolded with `src/`, `tests/`, `docs/`, `data/`, `.github/`
- [x] `pyproject.toml` builds; `uv sync` succeeds with all initial deps installed
- [x] Pre-commit hooks installed and passing on a no-op commit
- [x] CI workflow runs on push and on PRs to main (ruff, black, mypy, pytest, coverage)
- [x] CLAUDE.md complete and committed
- [x] `docs/data_sources.md` populated for all 13+ sources
- [x] `docs/phase_gates.md` populated (this file)
- [x] Smoke test passes locally and in CI
- [x] At least 1 entry in `docs/decisions.md`
- [x] First entry in `docs/skills_log.md`
- [x] Tag: `v0.1-foundation`

---

## Phase 1 — Hazard ingestion
- [x] Environment Agency Flood Zone 2 + 3 polygons loaded into DuckDB,
      indexed spatially (R-tree or H3) *(R-tree, 552,811 + 230,729 polygons
      from the EA's ArcGIS Hub Feature Service, ingested 2026-05-09)*
- [ ] SEPA + NRW + DfI Rivers flood polygons loaded into the same schema, harmonised
      *(NRW done 2026-05-15 — `nrw_flood_zone_2` / `nrw_flood_zone_3` tables,
      harmonised via the shared `FloodZone` enum and a `UNION ALL` lookup;
      SEPA + DfI remain)*
- [x] Subsidence proxy ingested (BGS GeoSure-via-WMS or DEFRA Soilscapes —
      decision logged in `docs/decisions.md`) *(decision reversed: BGS Soil
      Parent Material 1km, 241,514 cells loaded 2026-05-09)*
- [x] Postcode → hazard exposure function in `src/climate_insurance/hazards/`,
      returning `{flood_zone, subsidence_class, windstorm_band}` *(via
      `postcode_to_hazards()`; windstorm_band returns None until wind
      ingestion lands)*
- [x] At least 5 sample postcodes hand-validated against the Environment Agency
      public flood map (results table in `docs/findings.md`) *(2026-05-09
      entry, 5 / 5 match the EA service)*
- [x] Property-based tests (Hypothesis): flood-zone score is monotonic in
      stated zone; postcode-level lookup is idempotent *(see
      `tests/test_hazard_properties.py`; 7 passing properties)*
- [x] Methodology section "Hazard data" written *(`docs/methodology.md` §2,
      2026-05-09)*
- [x] At least 3 new entries in `docs/decisions.md` added during the phase
      *(7 entries since 2026-05-08)*
- [x] Test coverage ≥ 70% on the `hazards/` module *(86% as of 2026-05-09)*
- [ ] Tag: `v0.2-hazards`

---

## Phase 2 — Current-state risk model
- [ ] Frequency GLM (Poisson / Negative Binomial) fit on a documented exposure dataset
- [ ] Severity GLM (Gamma) fit
- [ ] Tweedie GBM (LightGBM) fit as challenger, with monotonic constraints
      on hazard features
- [ ] SHAP global + local explanations rendered for the Tweedie GBM
- [ ] Gini, lift curve, and double-lift chart computed and saved as figures
- [ ] Aggregate predicted average loss-cost validated against ABI residential
      property aggregate (within ±20%; deviance documented if exceeded)
- [ ] Model card v1 written (`docs/model_card.md`)
- [ ] Test coverage ≥ 70% on the `models/` module
- [ ] Methodology section "Current-state risk model" written
- [ ] Tag: `v0.3-current-risk`

---

## Phase 3 — Climate scenarios + forward projections
- [ ] CEDA / UKCP18 subset downloaded for SSP1-2.6, SSP2-4.5, SSP5-8.5 to 2070
      (regional 12 km is acceptable for the first cut)
- [ ] Hazard projection layer per (postcode, scenario, year) computed
- [ ] Damage curves applied per claim type (flood, wind, subsidence) — citations
      in `docs/methodology.md`
- [ ] Premium projection for 2030 / 2050 / 2070 produced for at least 1 000 sample postcodes
- [ ] Portfolio-view loss projection on a hypothetical 10 000-policy book complete
- [ ] Postgres migration done; DuckDB still available for the analytics layer
- [ ] dbt-core project initialised with the DuckDB adapter
- [ ] Methodology section "Forward projections" written
- [ ] Test coverage ≥ 70% on the projections module
- [ ] Tag: `v0.4-projections`

---

## Phase 4 — Productionisation
- [ ] FastAPI service exposing `GET /risk?postcode=&scenario=&year=`
- [ ] OpenAPI schema generated and tested
- [ ] Dockerfile builds; docker-compose runs API + Postgres locally
- [ ] Next.js 15 frontend with postcode search, MapLibre GL JS map, scenario
      slider, premium chart (Recharts)
- [ ] Frontend deployed to Vercel; API to Fly.io or Railway
- [ ] End-to-end Playwright smoke test passes against the deployed URL
- [ ] Methodology section "Productionisation" written
- [ ] Test coverage ≥ 70% on the `api/` module
- [ ] Tag: `v0.5-production`

---

## Phase 5 — Consumer Duty fairness audit
- [ ] IMD overlay joined to postcode-level premium projections across all four
      UK nations
- [ ] Loss-ratio change vs IMD decile computed for current and 2050 / 2070 scenarios
- [ ] Fairness dashboard page added to the frontend
- [ ] `docs/consumer_duty.md` fully written, citing FCA PS22/9 and FG24/3
- [ ] At least one specific finding of the form "decile X sees Y% uplift vs
      decile Z's W% under SSP-N by year M"
- [ ] Methodology section "Fairness analysis" written
- [ ] Tag: `v0.6-fairness`

---

## Phase 6 — Validation, polish, launch
- [ ] Full ABI validation memo in `docs/findings.md`
- [ ] LinkedIn launch post drafted (in `docs/`, not committed publicly until ready)
- [ ] Loom walkthrough recorded; link in README
- [ ] CV one-liner crafted (in `docs/`, private until used)
- [ ] All TODOs resolved or moved to GitHub issues
- [ ] All docs cross-linked from README
- [ ] Tag: `v1.0-launch`
