# ADR-0004: Canonical data as versioned CSV in git

- **Status:** Proposed (working default)
- **Date:** 2026-11-22
- **Related:** T-001, T-003

## Context
The dataset is small: thousands of poll rows, not millions. It is curated by
hand or by agents, and every value must be traceable to a source. Several
agents add data concurrently.

## Decision
- The canonical data lives in `data/` as UTF-8 CSV files, one file per
  election and data type. This keeps concurrent agents on separate files.
- Every row has `source_url` and `retrieved_at`.
- The analysis code reads the CSVs, using DuckDB/pandas where convenient.
  Derived outputs go to `build/`, which is git-ignored and reproducible.
- A database for the public site is a separate decision (T-050), loaded from
  these CSVs.

## Consequences
- Data changes can be reviewed as diffs, and every change is linked to a task
  commit.
- Validation (T-003) is required, because CSV does not enforce a schema.

## Alternatives considered
- PostgreSQL as the source of truth: harder to review, adds operational
  overhead early, and gives weaker provenance.
- A single large CSV: frequent merge conflicts between agents.
