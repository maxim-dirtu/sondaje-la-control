---
id: T-012
title: "Results: Parliamentary 2024 (Chamber of Deputies)"
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
Official Chamber of Deputies list-vote results of 2024-12-01 for the
`domestic`, `diaspora`, and `total` scopes.

## Context
Polls ask about vote intention for parties, so the Chamber of Deputies vote is
the comparison target. Follow the shared instructions in
[T-010](T-010-results-ep-2024.md).

## Scope
**In:** the results file(s) for `parl-2024-cd`.
**Out:** the Senate results. Propose them as a follow-up if they turn out to be
useful.

## Acceptance criteria
- [ ] The three scopes are present, and domestic + diaspora = total for every
      party.
- [ ] The valid-vote totals match the official final report exactly.
- [ ] `uv run sondaje validate` passes.

## Follow-ups

## Log

## Outcome
