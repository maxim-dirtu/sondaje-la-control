---
id: T-011
title: "Results: Presidential 2024 round 1"
status: todo
phase: 1
depends_on: [T-003, T-004]
owner: null
branch: null
methodology: [M-1.4]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
Official results of the 2024-11-24 presidential first round for the `domestic`,
`diaspora`, and `total` scopes.

## Context
The election was later annulled by the Constitutional Court, but the results
published by BEC still serve as the reference for evaluating the polls. Follow
the shared instructions in [T-010](T-010-results-ep-2024.md).

## Scope
**In:** the results file(s) for `pres-2024-r1`.
**Out:** analysing the annulment itself.

## Acceptance criteria
- [ ] The three scopes are present, and domestic + diaspora = total for every
      candidate.
- [ ] The valid-vote totals match the final BEC report exactly.
- [ ] The annulment is noted in the file's notes and the source is linked in
      the Log.
- [ ] `uv run sondaje validate` passes.

## Follow-ups

## Log

## Outcome
