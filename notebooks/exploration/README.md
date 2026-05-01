# Exploration notebooks

**Rule:** Notebooks live HERE only. Never under `src/`.

Notebooks are for exploration, sanity checks, and figure prototyping. Anything
production-grade graduates to `src/climate_insurance/` with tests.

## Naming convention
`YYYY-MM-DD-author-topic.ipynb`

Example: `2026-05-12-tanmay-ea-flood-zone-3-overlap.ipynb`

## What goes here
- Quick data peeks
- Plot prototyping
- Hand-validation against published maps
- One-off exploratory analyses

## What does NOT go here
- Anything imported by code in `src/`
- Anything required for tests to pass
- Anything that hardcodes credentials (use `.env` + `climate_insurance.config`)

## Running
```bash
make notebook    # uv run jupyter lab
```
