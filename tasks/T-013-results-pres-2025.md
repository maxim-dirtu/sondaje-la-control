---
id: T-013
title: "Results: Presidential 2025 rounds 1 and 2"
status: todo
phase: 1
depends_on: [T-003, T-004]
owner: null
branch: null
methodology: [M-1.4, M-1.5]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
Official results of the 2025-05-04 and 2025-05-18 presidential rounds for the
`domestic`, `diaspora`, and `total` scopes.

## Context
Each round is a separate election (M-1.5). Follow the shared instructions in
[T-010](T-010-results-ep-2024.md).

## Scope
**In:** the results file(s) for `pres-2025-r1` and `pres-2025-r2`.
**Out:** none.

## Acceptance criteria
- [ ] Both rounds are present with all three scopes, and domestic + diaspora =
      total for every candidate.
- [ ] The valid-vote totals match the official final reports exactly.
- [ ] `uv run sondaje validate` passes.

## Follow-ups

## Log

## Outcome
