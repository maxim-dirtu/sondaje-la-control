---
id: T-020
title: Data preparation pipeline
status: in-progress
phase: 2
depends_on: [T-002, T-003]
owner: copilot-agent-T-020
branch: task/T-020-data-prep-pipeline
methodology: [M-1.1, M-1.2, M-1.3, M-1.4, M-1.5, M-1.6]
created: 2026-11-22
updated: 2026-11-27
---

## Goal
One function call turns the canonical CSVs into a tidy, analysis-ready table:
one row per (poll, entity) with `s`, `r`, days before the election, recency
weight, `n`, target scope, and house.

## Context
All metrics build on this table. Develop it against **synthetic fixtures**;
real data is not required to start.

## Scope
**In:**
- `src/sondaje/prep.py` (or similar) and its tests
- A single config object holding the tunable parameters, with defaults taken
  from the METHODOLOGY table
- **Shared file allowed:** `docs/METHODOLOGY.md` section M-1, for
  clarifications, and to resolve the open specification issues OI-1…OI-5

**Out:**
- Any metric calculation.

## Acceptance criteria
- [ ] OI-1…OI-5 in METHODOLOGY are resolved: the sections are updated and the
      rows are removed from the open-issues table. The choices are in the Log.
- [ ] Every M-1.x rule has at least one unit test with hand-computed expected
      values.
- [ ] Docstrings cite the M-ID they implement.
- [ ] Withdrawals and alliance mappings are applied, and each adjustment is
      logged.
- [ ] Ruff and pytest pass.

## Follow-ups

## Log

## Outcome
