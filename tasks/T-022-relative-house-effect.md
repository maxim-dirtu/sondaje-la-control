---
id: T-022
title: Relative house effect and relative accuracy
status: todo
phase: 2
depends_on: [T-021]
owner: null
branch: null
methodology: [M-2.5, M-2.6]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
For each (house, election, entity), the error relative to the market, and for
each (house, election), the accuracy relative to the median house.

## Context
This is the core of I-002: it separates house-specific lean from
industry-wide misses.

## Scope
**In:** `src/sondaje/metrics/` and its tests.
**Out:** significance testing (T-024).

## Acceptance criteria
- [ ] If every house has the same error, all house effects are 0 (test).
- [ ] A synthetic house with a +3 pp offset is recovered exactly (test).
- [ ] The output tables have documented columns.

## Follow-ups

## Log

## Outcome
