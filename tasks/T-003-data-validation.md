---
id: T-003
title: Data validation tooling
status: todo
phase: 0
depends_on: [T-001, T-002]
owner: null
branch: null
methodology: []
created: 2026-11-22
updated: 2026-11-22
---

## Goal
`uv run sondaje validate` catches every schema, integrity, and provenance
error in `data/` before it reaches the analysis.

## Context
CSV does not enforce a schema ([ADR-0004](../docs/decisions/0004-data-storage-csv-in-git.md)).
Several agents add data concurrently, so validation is their shared safety net.

## Scope
**In:**
- `src/sondaje/` validation module plus the CLI subcommand, and tests with
  valid and invalid fixtures
- One machine-readable schema definition in code, kept consistent with
  `docs/DATA_MODEL.md`

**Out:**
- Fixing the data itself.

## Acceptance criteria
- [ ] Checks required columns, types, enums, and UTF-8 encoding.
- [ ] Checks referential integrity: election, entity, pollster, and poll IDs.
- [ ] Checks dates: fieldwork start ≤ end ≤ election date, and publish date ≥
      fieldwork end.
- [ ] Checks sums: raw poll shares sum to 100 ± a tolerance, and result shares
      and votes are consistent.
- [ ] Checks provenance: `source_url` and `retrieved_at` are not empty.
- [ ] Detects duplicate polls (same pollster, fieldwork dates, and election).
- [ ] Errors report `file:row: message`, and the exit code is non-zero on error.
- [ ] Each check has at least one passing and one failing test fixture.

## Follow-ups

## Log

## Outcome
