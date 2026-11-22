---
id: T-004
title: Election, party and alliance registry (MVP elections)
status: in-progress
phase: 0
depends_on: [T-001]
owner: agent-t004
branch: task/T-004-registry
methodology: [M-1.2, M-1.5]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
Registry rows for the 3 MVP elections (`parl-2024-cd`, `pres-2025-r1`,
`pres-2025-r2`; see [ADR-0007](../docs/decisions/0007-mvp-scope.md)) and for
every party, candidate, and alliance that appears in their official results.

## Context
The registry gives the Phase 1 tasks a shared vocabulary of IDs. Linking each
presidential candidate to the parties that supported them lets a lean toward a
**party** be tracked across both parliamentary and presidential elections (I-002).

## Scope
**In:**
- The registry files defined by T-001: elections, entities, and the alliance
  mapping
- Per entity: official name, short name, type (party/alliance/candidate/
  independent), and a chart color (hex)
- The alliance mapping (electoral alliances in `parl-2024-cd`), so that poll
  labels map to result entities
- Candidate → supporting party/parties for both presidential rounds, each with
  a source
- **Candidates that polls included but who are not in the official results**
  (withdrawn, excluded, or never registered): an entity row plus an
  `entity_map` row each, so that the pollster tasks don't all append the same
  rows. Use the discovery indexes (Wikipedia, sondajeromania.ro) to find them.

**Out:**
- Results and polls (Phase 1). Pollsters (T-005).

## Acceptance criteria
- [ ] All 3 MVP elections are present, with correct dates and round numbers.
- [ ] Every party, candidate, and alliance in the official results is present,
      with a source (AEP/BEC).
- [ ] Every alliance in these elections has a mapping.
- [ ] `sondaje validate` passes. If T-003 is not merged yet, the files match
      DATA_MODEL.md by manual check, recorded in the Log.

## Follow-ups

## Log

## Outcome
