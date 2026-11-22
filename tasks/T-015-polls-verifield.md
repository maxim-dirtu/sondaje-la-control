---
id: T-015
title: "Polls: Verifield (MVP elections)"
status: todo
phase: 1
depends_on: [T-011]
owner: null
branch: null
methodology: [M-1.1, M-1.3, M-1.4, M-1.5, M-1.7, M-3.2, M-5.3]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
Every published voting-intention poll by **Verifield** (`verifield`) for the 3
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
- Expected volume: about 4–5 polls. Verifield is a **campaign house**: only
  its round-2 poll falls in the 28-day final window, so its polls feed the
  campaign metrics (M-3) in all three elections and the final-poll metrics
  for round 2 only. It gets "no grade yet" in the MVP (ADR-0010).
- The round-2 report is a text PDF with a full topline, hosted by HotNews. The
  other polls are known through media (Digi24, Libertatea): record them as
  media-only (`verified = false`) and archive the articles.
- Polls were commissioned by clients that the pollster's publications or the
  media name (see `pollster_affiliations.csv`). Record `sponsor` and
  `sponsor_type` exactly as the source states, and leave them out when it
  doesn't say. Never characterize a client or a result (ADR-0003).
- Every option is recorded exactly as published. Never normalize, round, or
  guess.

## Scope
**In:**
- `data/polls/verifield/` (polls, poll results, archive manifest, inventory)
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
