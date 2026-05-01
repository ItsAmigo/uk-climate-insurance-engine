# Architecture

A Mermaid diagram replaces the ASCII sketch below at Phase 4
productionisation.

## Phase 1 — local pipeline
```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────┐
│  Source files    │ →  │  DuckDB tables   │ →  │  Postcode → hazard   │
│  (EA, SEPA, NRW, │    │  hazards.flood   │    │  exposure function   │
│   DfI, BGS, ONS) │    │  hazards.subs    │    │  (src/.../hazards/)  │
└──────────────────┘    │  hazards.wind    │    └──────────────────────┘
                        │  geo.postcodes   │
                        └──────────────────┘
```

## Phase 4 — full system (target)
```
                          ┌──────────────────────┐
                          │  Next.js 15 (Vercel) │
                          │  postcode + slider   │
                          └──────────┬───────────┘
                                     │  HTTPS
                                     ▼
                          ┌──────────────────────┐
                          │  FastAPI (Fly.io)    │
                          └──────────┬───────────┘
                                     │
                  ┌──────────────────┴──────────────────┐
                  ▼                                     ▼
        ┌──────────────────┐                  ┌──────────────────┐
        │ Postgres (Supa)  │                  │  DuckDB + dbt    │
        │ live read store  │                  │  analytics layer │
        └──────────────────┘                  └──────────────────┘
```

## Component responsibilities
- **Frontend (Next.js):** postcode search, scenario slider (year + SSP),
  MapLibre GL JS hazard layers, Recharts premium chart, fairness dashboard.
- **API (FastAPI):** stateless, reads from Postgres, returns JSON with hazards,
  premium series, and fairness context.
- **Postgres:** hot read store for postcode → projection lookups.
- **DuckDB + dbt:** offline transformations producing the projection tables
  that get loaded into Postgres.
