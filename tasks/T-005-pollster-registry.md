---
id: T-005
title: Pollster registry and transparency metadata
status: todo
phase: 0
depends_on: [T-001]
owner: null
branch: null
methodology: [M-5.3]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
A registry of every polling firm that published polls for the MVP elections,
with name aliases and sourced background information.

## Context
Pollster names appear in many variants across media. The aliases let the Phase 1
tasks map them consistently. The sponsor and affiliation information feeds
M-5.1d and M-5.3. [ADR-0003](../docs/decisions/0003-neutral-language.md)
applies to every description.

## Scope
**In:**
- The pollster registry file defined by T-001: ID, official name, aliases,
  website, typical survey modes, and known affiliations or regular clients
  (each with a source)
- A seed list taken from the "Opinion polling" Wikipedia pages of the 5 MVP
  elections (used as an index)

**Out:**
- Per-poll transparency fields, which the poll tasks capture.

## Acceptance criteria
- [ ] Every pollster with at least one poll on the indexed pages is listed.
- [ ] Every affiliation or client claim has a `source_url`. Unsourced claims
      are left out.
- [ ] The wording is factual and neutral.
- [ ] Validation passes (or is checked manually, as in T-004).

## Follow-ups

## Log

## Outcome
