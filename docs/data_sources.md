# Data sources — acquisition checklist

This file is the canonical list of external data the project consumes. Each
source must be documented HERE before any code is written to ingest it. Do not
auto-download until license terms and registration requirements are recorded.

## How to use this file
For each source we record:
- **URL** — landing page; verify in a browser before download in case URLs have moved
- **Extract** — exactly which datasets / layers / fields we pull
- **License** — the terms we comply with (and the attribution string)
- **Registration** — whether free registration is required
- **Gotchas** — known traps, file size, format quirks, refresh cadence

URLs below are starting points. Some (especially deep-linked dataset records)
move regularly. If a URL is dead, search `data.gov.uk` first, then the
publishing body's data portal. Update the URL in the same PR as the
ingestion code.

---

## Hazard layers

### 1. Environment Agency — Flood Map for Planning (England)
- **URL:** https://environment.data.gov.uk/  (search "Flood Map for Planning Rivers and Sea")
  Also published via DEFRA Data Services Platform: https://environment.data.gov.uk/portalstg/
- **Extract:** Flood Zones 2 and 3 polygons (rivers and sea, ignoring
  climate-change overlay — we apply UKCP18 ourselves in Phase 3).
  Source data is published as Shapefile / GeoPackage / WFS API.
- **License:** Open Government Licence v3.0 (OGL). Free for any use with
  attribution: *"Contains Environment Agency information © Environment Agency
  and database right"*.
- **Registration:** None.
- **Gotchas:**
  - File size > 100 MB — do NOT commit. Place in `data/raw/ea_flood_zones/`.
  - Zone 3 is the higher-probability zone (1-in-100 fluvial / 1-in-200 tidal).
    Zone 2 is 1-in-1 000.
  - England only. Wales / Scotland / NI need separate sources below.
  - Updated multiple times a year — record the download date in `decisions.md`.

### 2. SEPA — Flood Maps (Scotland)
- **URL:** https://www.sepa.org.uk/environment/water/flooding/flood-maps/
- **Extract:** Fluvial / coastal / surface water flood-extent polygons.
- **License:** Open Government Licence v3.0 with SEPA attribution:
  *"© Scottish Environment Protection Agency"*.
- **Registration:** None.
- **Gotchas:**
  - Scottish flood-zone semantics differ from EA — record the harmonisation
    decision in `methodology.md`.
  - SEPA also publishes climate-change uplift overlays. Do NOT use them; we
    apply UKCP18 directly to keep the climate layer single-sourced.

### 3. Natural Resources Wales — Flood Map for Planning (Wales)
- **URL:** https://datamap.gov.wales/  (search "Flood Map for Planning")
  Body root: https://naturalresources.wales/
- **Extract:** Flood Zones 2 and 3 polygons for Wales.
- **License:** Open Government Licence v3.0 with NRW / Cyfoeth Naturiol Cymru
  attribution.
- **Registration:** None.
- **Gotchas:** Bilingual metadata (English / Welsh). Use English layers unless
  rendering for a Welsh-language audience.

### 4. DfI Rivers — Strategic Flood Map (Northern Ireland)
- **URL:** https://www.infrastructure-ni.gov.uk/  (search "Strategic Flood Map
  Northern Ireland"). Also published via OpenDataNI: https://www.opendatani.gov.uk/
- **Extract:** Strategic flood-map fluvial + coastal extents.
- **License:** Open Government Licence with DfI attribution.
- **Registration:** None.
- **Gotchas:** NI data is the smallest of the four nations and sometimes
  lower-resolution. Document any spatial mismatch with the others in
  `decisions.md`.

### 5. British Geological Survey — GeoSure (subsidence)
- **URL:** https://www.bgs.ac.uk/datasets/geosure/
  WMS / WFS endpoints: https://ogc.bgs.ac.uk/
- **Extract:** GeoSure susceptibility ratings — primarily shrink–swell clays
  (the dominant subsidence driver in England). Other layers: landslides,
  soluble rocks, compressible ground, collapsible deposits, running sand.
- **License:** **NOT fully open.** GeoSure is a licensable product.
  - **OpenGeoscience** offers free *viewing* via a WMS but does NOT permit
    redistribution of the underlying ratings.
  - For commercial / redistributable use BGS requires a paid licence.
  - For this portfolio we either (a) use the OpenGeoscience WMS for
    visualisation only and aggregate categorical risk to postcode without
    redistributing the underlying raster, or (b) substitute Soilscapes (DEFRA,
    OGL) as a coarser open proxy.
  - **Decision required** — log in `decisions.md` before ingestion.
- **Registration:** Yes for download; no for OpenGeoscience WMS view.
- **Gotchas:** Do not commit any GeoSure layer to git regardless of route.
  Re-derive on every clone.

### 6. Met Office UKCP18 via CEDA Archive
- **URL:** https://archive.ceda.ac.uk/
  Project site: https://www.metoffice.gov.uk/research/approach/collaboration/ukcp/
- **Extract:**
  - UKCP18 Local (2.2 km) projections — daily / hourly precipitation,
    temperature, wind across SSP-aligned scenarios.
  - UKCP18 Regional (12 km) — coarser but cheaper to handle for the first pass.
  - We are **consumers**, not modellers. Download published projections; do
    not regrid or rerun (CLAUDE.md hard rule 8).
- **License:** Open Government Licence v3.0 with required attribution:
  *"Contains Met Office data licensed under OGL. UKCP18 data, Met Office"*.
- **Registration:** **Required.** Free. Sign up at the CEDA archive then
  accept the UKCP18 terms.
- **Gotchas:**
  - Files are massive (TB-scale for the full ensemble). Phase 3 pulls a
    curated subset only.
  - NetCDF format — add `xarray` and `netCDF4` in Phase 3.
  - SSP → RCP mapping per IPCC AR6 Cross-Chapter Box: SSP5-8.5 ≈ RCP8.5,
    SSP2-4.5 ≈ RCP4.5, SSP1-2.6 ≈ RCP2.6. Document the mapping in
    `methodology.md` before using projections.
  - Authenticated downloads — store credentials as `CEDA_USERNAME` /
    `CEDA_PASSWORD` in `.env`.

---

## Geography & exposure

### 7. ONS Postcode Directory (ONSPD)
- **URL:** https://geoportal.statistics.gov.uk/  (search "ONS Postcode
  Directory" — pick the latest quarterly release).
- **Extract:** Full UK postcode → easting / northing / lat-long, LSOA, MSOA,
  LAD, country code mapping.
- **License:** Open Government Licence v3.0 with ONS / OS attribution.
  Contains OS data © Crown copyright and database right; Royal Mail data ©
  Royal Mail copyright and database right.
- **Registration:** None.
- **Gotchas:**
  - Updated quarterly. Pin a release in `decisions.md`.
  - More than 2 M postcodes — load into DuckDB, never pandas-only.
  - Includes terminated postcodes — filter on `doterm IS NULL` for currently
    active ones.

### 8. OS Open data — Code-Point Open and OS OpenData
- **URL:** https://www.ordnancesurvey.co.uk/products/code-point-open
  Data Hub: https://osdatahub.os.uk/
- **Extract:** Postcode-unit centroids (Code-Point Open). Postcode-area /
  postcode-sector polygons are not directly published — derive by dissolving
  centroids on the sector code or use a third-party shapefile (cite source).
- **License:** OS OpenData licence (OGL-compatible) with required attribution.
- **Registration:** None for OpenData; an OS Data Hub account makes download
  easier.
- **Gotchas:** Postcodes are *points*, not areas. Decide the spatial
  abstraction (centroid lookup vs Voronoi vs dissolved sector) and log in
  `decisions.md`.

---

## Socioeconomic context (for Consumer Duty fairness lens)

### 9. English Indices of Multiple Deprivation 2019 (and equivalents)
- **URL:**
  - England — https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019
  - Wales — https://gov.wales/welsh-index-multiple-deprivation
  - Scotland — https://simd.scot/  (Scottish Index of Multiple Deprivation 2020)
  - Northern Ireland — https://www.nisra.gov.uk/  (search "Northern Ireland
    Multiple Deprivation Measure 2017")
- **Extract:** LSOA-level (England) / Data Zone-level (Scotland) / equivalent
  IMD scores, ranks, deciles, plus domain breakdowns (income, employment,
  health, education, etc.).
- **License:** Open Government Licence v3.0 across all four.
- **Registration:** None.
- **Gotchas:**
  - **The four nations' IMDs are NOT directly comparable** — different
    methodologies and reference years. Document the harmonisation approach in
    `methodology.md`.
  - IMD is not a measure of individual income; it is an area-level deprivation
    score. Phrase findings in `consumer_duty.md` carefully to avoid implying
    individual-level causation.
  - Joining IMD to postcodes: ONSPD provides postcode → LSOA mapping.

---

## Damage / vulnerability functions (use published curves, do not invent)

### 10. Published flood depth–damage curves
- **JBA Risk Management** — depth–damage curves frequently cited in UK industry.
  Some published in academic papers; the full library is proprietary. Use only
  *published* functions and cite the paper.
- **Penning-Rowsell Multi-Coloured Manual (MCM)** — the de-facto UK reference
  for residential-property flood damage. Latest editions are paywalled; older
  editions and summary tables appear in academic literature. Cite paper +
  edition.
- **EU Joint Research Centre — global flood depth–damage functions** (Huizinga
  et al. 2017, JRC publication, free PDF). Use the country-specific UK curves
  and the residential building category. Search "JRC Huizinga 2017 global
  flood depth damage" for the report.
- **License posture:** cite, do not redistribute the curves verbatim. Reproduce
  as code with explicit citation and edition.
- **Gotchas:** Curves vary by building type, content vs structure, return
  period. Pick one consistent source per claim type and document the choice.
  Phase 3 task.

### 11. Published wind damage curves
- **References to evaluate (Phase 3):**
  - Klawa & Ulbrich (2003) — windstorm loss index used widely in EU papers.
  - Heneka & Ruck (2008) — German residential wind damage function (translates
    to UK via building-stock similarity).
  - Roberts et al. — UK-specific Lothar / Klaus / Daria-class storm reanalyses.
- **License posture:** cite, do not redistribute. Reproduce as code.
- **Gotchas:** Wind damage is highly non-linear with gust speed. Small
  calibration differences cause large premium swings. Validate against ABI
  windstorm ratios.

---

## Validation references

### 12. ABI — UK home insurance aggregate stats
- **URL:** https://www.abi.org.uk/data-and-resources/  (search "Property
  statistics" and "Climate Risk").
- **Extract:** Aggregate average premium, claim frequency, average claim cost
  (residential buildings + contents), windstorm event statistics, flood claim
  totals.
- **License:** Free public stats are usable as a validation reference with
  attribution. No redistribution of underlying member data.
- **Registration:** None for public stats.
- **Gotchas:** ABI numbers are aggregate. Do NOT cherry-pick. Use as a sanity
  check, the ±20% rule from CLAUDE.md hard rule 4.

### 13. DEFRA — UK Climate Change Risk Assessment (CCRA3) data
- **URL:** https://www.gov.uk/government/publications/uk-climate-change-risk-assessment-2022
  (CCRA3, technical reports + supporting data).
- **Extract:** National-scale risk magnitudes for flooding, overheating,
  subsidence, plus methodology references for residential property impacts.
- **License:** Open Government Licence v3.0.
- **Registration:** None.
- **Gotchas:** CCRA is qualitative / semi-quantitative at national level.
  Treat as context, not a substitute for the postcode-level pipeline.

---

## Reference reading (linked here so the readiness checklist is one-stop)

### Pricing & GLM background
- **IFoA — *A Practical Guide to Generalised Linear Models in General
  Insurance Pricing*** (Pricing and Risk Working Party). Free PDF on
  https://www.actuaries.org.uk/  — search "GLMs in general insurance pricing".
- **Wüthrich, M. — *Statistical Foundations of Actuarial Learning and its
  Applications*** (Springer, open access).
  https://link.springer.com/book/10.1007/978-3-031-12409-9  — chapters 1–4
  cover the GLM / GBM frequency–severity framework.

### Climate scenario interpretation
- **IPCC AR6 WG I Atlas** — https://interactive-atlas.ipcc.ch/
- **UKCP18 Science Overview** — https://www.metoffice.gov.uk/research/approach/collaboration/ukcp/
