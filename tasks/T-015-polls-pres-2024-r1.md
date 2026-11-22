---
id: T-015
title: "Polls: Presidential 2024 round 1"
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
Every published first-round voting-intention poll whose fieldwork ended within
120 days before 2024-11-24, with full metadata and provenance.

## Context
Follow the shared instructions in [T-014](T-014-polls-ep-2024.md). Candidates
who withdrew before the vote stay in the data exactly as published. Their
handling is done in code (M-1.5).

## Scope
**In:** the poll files for `pres-2024-r1`.
**Out:** hypothetical second-round scenario polls. List them in Follow-ups if
they are abundant.

## Acceptance criteria
- [ ] Every poll on the index page inside the window is either included or
      listed in the Log with the reason it was excluded.
- [ ] `uv run sondaje validate` passes.
- [ ] The Outcome reports the number of polls and pollsters, and the % verified.

## Follow-ups

## Log

## Outcome
