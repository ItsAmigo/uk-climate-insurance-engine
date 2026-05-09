# Climate Insurance Engine — developer shortcuts.
# All recipes use `uv run` so the project venv is always used.
# On Windows, run via Git Bash, WSL, or install make:  winget install ezwinports.make
.PHONY: install test lint fmt notebook duckdb clean help ingest-onspd ingest-ea-flood ingest-bgs-spm

help:
	@echo "Targets:"
	@echo "  install   uv sync + pre-commit install"
	@echo "  test      pytest with coverage"
	@echo "  lint      ruff check, black --check, mypy"
	@echo "  fmt       ruff --fix, black"
	@echo "  notebook  uv run jupyter lab"
	@echo "  duckdb    open the project DuckDB file in the duckdb CLI"
	@echo "  ingest-onspd   download + ingest the latest ONSPD (set ONSPD_URL or pass URL=...)"
	@echo "  clean     remove caches and coverage artefacts"

install:
	uv sync
	uv run pre-commit install
	@echo "Done. Run 'uv run playwright install' if you need browser drivers (Phase 4+)."

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run black --check .
	uv run mypy src/

fmt:
	uv run ruff check --fix .
	uv run black .

notebook:
	uv run jupyter lab

duckdb:
	@echo "Note: requires the DuckDB CLI on PATH (https://duckdb.org/docs/installation/)."
	duckdb climate_insurance.duckdb

# Usage: make ingest-onspd URL=https://www.arcgis.com/.../<ITEM_ID>/data
# Or pre-set ONSPD_URL in .env. Find the ITEM_ID at geoportal.statistics.gov.uk
# (search "ONS Postcode Directory", click latest release).
ingest-onspd:
	uv run python -m scripts.fetch_onspd $(if $(URL),--url $(URL),)

# Download EA Flood Zones 2 and 3 (England) and ingest to DuckDB.
# Takes 25-30 min on a typical home connection (paginated through ArcGIS).
# Pass SKIP=1 to reuse an existing GeoJSON in data/raw/ea_flood_zones/.
ingest-ea-flood:
	uv run python -m scripts.fetch_ea_flood_zones $(if $(SKIP),--skip-download,)

# Download BGS Soil Parent Material 1km GeoPackage and ingest. ~2 min.
# Pass SKIP=1 to reuse an existing ZIP in data/raw/bgs_spm/.
ingest-bgs-spm:
	uv run python -m scripts.fetch_bgs_spm $(if $(SKIP),--skip-download,)

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov coverage.xml .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
