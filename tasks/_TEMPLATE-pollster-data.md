---
id: T-XXX
title: "Polls: <Pollster name> (MVP elections)"
status: todo
phase: 1
depends_on: [T-003, T-004, T-005, T-011]
owner: null
branch: null
methodology: [M-1.1, M-1.3, M-1.5, M-5.3]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

## Goal
Every published voting-intention poll by **<Pollster>** for the 3 MVP elections,
captured as a **full topline**, with transparency metadata and provenance.

Windows (fieldwork end date):
- `parl-2024-cd`: 120 days before 2024-12-01
- `pres-2025-r1`: 120 days before 2025-05-04
- `pres-2025-r2`: head-to-head polls with fieldwork between 2025-05-05 and
  2025-05-17. Pre-R1 hypothetical pairings are not R2 polls.

## Context
- Follow `docs/POLL_INGESTION.md` (from T-011) step by step.
- The T-006 report lists the formats this house publishes in.
- Every option is recorded exactly as published: all parties/candidates,
  other, undecided, and non-response. Never normalize, round, or guess.
- Candidates later excluded from the ballot, or who withdrew, are kept as
  published. Code handles them (M-1.5).
- Wording follows [ADR-0003](../docs/decisions/0003-neutral-language.md).

## Scope
**In:**
- This pollster's inventory, poll files, and archive manifest entries
- Append-only additions to the entity registry

**Out:**
- Other pollsters, and analysis.

## Acceptance criteria
- [ ] The inventory lists every publication found. Each one is either
      extracted or excluded with a reason.
- [ ] Every extracted poll has an archived original (hash + Web Archive URL).
- [ ] Every poll transcribed by hand passed the double-entry diff.
- [ ] `uv run sondaje validate` passes.
- [ ] The Outcome reports polls per election, the % from the original source,
      and the gaps.

## Follow-ups

## Log

## Outcome
