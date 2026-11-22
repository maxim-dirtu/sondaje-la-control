---
id: T-017
title: "Polls: Presidential 2025 rounds 1 and 2"
status: todo
phase: 1
depends_on: [T-003, T-004, T-005]
owner: null
branch: null
methodology: [M-1.1, M-1.3, M-1.5, M-5.3]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
Every published voting-intention poll for both 2025 rounds, with full metadata
and provenance:
- round 1: fieldwork ending within 120 days before 2025-05-04
- round 2: head-to-head polls with fieldwork between 2025-05-05 and 2025-05-17

## Context
Follow the shared instructions in [T-014](T-014-polls-ep-2024.md). Polls
published before round 1 that model a hypothetical round-2 pairing are not
round-2 polls.

## Scope
**In:** the poll files for `pres-2025-r1` and `pres-2025-r2`.
**Out:** hypothetical pairings (list them in Follow-ups if needed).

## Acceptance criteria
- [ ] Every poll on the index page inside each window is either included or
      listed in the Log with the reason it was excluded.
- [ ] `uv run sondaje validate` passes.
- [ ] The Outcome reports the number of polls and pollsters per round, and the
      % verified.

## Follow-ups

## Log

## Outcome
