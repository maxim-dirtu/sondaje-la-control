---
id: T-012
title: "Polls: AtlasIntel (MVP elections)"
status: in-progress
phase: 1
depends_on: [T-011]
owner: Copilot (contributor agent)
branch: task/T-012-polls-atlasintel
methodology: [M-1.1, M-1.3, M-1.4, M-1.5, M-1.7, M-5.3]
created: 2026-11-22
updated: 2026-11-27
---

## Goal
Every published voting-intention poll by **AtlasIntel** (`atlasintel`) for the 3
MVP elections, captured as a **full topline**, with transparency metadata and
provenance.

Collection windows (fieldwork end date):
- `parl-2024-cd`: 120 days before 2024-12-01
- `pres-2025-r1`: 120 days before 2025-05-04
- `pres-2025-r2`: head-to-head polls with fieldwork between 2025-05-05 and
  2025-05-17. Pre-R1 hypothetical pairings are not R2 polls (R-84).

## Context
- Follow `docs/POLL_INGESTION.md` (from T-011) step by step.
- [ADR-0012](../docs/decisions/0012-mvp-pollsters.md) and its report
  [pollster-selection.md](../docs/reports/pollster-selection.md) give the
  rules, evidence and publication formats for this house. Read its §5.
- Expected volume: about 9 polls (1 excluded from metrics by M-1.7).
- Reports are on the pollster's own site as PDFs whose values sit in **chart
  images**, so expect manual double entry. Full toplines include "don't know"
  and null/blank, on two bases (use `share_base`).
- **Record the 1–3 May 2025 poll** (published 2025-05-05, after round 1) with
  its true `published_date`. The pipeline excludes it (M-1.7); the UI shows it
  with a notice.
- Some round-2 figures are reported as including the diaspora. Set
  `population_geo` and `target_scope` from the report or its partner (rule 3
  in ADR-0012). Where sources disagree on a methodology item, such as the
  parliamentary margin of error (±2 pp in the report vs ±3% in HotNews), use
  the pollster's report.
- Every option is recorded exactly as published. Never normalize, round, or
  guess.
- Candidates later excluded from the ballot, or who withdrew, are kept as
  published. Code handles them (M-1.5).
- Wording follows [ADR-0003](../docs/decisions/0003-neutral-language.md).

## Scope
**In:**
- `data/polls/atlasintel/` (polls, poll results, archive manifest, inventory)
- Append-only additions to the entity registry (only entities that T-004
  missed)

**Out:**
- Other pollsters, and analysis.

## Acceptance criteria
- [ ] The inventory lists every publication found, including polls missing
      from the discovery indexes. Each one is either extracted or excluded
      with a reason.
- [ ] Every extracted poll has an archived original (hash + Web Archive URL).
- [ ] Every poll transcribed by hand passed the double-entry diff.
- [ ] `uv run sondaje validate` reports 0 errors.
- [ ] The Outcome reports polls per election, the % from the original source,
      and the gaps.

## Follow-ups

## Log

## Outcome
