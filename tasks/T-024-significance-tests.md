---
id: T-024
title: Significance tests
status: todo
phase: 2
depends_on: [T-022]
owner: null
branch: null
methodology: [M-4.1, M-4.2, M-4.3]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
For every (house, entity): sampling z-scores per poll, and a sign test and a
t-test across elections, using (house, election) as the unit.

## Context
These tests separate systematic lean from noise. They are the frequentist
precursor of the Bayesian model (T-040).

## Scope
**In:** `src/sondaje/stats/` and its tests.
**Out:** the Bayesian model (T-040).

## Acceptance criteria
- [ ] The results match SciPy reference values in the tests.
- [ ] The unit of independence follows M-1.6 (tested).
- [ ] Combinations with fewer than 3 elections are flagged as insufficient
      instead of being tested.

## Follow-ups

## Log

## Outcome
