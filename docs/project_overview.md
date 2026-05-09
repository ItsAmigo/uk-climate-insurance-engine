# Project Overview — UK Climate-Adjusted Home Insurance Risk Engine

> A one-page explainer in plain English. Hand this to anyone who asks what
> I'm building.

---

## The simple version
I'm building a website where someone in the UK types in their postcode and sees:
1. **What climate risks their home faces today** — the chance of flooding,
   ground movement (cracks from shrinking clay soil), or damage from
   strong winds.
2. **How those risks change between now and 2070** under different
   climate-change futures (mild, moderate, severe).
3. **What that means for their home-insurance premium** — the yearly
   amount they pay.
4. **Whether the changes hit poorer areas harder than richer ones** — a
   fairness check.

## Why this matters now
Insurance companies in the UK are repricing for climate change right now —
floods, storms, and ground shrinkage are causing more claims, so premiums
are moving. The UK financial regulator (the FCA — Financial Conduct
Authority) introduced a rule in 2023 called **Consumer Duty** that says
firms must offer **fair value** and not unfairly disadvantage groups of
customers. Pricing teams at every UK insurer now have to prove their
climate-driven price increases are fair. There is no public tool that
does this end to end. This is one.

## What it actually does, step by step

**Step 1 — Hazard maps.** I gather public maps showing where in the UK
each kind of climate damage is most likely:
- *Flooding* — from the Environment Agency (England), SEPA (Scotland's
  environment agency), Natural Resources Wales, and DfI Rivers (Northern
  Ireland's flood authority)
- *Ground movement* (subsidence — when clay soil shrinks in dry summers
  and cracks foundations) — from the British Geological Survey
- *Strong winds* — from Met Office records

**Step 2 — Risk model.** Using historical insurance-claim patterns, I
train a statistical model that takes the hazards at a property and
predicts the expected yearly damage cost (called "pure premium" in
insurance). I use the same model families that real UK insurance pricing
teams use — generalised linear models (a classical statistical method) and
gradient-boosted trees (a modern machine-learning method).

**Step 3 — Look forward to 2070.** Climate change shifts those hazards.
I take the official UK government climate projections (called UKCP18 —
UK Climate Projections 2018, run by the Met Office) and the international
IPCC scenarios (three "what-if" futures named SSP1-2.6, SSP2-4.5, and
SSP5-8.5 — least to most warming) and project what each property's
premium would be in 2030, 2050, and 2070.

**Step 4 — Fairness check.** I overlay the official UK deprivation index
(IMD — Index of Multiple Deprivation, which scores every neighbourhood
from richest to poorest) and check whether premium increases hit deprived
areas disproportionately. This is the project's distinctive piece —
most student projects stop at step 3.

**Step 5 — Ship it.** Wrap everything in a website where anyone can type
a postcode and see the results on a map, with a slider to switch between
climate scenarios.

## Who I'm building this for
A portfolio piece to apply for graduate jobs at:
- **UK insurance companies and brokers** — Aviva, Allianz, Hiscox, Direct
  Line, Admiral, LV=, Aon, WTW, Marsh, Howden, Lloyd's of London
  syndicates, etc.
- **Consulting firms with insurance practices** — Deloitte, PwC, EY,
  KPMG, Accenture, IBM, Cognizant, TCS, Infosys, Wipro.

The end-state is a live URL I can put on my CV and in cover letters.

## What makes it different from a typical student project
- Uses **the actual vocabulary and methods** real pricing teams use, not
  generic "machine-learning on a Kaggle dataset."
- Includes the **fairness audit** — most projects stop at the model; this
  one carries the regulator's framework all the way through.
- **Honest scope** — I'm a *user* of published climate models and
  damage-curve research, not pretending to have invented them.
- **Validates against industry numbers** — the model's average prediction
  is checked against published UK industry statistics from the
  Association of British Insurers (the ABI). If my model is more than
  20% off their numbers, I have to explain why.

## How it's built (and what each piece does)
- **Python 3.12** — language for the analysis and backend
- **DuckDB / PostgreSQL** — databases that store the maps and lookup tables
- **GeoPandas** — Python library for working with maps and geographic data
- **statsmodels and LightGBM** — for the actual statistical models
- **FastAPI** — turns the model into a web service
- **Next.js + MapLibre** — builds the public website with an interactive map
- **GitHub Actions** — runs automated quality checks on every code change

## How far along I am
The project has 6 phases. Each phase has a checklist; a phase only ends
when every box is ticked.

- ✅ **Phase 0 — Foundation** (done). Repo set up, all tooling working,
  all 13 data sources documented, automated checks running.
- 🔄 **Phase 1 — Hazard ingestion** (just started). Loading the flood
  and subsidence maps and writing the function that turns a postcode
  into a risk profile.
- ⏭ Phases 2–6: build the risk model → project forward → ship the
  website → run the fairness audit → launch.

## The rules I work under
- Every meaningful decision is written down (`docs/decisions.md`) so a
  reviewer can see why I chose what I chose.
- No data file is ever committed to the code repository — data is
  downloaded fresh on each setup.
- Every external dataset's licence is recorded *before* I write code to
  use it (`docs/data_sources.md`).
- I never invent damage formulas — I cite published research.
- All non-trivial work goes on a feature branch and is merged through a
  pull request, with a green automated-test run as the gate.

## Where to read more (in this repo)
- `CLAUDE.md` — the full rulebook for the project
- `docs/phase_gates.md` — the checklist for each phase
- `docs/decisions.md` — log of every meaningful choice
- `docs/data_sources.md` — every external dataset, with licence and gotchas
- `docs/findings.md` — empirical results as they land
- `docs/methodology.md` — the formal write-up
- `docs/consumer_duty.md` — the fairness narrative
