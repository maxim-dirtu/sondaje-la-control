---
id: T-006
title: Select MVP pollsters (2–4)
status: in-progress
phase: 0
depends_on: [T-005]
owner: agent-t006
branch: task/T-006-select-mvp-pollsters
methodology: [M-5.3]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
A documented, reproducible choice of 2–4 pollsters for the MVP, approved by the
owner.

## Context
[ADR-0007](../docs/decisions/0007-mvp-scope.md). This task also works as a
feasibility check for poll collection: it finds out how each house publishes
its results.

## Scope
**In:**
- `docs/reports/pollster-selection.md`: a scorecard of every pollster in the
  T-005 registry that was active in the 3 MVP elections
- A draft ADR `docs/decisions/draft-mvp-pollsters.md` proposing the selection

Scorecard criteria (score each one, with links as evidence):
1. **Coverage (required):** at least one poll inside the final window
   (M-1.3) for **each** of `parl-2024-cd`, `pres-2025-r1`, `pres-2025-r2`.
   Also count the total number of polls in the 120-day windows.
2. **Full topline:** the original publishes every option, including undecided
   and non-response.
3. **Transparency:** the M-5.3 checklist items that are published.
4. **Access:** the original report is available (own site, PDF), and its format
   is one of: text PDF, image or scanned PDF, HTML, media article only.
5. **Popularity:** how often major media cite the house (rough indicator).
6. **Diversity of the set:** different survey modes and client profiles, so
   that house effects can be compared. Describe them factually (ADR-0003).

**Out:**
- Collecting poll data, beyond what is needed to judge the criteria.

## Acceptance criteria
- [ ] Every candidate pollster is scored on criteria 1–5, with evidence links.
- [ ] The draft ADR proposes 2–4 houses, plus 1–2 reserves, with reasons.
- [ ] The report lists the publication formats found for each house. T-011
      needs this to know which extraction paths to support.
- [ ] The owner has approved the selection. The coordinator then numbers the ADR
      and creates one data task per pollster (T-012 onward).

## Follow-ups

## Log

## Outcome
