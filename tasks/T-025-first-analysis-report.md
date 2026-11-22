---
id: T-025
title: First analysis report and parameter sensitivity
status: todo
phase: 2
depends_on: [T-010, T-021, T-022, T-023, T-024]   # plus the per-pollster data tasks, added by the coordinator after T-006
owner: null
branch: null
methodology: [M-1.3, M-1.2, M-2, M-3.2, M-4.1, M-4.2, M-4.3]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
A reproducible report on the MVP data (3 elections, 2–4 pollsters) that ranks
the pollsters by accuracy and shows their house effects per party, together
with a sensitivity analysis of the main parameters.

## Context
This is the first real test of the methodology (Milestone M2). Its findings
feed the parameter defaults and the prototype (T-030). With at most 3
(house, election) pairs per house, significance results are **preliminary**
([ADR-0007](../docs/decisions/0007-mvp-scope.md)), and the report must say so
clearly.

## Scope
**In:**
- A CLI command `sondaje report` that writes to `build/`
- A committed summary `docs/reports/first-analysis.md`
- Sensitivity runs: `window_days` ∈ {14, 21, 30}, `tau` ∈ {5, 7, 10}, and
  `small_party_threshold` ∈ {0.5, 1, 2}%

**Out:**
- Bayesian modelling and the trust score.

## Acceptance criteria
- [ ] One command regenerates the report from `data/`.
- [ ] The report states its limitations: sample of elections, data coverage,
      and the % of verified polls.
- [ ] Rankings that are unstable across parameter settings are flagged.
- [ ] The wording follows ADR-0003.
- [ ] Recommended parameter values are proposed under Follow-ups, as a
      METHODOLOGY change.

## Follow-ups

## Log

## Outcome
