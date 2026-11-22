---
id: T-031
title: UX concept and design references
status: review
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
- [x] Every key screen has a wireframe with a plain-language headline example.
- [x] Each screen states the single question it answers for a non-expert.
- [x] Uncertainty and "low certainty" states are designed, not left for later.
- [ ] The owner has reviewed the concept and recorded feedback in the Log.

## Follow-ups
- **T-043 / M-5.2 (grade ceiling in the MVP):** with `N0 = 3` and at most 3
  elections, the shrunk score cannot exceed 75 (A is unreachable; B needs a raw
  score >= 90). Decide whether letter grades are shown during the MVP or only
  findings + certainty (open UX question 1 in `docs/ux/storyboard.md`).
- **T-043 / M-5.2 ("not rated" threshold):** the mock-ups propose no grade
  unless a house has final polls in at least 2 elections. M-5.2 currently
  computes a score for N = 1. Needs a spec decision.
- **METHODOLOGY (display thresholds):** specify (a) the interval level used in
  the UI (mock-ups assume 90% everywhere, matching M-4.4), (b) the minimum
  number of campaign polls for a campaign metric (proposed 3), and (c) the
  thin-market rule (proposed: hatch periods with fewer than 2 other houses).
- **T-004:** store a display colour per party; check >= 3:1 against white and
  add an outline when it fails (visual-language §3.3).
- **T-051:** confirm the Romanian glossary used in the mock-ups ("abatere
  sistematică", "p.p.", "certitudine scăzută/medie/ridicată", "Ce nu spunem",
  "fără sondaj final", "apropiere la final", "sondaje neobișnuit de stabile")
  and the banned-word list in visual-language §8.
- **T-030:** build on `docs/ux/mockups/tokens.css` + `components.css`;
  implement the heatmap detail panel / mobile bottom sheet, the target-plot
  hover highlight, and verify 44 px touch targets.
- **T-050 / T-052:** self-host one sans and one serif with Romanian comma-below
  coverage; no ads inside investigative content; dark mode only as the token
  mapping in visual-language §9.
- **PLAN.md (coordinator):** link `docs/ux/` from Phase 3 / T-030.

## Log
- 2026-11-22 (agent-t031): claimed the task; wrote the first design-references
  review (sondajeromania.ro, 538, OWID, Pew). The agent was cancelled before
  the other deliverables.
- 2026-11-22: the owner clarified the design direction, recorded as ADR-0009:
  sondajeromania.ro is an inspiration for visual design, design system and UX
  only (not its mechanisms); light mode is primary (dark-first looks "AI-ish");
  the visual language is a small token-based design system.
- 2026-11-22 (agent-t031-2): resumed the task; rebased the branch on `main`
  (ADR-0009). Re-checked sondajeromania.ro in a browser: it defaults to dark mode
  and has a light theme toggle; observed the light theme only for general
  patterns (canvas, cards, type hierarchy, eyebrows, nav). Nothing copied.
- 2026-11-22: revised `design-references.md` into "design ideas we take" vs.
  "mechanisms we deliberately don't adopt" vs. "presentation details we do
  differently"; the previous text described the dark default as the reference.
- 2026-11-22: design decisions: blue = overestimates (right), orange =
  underestimates (left); colour only for data, links/nav in ink; party colours
  only as chips; pollsters never colour-coded (ink + shape + label); serif only
  for the headline finding; grade badges are neutral ink, no traffic lights; no
  ordinal ranks (grade groups, alphabetical); heatmap cells coloured only when
  the 90% interval excludes zero; placeholder party palette away from blue/orange
  and from real Romanian party colours.
- 2026-11-22: fictitious content only: pollsters "Institutul Alfa", "Beta
  Research", "Gamma Data", "Delta Opinion"; parties "Partidul A–E"; elections
  "Alegerea 1–3" (not the real MVP elections, to avoid real events with
  invented numbers). The example numbers are internally consistent (signed
  errors sum to zero per poll; relative effects and averages match across
  screens). Brand placeholder: "Sondaje la control" (repository name; Q1 open).
- 2026-11-22: while mocking the leaderboard, found that M-5.2 shrinkage with
  N <= 3 caps grades at B (see Follow-ups); mocked honestly (hatched "A").
- 2026-11-22: contrast ratios computed with the WCAG 2 formula and listed in
  visual-language §2 and §9.
- 2026-11-22: opened every mock-up in the integrated browser at ~800 px and
  390 px widths. Fixed: CSS decoded with the wrong charset (added `@charset`
  and escaped non-ASCII `content` strings), mobile overflow (grid minmax, legend
  wrap), unreadable phone chart (added a stacked phone variant of the diverging
  bar), two-row sticky nav on phones (now a scrollable row). The two-column
  desktop layout (> 960 px) could not be screenshot at full width because the
  browser window was limited to ~800 px.
- Owner review: pending.

## Outcome
UX concept delivered in `docs/ux/`:
- `design-references.md`: review of sondajeromania.ro (light mode; design
  ideas taken vs. mechanisms not adopted, per ADR-0009), 538, OWID, Pew, and a
  synthesis of 9 principles.
- `visual-language.md`: the design system (tokens for colour, type, spacing,
  radius, elevation; colour-blind-safe diverging encoding; party-colour rules;
  number formatting; chart conventions; a table of uncertainty and data states;
  component inventory; tone of copy; optional dark-mode token mapping;
  accessibility checklist).
- `storyboard.md`: the reader journey and disclosure layers; per screen the
  question, a Romanian headline example, first view vs. on click, and the
  low-certainty / insufficient-data states; a states matrix; 5 open UX
  questions.
- `mockups/`: `tokens.css`, `components.css`, and static light-mode HTML
  mock-ups with inline SVG charts and no external resources: `index.html`,
  `leaderboard.html`, `pollster-card.html`, `heatmap.html`,
  `target-plot.html`, `timeline.html`, `methodology.html`, plus the
  `components.html` specimen. Every page carries the "Date fictive" banner.

Key commits: `d51c8f7` (tokens/components), `224b058` (pollster card),
`bdbcdd5` (heatmap), `68529e3` (target plot), `c962ba0` (timeline), `d8159fc`
(leaderboard), `735ec18` (methodology), `9e3b8ba` (ADR-0009 revision of the
references), `693cd75` (visual language), `4c0935a` (storyboard), `629b75e`
(responsive fixes).

Known limitations: the owner has not reviewed the concept yet; the Romanian
copy is a draft for tone (T-051); interactions (hover, selectors, bottom sheet)
are described but static; desktop layouts wider than ~800 px were checked only
by CSS reasoning, not by screenshot; no web fonts are loaded, so the rendering
depends on the fonts installed locally.