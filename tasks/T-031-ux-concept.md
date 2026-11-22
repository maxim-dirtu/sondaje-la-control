---
id: T-031
title: UX concept and design references
status: in-progress
phase: 3
depends_on: []
owner: agent-t031-2
branch: task/T-031-ux-concept
methodology: [M-2.5, M-3.2, M-5]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
A UX concept that shows how the investigation's findings are explained to the
general public: storyboards and wireframes for the key screens, plus a short
visual-language guide.

## Context
[ADR-0008](../docs/decisions/0008-product-positioning.md): the UI explanation is
the top priority. This task can start immediately; it does not need real data
(use clearly fictitious example values). The owner considers sondajeromania.ro a
good reference for clarity and tone.

## Scope
**In:**
- `docs/ux/` (new): a design-references review of sondajeromania.ro and 2–3
  others (e.g. the FiveThirtyEight pollster ratings), covering what works and
  why. General ideas only; nothing is copied (no code, assets, or text).
- Storyboards/wireframes (Markdown + images or simple HTML mock-ups) for:
  - the pollster card: grade, one-sentence finding, diverging bar per party
  - the house × party heatmap
  - the per-election "target" plot (houses vs. actual result)
  - the campaign timeline (house vs. market vs. result)
  - the leaderboard
  - "how we measure this", explained in plain language
- A visual-language guide: typography, colours (party colours plus neutral UI),
  chart conventions, how uncertainty is shown, tone of the copy
  ([ADR-0003](../docs/decisions/0003-neutral-language.md))

**Out:**
- The production implementation (T-030 prototype, T-052 public site), and the
  final Romanian copy (T-051).

## Acceptance criteria
- [ ] Every key screen has a wireframe with a plain-language headline example.
- [ ] Each screen states the single question it answers for a non-expert.
- [ ] Uncertainty and "low certainty" states are designed, not left for later.
- [ ] The owner has reviewed the concept and recorded feedback in the Log.

## Follow-ups

## Log

## Outcome
