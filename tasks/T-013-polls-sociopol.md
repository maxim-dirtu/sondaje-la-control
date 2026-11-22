---
id: T-013
title: "Polls: Sociopol (MVP elections)"
status: todo
phase: 1
depends_on: [T-011]
owner: null
branch: null
methodology: [M-1.1, M-1.3, M-1.4, M-1.5, M-1.7, M-5.3]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
Every published voting-intention poll by **Sociopol** (`sociopol`) for the 3
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
- Expected volume: about 14 polls (12 in round 1). The house has no website
  of its own; its polls are published only through the România TV
  broadcasts and articles.
- **Media-only sources** (ADR-0012 rule 1): record each poll with
  `verified = false`, and archive the article and any broadcast graphic. When
  the TV graphic and the article text disagree, use the graphic as the
  primary value and put the text value in `notes`. Known case: the 20–22 Nov
  2024 parliamentary poll shows USR at 13% on the graphic and 15% in the text.
- That 20–22 Nov 2024 parliamentary poll is missing from all discovery
  indexes. Search beyond them (rule 4).
- Toplines are published without an undecided share. If a topline sums to 100
  with no undecided option, record exactly what was published and note it. A
  DATA_MODEL clarification may follow.
- The round-2 poll is known only from an on-air statement by the director. Do
  not invent fields, and mark gaps in `notes`.
- Every option is recorded exactly as published. Never normalize, round, or
  guess.
- Wording follows [ADR-0003](../docs/decisions/0003-neutral-language.md).
  Affiliation records are factual and sourced (T-005).

## Scope
**In:**
- `data/polls/sociopol/` (polls, poll results, archive manifest, inventory)
- Append-only additions to the entity registry (only entities that T-004
  missed)

**Out:**
- Other pollsters, and analysis.

## Acceptance criteria
- [ ] The inventory lists every publication found, including polls missing
      from the discovery indexes. Each one is either extracted or excluded
      with a reason.
- [ ] Every extracted poll has an archived original (hash + Web Archive URL).
      For broadcast graphics, the archived item is the best available
      capture; say which in `notes`.
- [ ] Every poll transcribed by hand passed the double-entry diff.
- [ ] `uv run sondaje validate` reports 0 errors.
- [ ] The Outcome reports polls per election, the % from the original source,
      and the gaps.

## Follow-ups

## Log

## Outcome
