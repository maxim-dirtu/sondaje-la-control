---
id: T-030
title: Prototype dashboard (real data, applying the owner decisions)
status: todo
phase: 3
depends_on: [T-025, T-031]
owner: null
branch: null
methodology: [M-1.3, M-1.7, M-2.5, M-3.2, M-5.2]
created: 2026-11-27
updated: 2026-11-27
---

## Goal
An internal, clickable prototype that shows the real MVP results (not made-up
data) with the visual language of T-031, so the owner can explore every metric
and judge whether the explanations work for a non-expert.

## Context
- T-031 delivered static mock-ups with fictitious data in `docs/ux/mockups/`.
  They were drawn **before** several owner decisions, so the prototype must
  apply the corrections listed below. The mock-ups themselves are not
  redone; they carry a note that they are superseded on these points.
- [ADR-0008](../docs/decisions/0008-product-positioning.md): the product is an
  investigation, and the explanation comes first.
- [ADR-0009](../docs/decisions/0009-design-direction-light-first.md):
  light mode first; design inspiration only from sondajeromania.ro.
- Reuse the design tokens and components in
  `docs/ux/mockups/tokens.css` and `components.css`.

## Scope
**In:**
- The prototype app. Choosing the technology is part of the task (Streamlit or
  a static site generated from `build/`). Record the choice and the reason in
  the Log, and in a draft ADR if it affects T-050.
- The screens of T-031: leaderboard, pollster card, house × party heatmap, one
  election (target plot), campaign timeline, and "how we measure".
- Reading the output of the metrics tasks (T-021…T-024, T-025). It never
  recomputes a metric itself.
- **Shared files allowed:** `docs/ux/` (to bring the docs in line with the
  decisions below).

**Out:**
- Anything public: hosting, final Romanian copy (T-051), right of reply
  (T-053). Bayesian model, herding and trust score (T-040…T-043); until those
  exist, the screens show the states "not available yet".

## Fixes to apply (decisions made after the mock-ups)

| # | Fix | Decision | Where the mock-ups differ |
|---|---|---|---|
| 1 | **Final window is 28 days**, not 21. Every label, band and explanation says 28 | ADR-0012, M-1.3 | `timeline.html`, `target-plot.html`, `methodology.html`, `pollster-card.html`, `heatmap.html`, `tokens.css`, `storyboard.md`, `visual-language.md` |
| 2 | **The pollster card leads with a balanced summary**: overall accuracy against the other houses, and whether any clear deviation exists. A party is not named in the first line by default. The per-party deviations follow | ADR-0010 | `pollster-card.html`, `leaderboard.html`, `storyboard.md`, `design-references.md` lead with the strongest deviation |
| 3 | **Grades**: shown as "provisional" in the MVP; **no grade below 3 elections**, shown as "no grade yet" with the findings and their uncertainty | ADR-0010, M-5.2 | Check the leaderboard and card variants |
| 4 | **Polls published on or after election day** are shown with a notice ("published after the vote, not counted in the calculations") and are excluded from every metric | ADR-0012, M-1.7 | Not in the mock-ups |
| 5 | **Lower verification level** for polls with `verified = false` (media-only sources, e.g. Sociopol), visible next to the poll and in any figure that uses it | ADR-0012 | Not in the mock-ups |
| 6 | **Campaign houses** (e.g. Verifield: final window in one election only): the card says which elections count for the final-poll metrics and which only for the campaign view | ADR-0012 | Not in the mock-ups |
| 7 | Remove the "Date fictive" banner from screens that use real data. Keep it on any screen that still uses fixtures | T-031 | Banner is on every page |
| 8 | Check the **desktop two-column layout** (wider than 960 px), which the T-031 agent could not screenshot | T-031 follow-up | `components.css` |
| 9 | **Every number links to its source** (I-019). A small external-link icon (↗) next to each poll value and each official result opens a popover. For polls it shows the original publication (`source_url`), the archived copy (`archive_url`), and the verification level (the pollster's own report vs media only; wording by T-051). For results it links the AEP/BEC source. The links are generated from `polls.document_id` → `archive_manifest.csv`, never typed by hand. Polls with sources in several documents (e.g. a graphic plus the article that gives the fieldwork dates) list every document. Also add an internal **sources page**: every archived document with both links, its SHA-256, its inventory status and the polls it feeds | Owner, 2026-11-27 | The mock-ups only have a "Sursa" column and a CSV download |

## Acceptance criteria
- [ ] All screens read real MVP data produced by the pipeline. None contains
      hard-coded figures.
- [ ] Each of the 9 fixes above is done, or declined with a reason in the Log.
- [ ] No screen uses accusatory wording ([ADR-0003](../docs/decisions/0003-neutral-language.md)).
      Every deviation shows its magnitude and its uncertainty.
- [ ] The low-certainty, "no grade yet" and "not available yet" states are
      shown, not hidden.
- [ ] The owner has explored the prototype, and the feedback is in the Log.
- [ ] Docs in `docs/ux/` are updated to match; ruff and pytest pass.

## Follow-ups

## Log
- 2026-11-27 (coordinator): fix 9 (source links and the sources page) added
  at the owner's request (I-019). The owner chose a popover that shows both
  links and the verification level. The internal lookup is built here, not as
  a separate CLI task.

## Outcome
