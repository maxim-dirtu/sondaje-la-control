---
id: T-004
title: Election, party and alliance registry (2024–2025)
status: todo
phase: 0
depends_on: [T-001]
owner: null
branch: null
methodology: [M-1.2, M-1.5]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
Registry rows for the 5 MVP elections and for every party, candidate, and
alliance that appears in their official results.

## Context
MVP elections: see [PLAN.md](../docs/PLAN.md). The registry gives the Phase 1
tasks a shared vocabulary of IDs.

## Scope
**In:**
- The registry files defined by T-001: elections, entities, and the alliance
  mapping
- Per entity: official name, short name, type (party/alliance/candidate/
  independent), and a chart color (hex)
- The alliance mapping, e.g. joint lists in EP 2024, so that poll labels map to
  result entities

**Out:**
- Results and polls (Phase 1). Pollsters (T-005).

## Acceptance criteria
- [ ] All 5 MVP elections are present, with correct dates and round numbers.
      The annulment of Presidential 2024 R1 is recorded.
- [ ] Every party, candidate, and alliance in the official results is present,
      with a source (AEP/BEC).
- [ ] Every alliance in these elections has a mapping.
- [ ] `sondaje validate` passes. If T-003 is not merged yet, the files match
      DATA_MODEL.md by manual check, recorded in the Log.

## Follow-ups

## Log

## Outcome
