# Skills log

A running tally of new tools / libraries / concepts encountered each session
and the problem each one solved. Append to this at the end of every session.

## Format
**YYYY-MM-DD — Phase X — Topic**
- What it is
- What problem it solved
- Where to learn more

---

## 2026-04-30 — Phase 0 — `uv`
- Astral's drop-in replacement for pip / venv / pip-tools / poetry — handles
  project init, dependency resolution, lock files, and venv creation.
- Solved: deciding the dependency-management tool for the project. uv handled
  it all without juggling three CLIs.
- Reference: https://docs.astral.sh/uv/

## 2026-04-30 — Phase 0 — Pre-commit framework + ruff + black + mypy stack
- Pre-commit runs lint / format / type checks before each `git commit`,
  catching style and typing regressions at the moment they happen.
- Solved: enforcing the CLAUDE.md hard rule that no untyped code lands on
  main, without relying on memory.
- Reference: https://pre-commit.com/

## 2026-04-30 — Phase 0 — Python `src/` layout vs flat layout
- The src/ layout makes pytest / mypy import from the *installed* package, not
  from the working directory, eliminating a class of "passes locally, fails in
  CI" bugs.
- Solved: choosing a project layout that scales beyond Phase 0.
- Reference: PyPA packaging guide on src vs flat layouts.

_(append one entry per session)_
