---
id: T-016
title: "Sponsor source: credit M-5.3 'client disclosed' only when the pollster discloses it"
status: todo
phase: 1
depends_on: [T-012, T-013, T-014, T-015]
owner: null
branch: null
methodology: [M-5.3, M-5.1d]
created: 2026-11-27
updated: 2026-11-27
---

## Goal
The data records **who** named a poll's client, so that the transparency
checklist (M-5.3) credits only the pollster's own disclosure. Media-sourced
clients still count for party-commissioned flags (M-5.1d).

## Context
- Owner decision, 2026-11-27 (T-011, question 2): when the pollster's
  publication names no client, a client stated explicitly by the media is
  recorded as the sponsor
  ([POLL_INGESTION.md §0.1](../docs/POLL_INGESTION.md)). First case: Verifield
  round 2 (`verifield-pres-2025-r2-20250506`, client named by HotNews).
- M-5.3 currently maps "client/sponsor published" to
  `sponsor_type ≠ not_disclosed` (DATA_MODEL §6.11). After that decision, a
  pollster would get credit for a disclosure that the media made.
- Waits for T-012…T-015, so that every poll file is migrated once.

## Scope
**In:**
- A way to record the sponsor's source in `polls.csv`, e.g. a
  `sponsor_source` column (`pollster` | `media`, empty when
  `not_disclosed`). The design is part of the task; record it in the Log.
- **Shared files allowed:** `docs/DATA_MODEL.md` (column, rule, changelog,
  M-5.3 mapping) and `docs/METHODOLOGY.md` (M-5.3 wording).
- Schema and validation code, with tests. Migration of every
  `data/polls/*/polls.csv`, filling the new column from each poll's sources
  and `notes`. Never guessed: an unclear case is flagged in the Log.
- `docs/POLL_INGESTION.md` §0.1 updated to fill the new column.

**Out:**
- Computing the transparency score (T-043).

## Acceptance criteria
- [ ] M-5.3 credits "client/sponsor" only for a pollster-disclosed client;
      METHODOLOGY and DATA_MODEL say so.
- [ ] Every existing poll has the new field filled, or empty for
      `not_disclosed`, with validation rules and tests.
- [ ] `uv run sondaje validate --against main`, pytest, and ruff pass.

## Follow-ups

## Log

## Outcome
