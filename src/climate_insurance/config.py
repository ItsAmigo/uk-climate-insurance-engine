"""Project configuration: env vars, paths, DB connection.

Centralises file paths and environment variables so downstream modules never
construct paths inline. Phase 0 keeps this minimal; new keys are added per
phase as they become needed (Postgres in Phase 3, API keys in Phase 4).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_RAW: Path = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED: Path = PROJECT_ROOT / "data" / "processed"

DUCKDB_PATH: Path = Path(os.getenv("DUCKDB_PATH", str(PROJECT_ROOT / "climate_insurance.duckdb")))
DATABASE_URL: str | None = os.getenv("DATABASE_URL")

CEDA_USERNAME: str | None = os.getenv("CEDA_USERNAME")
CEDA_PASSWORD: str | None = os.getenv("CEDA_PASSWORD")

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
