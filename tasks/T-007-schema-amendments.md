---
id: T-007
title: Schema amendments from Phase 0 follow-ups
status: in-progress
phase: 0
depends_on: [T-003, T-004, T-005]
owner: agent-t007
branch: task/T-007-schema-amendments
methodology: [M-1.5]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
The data model, the validator, and the existing data can express every
situation found in Phase 0, without workarounds.

## Context
The follow-ups raised by T-003, T-004, and T-005 (see their task files). The
most important one: in `parl-2024-cd`, PMP ran on Forța Dreptei's lists, but
`entity_map` has no relation for "ran on another party's list". PMP is
currently mapped as `not_registered`, so a poll share for PMP would be dropped
instead of being added to Forța Dreptei.

## Scope
**In:**
- **Shared files allowed:** `docs/DATA_MODEL.md` (bump the schema version and
  follow §9), and the related code: `src/sondaje/schema.py`,
  `src/sondaje/validation/`, and tests.
- Amendments:
  1. **`entity_map` relation for running on another party's list** (e.g.
     `ran_on_list_of`). A poll share for the entity is added to the host
     entity's share. Update the PMP row in
     `data/elections/parl-2024-cd/entity_map.csv`, with a source. Check whether
     other parl-2024-cd parties are in the same situation.
  2. **Person with two roles** (e.g. a list independent in one election and a
     presidential candidate in another): document the ID rule in §4.2. Either
     confirm the current `-<year>` suffix approach or replace it, and update
     the data if it changes.
  3. **Person IDs:** clarify which given name is used (first given name,
     everyday name, or full name).
  4. **§7:** document the validator's output format
     (`path:row: [R-xx] error|warning: message`), the `--against REF` option,
     and the interpretations T-003 recorded in its Log (R-20, R-43, overlap
     reporting).
  5. **Survey `mode`:** a convention for face-to-face polls that don't say
     CAPI or PAPI, and for "random digital recruitment" polls (T-005
     follow-up).
  6. **`verified`:** define what it means for alias and affiliation rows.
  7. **Fill `counterpart_entity_id`** in `pollster_affiliations.csv` where the
     counterpart is now a registered entity.

**Out:**
- The poll inventory (T-011), local elections (T-062), and crosstabs (I-014).

## Acceptance criteria
- [ ] Each amendment is either done, or explicitly declined with a reason in
      the Log.
- [ ] The DATA_MODEL version is bumped and the change list follows §9.
- [ ] The validator and its tests are updated; every new rule has a passing and
      a failing fixture.
- [ ] `uv run sondaje validate` reports 0 errors; pytest and ruff pass.

## Follow-ups

## Log

## Outcome
