---
id: T-003
title: Data validation tooling
status: in-progress
phase: 0
depends_on: [T-001, T-002]
owner: agent-t003
branch: task/T-003-data-validation
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
- The integrity rules **R-01…R-94** in DATA_MODEL.md §7, with their
  parameters (`share_sum_tolerance_pp`, `max_poll_age_days`, and an injectable
  `reference_date`, so that the fictitious 2099 example in §10 can be a test
  fixture). R-34 (append-only check against `main`) may be a separate command.

**Out:**
- Fixing the data itself.

## Acceptance criteria
- [ ] Every rule in DATA_MODEL.md §7 is implemented, or listed in the Log
      with the reason it was deferred.
- [ ] Checks required columns, types, enums, and UTF-8 encoding.
- [ ] Checks referential integrity: election, entity, pollster, poll, and
      document IDs.
- [ ] Checks dates: fieldwork start ≤ end < election date (R-81; exit polls
      are out of scope), and publish date ≥ fieldwork end.
- [ ] Checks sums: raw poll shares sum to 100 ± the tolerance for each
      (poll, share base), and domestic + diaspora = total for results.
- [ ] Checks provenance: `source_url` and `retrieved_at` are not empty.
- [ ] Detects duplicate polls (same pollster, fieldwork dates, and election).
- [ ] Errors report `file:row: message`, and the exit code is non-zero on error.
- [ ] Each check has at least one passing and one failing test fixture.

## Follow-ups

## Log

## Outcome
