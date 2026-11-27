---
id: T-014
title: "Polls: CURS (MVP elections)"
status: in-progress
phase: 1
depends_on: [T-011]
owner: copilot (Sonnet)
branch: task/T-014-polls-curs
methodology: [M-1.1, M-1.3, M-1.4, M-1.5, M-1.7, M-5.3]
created: 2026-11-22
updated: 2026-11-27
---

## Goal
Every published voting-intention poll by **CURS** (`curs`) for the 3 MVP
elections, captured as a **full topline**, with transparency metadata and
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
- Expected volume: about 7 polls. The house publishes national reports as text
  PDFs and as slide images on its own site (curs.ro), and reports 6 of the 7
  M-5.3 transparency items, including weighting.
- Both collection modes occur: face-to-face and CATI. Record the mode per poll
  as the report states it (see DATA_MODEL §6.11 conventions for reports that
  say "face-to-face" without naming CAPI or PAPI).
- The round-2 poll is known through TVR Info only. Record it as media-only
  (`verified = false`) and say so in `notes`.
- The latest parliamentary and round-1 polls end 26 and 24 days before the
  vote, inside the 28-day final window (ADR-0012).
- Every option is recorded exactly as published. Never normalize, round, or
  guess.
- Wording follows [ADR-0003](../docs/decisions/0003-neutral-language.md).

## Scope
**In:**
- `data/polls/curs/` (polls, poll results, archive manifest, inventory)
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
