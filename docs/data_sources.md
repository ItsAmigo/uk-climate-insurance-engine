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
- **Canonical source:** Environment Agency's own ArcGIS Hub Feature Service:
  `https://services1.arcgis.com/JZM7qJpmv7vJ0Hzx/arcgis/rest/services/Flood_Map_for_Planning/FeatureServer`
  Item id `510b860c094046f7813d86811a646543`. Hub item URL:
  https://www.arcgis.com/home/item.html?id=510b860c094046f7813d86811a646543
  The Defra Data Services Platform UI at
  https://environment.data.gov.uk/dataset/04532375-a198-476e-985e-0579a0a11b47
  surfaces the same data but is JavaScript-only — direct downloads must come
  from the Feature Service above.
- **Extract:** Flood Zone 2 polygons (~553k features) and Flood Zone 3 polygons
  (~231k features). Layer indices on the FeatureServer: `1` = Zone 3,
  `2` = Zone 2. We **exclude** the climate-change overlay (CLAUDE.md hard
  rule 8 — we apply UKCP18 ourselves in Phase 3).
- **License:** Open Government Licence v3.0 (OGL). Attribution required:
  *"Contains Environment Agency information © Environment Agency and database
  right. Some features based on digital spatial data from the Centre for
  Ecology & Hydrology, © NERC (CEH). © Crown Copyright and Database Rights
  2024 OS AC0000807064."*
- **Source CRS:** British National Grid (EPSG:27700). We request `outSR=4326`
  on the Feature Service query so the GeoJSON arrives already in WGS84
  (lat/lon) — same coordinate system as ONSPD postcode coords. No
  reprojection needed at ingest.
- **Registration:** None.
- **Refresh:** `make ingest-ea-flood` — paginates through the Feature Service
  at the API limit of 2000 records per call, sleeps 0.2s between calls.
  Takes ~25–30 min on a typical home connection. Sets `outSR=4326`.
- **Currently pinned release:** Flood Zones 2 and 3 published November 2023
  (the EA's most recent revision as of May 2026). 553,158 Zone 2 polygons
  and 231,054 Zone 3 polygons.
- **Gotchas:**
  - Combined GeoJSON download is ~1–2 GB — do NOT commit. Place in
    `data/raw/ea_flood_zones/` (gitignored).
  - Zone 3 is the higher-probability zone (1-in-100 annual chance from
    rivers / 1-in-200 from sea). Zone 2 is 1-in-1,000 to 1-in-100.
  - England only. Wales / Scotland / NI need separate sources below.
  - The Feature Service does not support a single bulk-download URL — full
    extraction must paginate.

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

### 5. British Geological Survey — Soil Parent Material 1km (subsidence proxy)
- **URL:** https://www.bgs.ac.uk/datasets/soil-parent-material-model/
  Direct GeoPackage download: https://www.bgs.ac.uk/?wpdmdl=49018
  ESRI shapefile alternative: https://www.bgs.ac.uk/?wpdmdl=72034
  User guide: https://www.bgs.ac.uk/?wpdmdl=12059
- **Extract:** 1 km grid cells covering Great Britain (241,514 cells), with
  six soil-parent-material attributes per cell. We use `SOIL_GROUP`
  (HEAVY/MEDIUM/LIGHT shorthand for clay/silt/sand dominance) as the
  subsidence-risk proxy via the dominant-class rule logged in
  `decisions.md` 2026-05-09. Other attributes (`SOIL_TEX`, `PMM_GRAIN`,
  `CARB_CNTNT`, `SOIL_DEPTH`, `ESB_DESC`) are loaded but unused at this
  stage — useful for future refinement.
- **License:** Open Government Licence v3.0 with required attribution:
  *"Contains British Geological Survey materials © UKRI 2019. All rights
  reserved."* The 1 km free release is the canonical OGL-licensed product.
  The 1:50,000 high-res version is a paid commercial licence and is
  out of scope for this project.
- **Source CRS:** OSGB36 / British National Grid (EPSG:27700). The loader
  reprojects to WGS84 (EPSG:4326) at ingest using DuckDB-spatial's
  `ST_Transform` + `ST_FlipCoordinates` so geometries align with the rest
  of the pipeline (which uses ST_Point(lon, lat)).
- **Registration:** None for the free 1 km dataset.
- **Refresh:** `make ingest-bgs-spm` — single-shot HTTPS download of the
  ZIP (~166 MB), unzips to a ~919 MB GeoPackage, ingests in ~2 minutes.
- **Currently pinned release:** Soil Parent Material V1 1km, dated 2019
  (BGS has not published a newer version of the free release as of
  May 2026). 241,514 grid cells loaded.
- **Coverage gap:** Northern Ireland is not in the BGS SPM coverage. The
  lookup function falls back to `SubsidenceClass.MEDIUM` for any
  coordinate outside the loaded grid.
- **Gotchas:**
  - The GeoPackage has six layers, all with *identical* feature schema —
    they only differ in which attribute they're named after. Load any
    single layer; we use 'Soil Texture' canonically.
  - GeoPackage is 919 MB on disk — do NOT commit. Place in
    `data/raw/bgs_spm/` (gitignored).

### 5b. (rejected — see decisions.md 2026-05-09 reversal) DEFRA Soilscapes
- Rejected after a closer licence read showed Soilscapes is Cranfield-owned
  and explicitly *"not intended for supporting commercial activities"*.
  The 2026-05-08 decision-log entry that called it "fully open under OGL"
  was incorrect.

### 5c. (alternative for premium reviewers) BGS GeoSure (paid)
- The BGS GeoSure dataset is the gold-standard UK subsidence dataset
  (clay shrink-swell + landslide + collapsible ground + soluble rocks +
  running sand) but is a paid licensable product. Free viewing via the
  OpenGeoscience WMS is permitted but redistribution of the underlying
  ratings is not. Out of scope for an open portfolio repo; a follow-up
  study with a BGS data licence could swap GeoSure in behind the same
  `subsidence_class` interface.

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
  - Column names changed in 2024 to `<year>cd`-suffixed form
    (`lsoa11cd`, `lad25cd`, `ctry25cd`, etc). The pre-2024 names
    (`lsoa11`, `oslaua`, `ctry`) are gone — anything you copy from older
    notebooks needs updating.
- **Currently pinned release:** ONSPD February 2026 (`ONSPD_FEB_2026.zip`,
  235 MB, ArcGIS Hub item id `3080229224424c9cb53c0b48f5a64d27`).
  Loaded **1,794,940** active UK postcodes on 2026-05-08.
- **How to refresh:** `make ingest-onspd URL=https://www.arcgis.com/sharing/rest/content/items/<NEW_ITEM_ID>/data`
  — find the item ID by visiting the new release's geoportal page and
  reading the URL.

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
