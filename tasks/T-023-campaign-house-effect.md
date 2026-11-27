---
id: T-023
title: Market average and campaign house effect
status: in-progress
phase: 2
depends_on: [T-020]
owner: copilot-t023
branch: task/T-023-campaign-house-effect
methodology: [M-3.1, M-3.2]
created: 2026-11-22
updated: 2026-11-28
---

## Goal
A smoothed market average over the campaign, plus each house's average
deviation from it across the whole campaign (leave-one-house-out).

## Context
This captures any lean during the campaign that a final-poll analysis would
miss (I-004). It is also the input for the convergence flag (T-042).

## Scope
**In:**
- `src/sondaje/metrics/` and its tests
- **Shared file allowed:** `docs/METHODOLOGY.md` sections M-3.1 and M-3.2 (to
  record the smoothing method chosen)

**Out:**
- The convergence flag (T-042) and herding (T-041).

## Acceptance criteria
- [ ] A synthetic house with a constant +3 pp offset over a moving trend is
      recovered within ±0.5 pp.
- [ ] Leave-one-house-out is verified by a test.
- [ ] The smoothing method and its parameters are recorded in METHODOLOGY.

## Follow-ups

## Log

## Outcome
