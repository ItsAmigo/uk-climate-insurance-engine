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

_(next entry written at the close of Phase 1, including the five hand-validated
sample-postcode comparison against the EA public flood map)_
