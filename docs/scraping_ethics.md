# Scraping ethics

CLAUDE.md hard rule 2 forbids aggressive scraping. This page documents how we
satisfy that rule in practice.

## Pre-flight checklist (run before writing any fetch code)
1. Is there an official bulk download or API? If yes, USE THAT — never scrape
   what is offered as a download.
2. Read the site's `robots.txt` and Terms of Service. Record both URLs and the
   fetch date in `docs/data_sources.md`.
3. Confirm the licence permits the use case. UK Open Government Licence (OGL)
   is fine; "all rights reserved" + ToS prohibition is a hard stop.
4. Is the data behind a paywall? If yes, do not bypass.
5. Is registration required? Register and use credentials (do not commit them).

## Rate-limiting rules of thumb
- Default request rate: ≤ 1 request per second per host. Slower for small
  public-sector sites.
- Always include a descriptive `User-Agent`:
  `climate-insurance/0.1 (portfolio project; +github.com/<user>/<repo>)`
  Include a contact path so the operator can reach the project owner.
- Respect HTTP 429 / `Retry-After`. Implement exponential back-off.
- Cache aggressively to avoid re-fetching the same resource.

## What we are NOT doing
- No scraping of insurer websites for premiums. Use ABI aggregates only.
- No scraping of property listings (Rightmove, Zoopla). Out of scope.
- No bypassing of paywalls (academic, BGS commercial layers, JBA proprietary).

## Audit log
Every external fetch is logged with: timestamp, URL, response status, bytes
fetched. The log lives in `data/raw/_fetch_audit.jsonl` (gitignored).

_(populate when the first scraper is written, likely Phase 1 if EA bulk
download is preferred over API)_
