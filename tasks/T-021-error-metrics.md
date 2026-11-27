---
id: T-021
title: Error metrics
status: in-progress
phase: 2
depends_on: [T-020]
owner: github-copilot-cli
branch: task/T-021-error-metrics
methodology: [M-2.1, M-2.2, M-2.3, M-2.4]
created: 2026-11-22
updated: 2026-11-28
---

## Goal
Signed error, MAE, total error, and log-odds accuracy per poll and per final
poll of each (house, election).

## Context
See [METHODOLOGY M-2](../docs/METHODOLOGY.md).

## Scope
**In:**
- `src/sondaje/metrics/` and its tests
- **Shared file allowed:** `docs/METHODOLOGY.md` section M-2, for edge-case
  clarifications only (e.g. a share of 0 in log-odds)

**Out:**
- Comparisons between houses (T-022).

## Acceptance criteria
- [ ] Each metric is tested against a hand-computed example.
- [ ] Edge cases (zero shares, a missing entity) behave as documented in the
      spec.
- [ ] Docstrings cite the M-IDs.

## Follow-ups

## Log

## Outcome
