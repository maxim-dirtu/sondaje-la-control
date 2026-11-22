---
id: T-016
title: "Polls: Parliamentary 2024"
status: todo
phase: 1
depends_on: [T-003, T-004, T-005]
owner: null
branch: null
methodology: [M-1.1, M-1.3, M-5.3]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
Every published party voting-intention poll whose fieldwork ended within 120
days before 2024-12-01, with full metadata and provenance.

## Context
Follow the shared instructions in [T-014](T-014-polls-ep-2024.md). The
comparison target is the Chamber of Deputies list vote (T-012).

## Scope
**In:** the poll files for `parl-2024-cd`.
**Out:** none.

## Acceptance criteria
- [ ] Every poll on the index page inside the window is either included or
      listed in the Log with the reason it was excluded.
- [ ] `uv run sondaje validate` passes.
- [ ] The Outcome reports the number of polls and pollsters, and the % verified.

## Follow-ups

## Log

## Outcome
