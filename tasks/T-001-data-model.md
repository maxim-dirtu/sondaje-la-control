---
id: T-001
title: Define data model and CSV schemas
status: todo
phase: 0
depends_on: []
owner: null
branch: null
methodology: [M-1, M-5.3]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
A complete, documented data model and CSV layout that every data-collection and
analysis task can rely on without further discussion.

## Context
- [ADR-0004](../docs/decisions/0004-data-storage-csv-in-git.md): canonical data is
  CSV in git, one file per election per data type.
- [METHODOLOGY M-1](../docs/METHODOLOGY.md) lists the fields the calculations need
  (sample size, fieldwork dates, target scope, alliances).
- M-5.3 lists the transparency fields captured per poll.

## Scope
**In:**
- `docs/DATA_MODEL.md` (new; this task owns it)
- `data/README.md` and the directory layout under `data/`, with header-only
  CSV files where useful
- ID conventions: elections (e.g. `ep-2024`, `pres-2024-r1`, `parl-2024-cd`,
  `pres-2025-r1`, `pres-2025-r2`), entities (parties/candidates), pollsters,
  and polls
- Entities to cover: elections, entities (parties/candidates), per-election
  alliance/label mapping, pollsters, polls (one row per poll), poll results
  (one row per poll × entity, raw published shares including undecided
  buckets), and election results (scope: `domestic` | `diaspora` | `total`)
- Poll metadata: fieldwork start/end, publish date, sample size, mode, sampled
  population, client/sponsor and sponsor type, question wording, whether the
  weighting and the margin of error were published, `source_url`, `source_type`
  (`pollster` | `media` | `wikipedia` | `other`), `verified` (whether checked
  against the original source), `retrieved_at`, and `notes`
- Append-only rule for shared registry files (`entities`, `pollsters`)

**Out:**
- Validation code (T-003) and real data (T-004, T-005, Phase 1).

## Acceptance criteria
- [ ] `DATA_MODEL.md` documents every column: name, type, required/optional,
      allowed values, and an example.
- [ ] The layout lets the Phase 1 tasks run in parallel without touching the
      same files (except append-only registries).
- [ ] Every input needed by M-1, M-2, M-3, M-4.1, and M-5.3 is present.
- [ ] Raw shares are stored exactly as published. The docs state that
      normalization happens in code, never in data.
- [ ] A worked example (one fictitious poll, clearly labelled as fictitious and
      kept out of `data/`) shows every file involved.

## Follow-ups

## Log

## Outcome
