# UK Climate-Adjusted Home Insurance Risk Engine

> A web tool that turns a UK postcode into a forward-looking, climate-adjusted home insurance technical premium — and audits the result for fair-value impact under FCA Consumer Duty.

**Live URL:** _coming in Phase 6_

## Architecture
_Mermaid diagram lands in Phase 4 — see [docs/architecture.md](docs/architecture.md)._

## Quickstart

```bash
# 1. Install uv  →  https://docs.astral.sh/uv/
# 2. Clone the repo and enter it
# 3. Install dependencies + pre-commit hooks
make install

# 4. Run the smoke test
make test
```

### Windows note
`make` is not built into Windows. Install it with one of:

```powershell
winget install ezwinports.make    # winget
choco install make                # Chocolatey
scoop install make                # Scoop
```

Or run the underlying commands directly from the [Makefile](Makefile).

## Methodology and decisions
- Methodology: [docs/methodology.md](docs/methodology.md)
- Data sources: [docs/data_sources.md](docs/data_sources.md)
- Decisions log: [docs/decisions.md](docs/decisions.md)
- Phase gates (definition of done): [docs/phase_gates.md](docs/phase_gates.md)
- Consumer Duty stance: [docs/consumer_duty.md](docs/consumer_duty.md)

## Project status
Time-unconstrained, milestone-gated. The project advances only when the gates in
[docs/phase_gates.md](docs/phase_gates.md) pass. There are no week numbers.

## Licence
MIT. Add a `LICENSE` file with the copyright holder before going public.
