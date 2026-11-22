---
id: T-014
title: "Polls: European Parliament 2024"
status: todo
phase: 1
depends_on: [T-003, T-004, T-005]
owner: null
branch: null
methodology: [M-1.1, M-1.3, M-5.3]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
Every published voting-intention poll for EP 2024 whose fieldwork ended within
120 days before 2024-06-09, with full metadata and provenance.

## Context
Shared instructions for all poll tasks (T-014 to T-017):
- The Wikipedia "Opinion polling for ..." page is an **index**. For every poll,
  try to find the original publication (the pollster's site, or the media
  outlet that commissioned it). Set `verified` and `source_type` accordingly.
- Store **raw published shares**, including the undecided/other buckets if they
  were published. Never normalize in the data (M-1.1 is done in code).
- Capture every transparency field (M-5.3) the original publishes. Leave a
  field empty if it was not published; never guess.
- Map poll labels to entities through the alliance mapping. Missing entities or
  pollsters may be appended to the registries (append-only).
- Follow [ADR-0003](../docs/decisions/0003-neutral-language.md) in all notes.

## Scope
**In:** the poll files for `ep-2024`, as defined in DATA_MODEL.md.
**Out:** analysis of any kind.

## Acceptance criteria
- [ ] Every poll on the index page inside the window is either included or
      listed in the Log with the reason it was excluded.
- [ ] Polls found outside Wikipedia are included and marked as such.
- [ ] `uv run sondaje validate` passes.
- [ ] The Outcome reports the number of polls and pollsters, and the % verified
      against the original source.

## Follow-ups

## Log

## Outcome
