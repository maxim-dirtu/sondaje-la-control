---
id: T-010
title: "Results ingestion: Parliamentary 2024 and Presidential 2025 (R1, R2)"
status: in-progress
phase: 1
depends_on: [T-002, T-003, T-004]
owner: agent-t010
branch: task/T-010-results-ingestion
methodology: [M-1.4]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
A reproducible downloader that produces the official results of the 3 MVP
elections for the `domestic`, `diaspora`, and `total` scopes.

## Context
- prezenta.roaep.ro (AEP) publishes final per-polling-station results (PV) as
  CSV.
- The open-source project
  [gov2-ro/prezenta.roaep.ro](https://github.com/gov2-ro/prezenta.roaep.ro)
  already downloads these files. Study it for URL patterns and file formats.
  Check its license before reusing any code. If no license is found, reuse
  knowledge only.
- The BEC final official results are the control totals.

## Scope
**In:**
- `src/sondaje/ingest/results.py` and a CLI command
  `sondaje ingest-results <election_id>`
- The results files for `parl-2024-cd` (Chamber of Deputies list vote),
  `pres-2025-r1`, and `pres-2025-r2`
- Raw downloads go to `data/raw/` (git-ignored). Their source URLs and SHA-256
  hashes are recorded in a committed manifest.
- An entity missing from the registry may be appended to the entities file
  (append-only). T-004 is a dependency, so rebase on its merge first; only
  entities that T-004 missed may be appended.

**Out:**
- Results below the national level (county, polling station). Propose them as
  a follow-up.
- The Senate results.

## Acceptance criteria
- [ ] Re-running the command reproduces the committed results files exactly.
- [ ] domestic + diaspora = total for every entity.
- [ ] The valid-vote totals and the per-entity votes match the BEC final report.
      The comparison is recorded in the Log.
- [ ] `uv run sondaje validate` passes. Tests cover parsing and aggregation, on
      a small fixture.

## Follow-ups

## Log

## Outcome
