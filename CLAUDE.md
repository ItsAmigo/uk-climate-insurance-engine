# Project: UK Climate-Adjusted Home Insurance Risk Engine

## What this is
A portfolio project to land a UK insurance pricing graduate scheme or consulting
analytics graduate role. End state: a live URL where a user enters a UK postcode
and sees their property's current and projected climate hazard exposure, the
implied insurance premium impact under IPCC scenarios, and a fairness lens on
how those impacts distribute across socioeconomic groups.

## Status: time-unconstrained, milestone-gated
This project is NOT on a fixed schedule. Each phase has a definition-of-done in
docs/phase_gates.md. Phases advance only when their gates pass. The student
chooses pace.

## Target audience for the artifact
Recruiters and hiring managers at:
- Insurance: Aviva, Hastings, Allianz, Brit, Beazley, Hiscox, Direct Line,
  Admiral, LV=, RSA, Aon, WTW, Marsh, Howden, Lloyd's syndicates.
- Consulting: Deloitte, PwC, EY, KPMG, Accenture, IBM, Cognizant, TCS, Infosys,
  Wipro.

## Hard rules (do not violate)
1. NEVER use the word "accuracy" for pricing or loss models. Pricing is not
   classification. Use Gini, lift curves, double lift, deviance, loss ratio.
2. NEVER scrape aggressively. Document every external data source's licence and
   ToS in docs/scraping_ethics.md and docs/data_sources.md before writing a
   scraper. Use respectful delays. Identify the user-agent.
3. ALWAYS log non-trivial decisions in docs/decisions.md as they happen. One
   paragraph each: what was considered, what was chosen, why.
4. ALWAYS validate model outputs against published industry aggregate stats
   (ABI). If divergence > 20%, document why in methodology.md.
5. Notebooks live in notebooks/exploration/ ONLY. Never in src/.
6. Never commit data files, .env, or model artefacts to git.
7. Use industry vocabulary correctly (see glossary below).
8. Climate modelling: WE ARE A CONSUMER OF UKCP18 / IPCC AR6 OUTPUTS. We do not
   run climate models. We do not reproject GCM data ourselves. Stay in the
   consumer role.
9. Damage curves come from PUBLISHED LITERATURE (cite in methodology.md). Do
   not invent or scrape proprietary models.
10. Fairness analysis is mandatory. The Consumer Duty page is the project's
    differentiator and is non-negotiable.
11. Git workflow: every non-trivial change goes on a feature branch and is
    merged via PR against main. Conventional commits: feat:, fix:, docs:,
    refactor:, test:, chore:. Tag releases at phase boundaries (v0.1-foundation,
    v0.2-hazards, etc).
12. After every working session, append to docs/skills_log.md: what new tool /
    concept / library was learned, what problem it solved.

## Tech stack
### Core (used from Phase 1)
- Python 3.12 with uv for dependency management
- DuckDB for local analytical storage (parquet + SQL)
- GeoPandas, Shapely, PyProj, Rasterio for geospatial work
- pytest + Hypothesis for tests (Hypothesis for property-based monotonicity tests)
- ruff + black + mypy + pre-commit for code quality
- GitHub Actions for CI

### Phase 2+
- statsmodels (GLMs), lightgbm (GBMs), shap (explainability)
- MLflow for experiment tracking

### Phase 3+
- Supabase Postgres (when concurrent reads matter)
- dbt-core with DuckDB adapter for the analytics layer

### Phase 4+
- FastAPI + Pydantic v2 for the service
- Next.js 15 + Tailwind + shadcn/ui + MapLibre GL JS + Recharts for the frontend
- Docker + docker-compose for the API
- Vercel (frontend), Fly.io or Railway (API + DB)

### Explicitly NOT used
Kubernetes, Terraform, Airflow, Kafka, Spark, Snowflake, Databricks, Hugging Face,
LangChain, full AWS/GCP/Azure deployments. These are scope creep.

## Phases
- Phase 0: Foundation. Repo scaffolding, tooling, data source documentation.
  ← THIS SESSION
- Phase 1: Hazard ingestion. Load flood, subsidence, windstorm data. Postcode
  → hazard exposure function with tests.
- Phase 2: Current-state risk model. Frequency-severity GLMs and Tweedie GBM
  on current hazard exposure. Validate against ABI aggregates.
- Phase 3: Climate scenarios + forward projections. UKCP18 ingestion. SSP1-2.6,
  SSP2-4.5, SSP5-8.5 hazard projections to 2070. Damage curve application.
- Phase 4: Productionisation. FastAPI service, dockerised. Postgres migration.
  Next.js + MapLibre frontend with postcode search and scenario slider.
- Phase 5: Consumer Duty fairness audit. IMD overlay, demographic loss-ratio
  analysis, fairness dashboard page. THIS IS THE DIFFERENTIATOR — never cut.
- Phase 6: Validation, polish, launch. ABI validation. LinkedIn launch post.
  Loom walkthrough. Application-ready CV one-liner.

## Vocabulary glossary (use correctly)
- **Pure premium**: expected claim cost per unit of exposure.
- **Frequency**: claim count per unit of exposure.
- **Severity**: claim cost per claim.
- **Exposure**: time-at-risk, typically policy-years.
- **Technical price**: the model-derived cost-reflective price.
- **Street price**: the actual market price after commercial loadings.
- **Monotonic constraint**: ML constraint forcing the model output to move only
  one direction with respect to a feature (e.g., risk strictly increases with
  flood-zone level).
- **Gini coefficient**: standard pricing model discrimination metric, 0-1, where
  higher is better.
- **Lift curve**: actual loss vs predicted loss across model deciles.
- **Double lift chart**: comparison of two competing models on the same data.
- **Tweedie**: compound Poisson-Gamma distribution, native for pure premium
  modelling, power parameter between 1 and 2.
- **GLM**: generalised linear model, the actuarial workhorse.
- **GBM**: gradient boosted machine, modern challenger to GLMs.
- **Deviance**: GLM goodness-of-fit measure analogous to residual sum of squares.
- **Loss ratio**: claims paid / premiums earned.
- **IBNR**: Incurred But Not Reported reserves. We do not model this; we know
  the term.
- **Capping (winsorising)**: limiting extreme claim values for stable modelling.
- **SSP**: Shared Socioeconomic Pathway, IPCC AR6 scenario family (replaces RCPs).
- **RCP**: Representative Concentration Pathway, IPCC AR5 scenarios. Some UKCP18
  data uses these. Know the mapping.
- **UKCP18**: UK Climate Projections 2018, Met Office, the canonical UK
  climate scenario dataset.
- **IPCC AR6**: 6th Assessment Report of the Intergovernmental Panel on Climate
  Change.
- **IMD**: Index of Multiple Deprivation. England has its own, Wales/Scotland/NI
  have equivalents. Postcode-area resolution.
- **Consumer Duty**: FCA regulation (PS22/9, FG24/3) requiring fair value and no
  unjustified discrimination in financial products. Pricing teams' top concern
  in 2026.
- **Fair value**: regulatory term — price reasonable relative to benefits
  delivered.
- **Model card**: Google's framework for documenting model intended use,
  limitations, fairness, and training data.
- **SHAP**: SHapley Additive exPlanations, the standard local + global model
  explainability framework.

## Session protocol
At the start of every Claude Code session:
1. Read this file (CLAUDE.md).
2. Read docs/decisions.md (last 5 entries).
3. Read docs/phase_gates.md (current phase's gates).
4. Read the most recent docs/findings.md entry if present.
5. Ask the user which sub-task within the current phase to work on.
6. Never assume the next phase has started. Phases advance only when the user
   says so.

At the END of every session, append one entry to docs/skills_log.md naming the
new tool, library, or concept the user encountered, and the problem it solved.
