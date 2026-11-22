---
id: T-010
title: "Results: European Parliament 2024"
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
Official EP 2024 results (2024-06-09) for the `domestic`, `diaspora`, and
`total` scopes.

## Context
Shared instructions for all results tasks (T-010 to T-013):
- Use only official sources (AEP/BEC final results), never media summaries.
- Store votes. Shares are computed from valid votes.
- Every row has `source_url` and `retrieved_at`.
- An entity missing from the registry may be appended to the entities file.
  The file is append-only; existing rows are never edited.

## Scope
**In:** the results file(s) for `ep-2024`, as defined in DATA_MODEL.md.
**Out:** the local elections held on the same day (see T-062).

## Acceptance criteria
- [ ] The three scopes are present, and domestic + diaspora = total for every
      entity.
- [ ] The valid-vote totals match the official final report exactly.
- [ ] `uv run sondaje validate` passes.
- [ ] Any discrepancy between official sources is recorded in the Log.

## Follow-ups

## Log

## Outcome
