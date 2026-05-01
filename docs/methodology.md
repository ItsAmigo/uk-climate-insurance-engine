# Methodology

This document is the canonical record of analytical choices in the Climate
Insurance Engine. Each section is filled out as the corresponding phase is
completed. Every numerical claim cites a source.

## 1. Scope and intended use
_(populate at the close of Phase 0: confirm scope statement and out-of-scope list)_

## 2. Hazard data
_(Phase 1 — flood, subsidence, windstorm sources, harmonisation across UK nations,
postcode-level aggregation rule, R-tree / H3 spatial indexing choice)_

## 3. Current-state risk model
_(Phase 2 — exposure data choice, frequency-severity vs Tweedie, monotonic
constraints on hazard features, validation strategy, ABI sanity-check rule)_

## 4. Climate scenarios and forward projections
_(Phase 3 — UKCP18 subset chosen, SSP-to-RCP mapping, downscaling approach,
damage-curve choices with citations)_

## 5. Productionisation
_(Phase 4 — API contract, caching strategy, frontend interactions, deployment
topology, rollback plan)_

## 6. Fairness analysis
_(Phase 5 — IMD harmonisation across the four nations, fairness metric definitions,
Consumer Duty linkage)_

## 7. Validation against industry aggregates
_(Phase 2 + 6 — ABI comparison rule: divergence > 20% triggers a documented
explanation per CLAUDE.md hard rule 4)_

## 8. Limitations
_(Phase 6 — known biases, data gaps, model assumptions, what we are NOT modelling)_

## 9. Glossary cross-reference
See [CLAUDE.md](../CLAUDE.md) "Vocabulary glossary" section.
