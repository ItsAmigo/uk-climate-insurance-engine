# Model Card — Climate-Adjusted Premium Engine

> Format reference: Mitchell et al. (2019), "Model Cards for Model Reporting."
> Updated at the close of each phase. Sections marked _(TBD)_ are placeholders.

## Model details
- **Model name:** Climate-Adjusted Home Insurance Premium Engine
- **Owner:** _(student name)_, MSc Data Analytics, Queen's University Belfast
- **Version:** 0.1.0 (Foundation phase)
- **Type:** _(TBD — frequency-severity GLM + Tweedie GBM challenger; final ensemble TBD in Phase 2)_
- **License:** MIT (code). See `docs/data_sources.md` for data licences.
- **Citation:** _(TBD — final form post-launch)_

## Intended use
- **Primary purpose:** Estimate current and forward-looking (2030 / 2050 / 2070)
  climate-adjusted technical premiums for UK residential properties at postcode
  resolution under three IPCC SSP scenarios.
- **Primary users:** Recruiters and hiring managers evaluating the candidate's
  portfolio. Not a commercial product.
- **Out-of-scope uses:** Underwriting decisions, mortgage conditioning,
  individual property valuation, legally consequential decisions of any kind.
  Educational and illustrative only.

## Factors
- **Geographic scope:** UK (England, Scotland, Wales, Northern Ireland).
- **Hazards modelled:** Flood (fluvial + coastal), subsidence proxy, windstorm.
  _(TBD — final list confirmed at Phase 3)_
- **Subgroup analysis:** IMD decile (per nation), urban–rural classification.

## Metrics
- **Primary:** Gini coefficient on a held-out sample. Lift curve. Double-lift
  vs GLM baseline.
- **Aggregate validation:** Average modelled loss cost vs ABI residential
  property aggregate (target ±20%; deviance documented if exceeded).
- _(TBD — full table at Phase 2)_

## Evaluation data
_(TBD — Phase 2)_

## Training data
_(TBD — Phase 2)_

## Quantitative analyses
_(TBD — Phase 2 / 3)_

## Ethical considerations
- **Fairness:** A Consumer Duty fairness audit is mandatory at Phase 5. We
  explicitly check whether modelled premium uplift falls disproportionately on
  lower-IMD postcodes and document the result in `docs/consumer_duty.md`.
- **Discrimination:** No protected-characteristic features used. IMD is an
  area-level deprivation proxy used for retrospective fairness analysis, not
  as a model input.
- **Data minimisation:** No personal data is processed. Inputs are
  postcode-area aggregates only.

## Caveats and recommendations
- We are **consumers** of UKCP18 / IPCC AR6 outputs, not climate modellers.
- Damage curves come from published literature; results inherit the calibration
  regimes of those source papers.
- Forward projections beyond 2070 are not produced.
- This is a portfolio artefact, not a regulated model. Do not deploy.
