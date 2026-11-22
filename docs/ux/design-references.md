# Design references

**Task:** T-031 · **Reviewed:** 2026-11-22 (revised the same day for ADR-0009)
· **Related:** ADR-0003, ADR-0008, ADR-0009, I-018

This review covers four references that explain polls or pollster quality to
non-experts. For each one it records what works for a general audience and
why, and what this project should avoid.

**Scope of the inspiration ([ADR-0009](../decisions/0009-design-direction-light-first.md)).**
From sondajeromania.ro we take ideas for the **visual design, the design
system, and the UX** only: layout, typography, spacing, component style,
readability, navigation, and theming (its light mode). We do **not** adopt its
product logic or mechanisms. It is a poll aggregator; this project is an
investigation ([ADR-0008](../decisions/0008-product-positioning.md)), and every
feature must serve [METHODOLOGY.md](../METHODOLOGY.md). Section 1 makes this
split explicit. From every reference we take general ideas only: no code,
assets, logos, colour values, or text are copied. Quotations are kept to single
UI labels, so that the observation can be checked.

The question behind the review: *what makes a person who has never heard of a
"house effect" understand, within seconds, how far a pollster can be trusted?*

---

## 1. sondajeromania.ro (primary design reference)

Pages reviewed: home, `/parlamentare`, `/institute` (pollster directory),
`/institute/<slug>` (pollster page), `/metodologie`. The site opens in dark
mode and offers a light mode through a toggle in the header. Following ADR-0009,
**the light mode is the one we study**; dark mode is out of scope for our
mock-ups.

### 1.1 Design ideas we take (visual design, design system, UX)

| Idea | What we observed (light mode) | Why it works | How we use it |
|---|---|---|---|
| **Calm light canvas** | A cool off-white page background, content on white cards with a large radius, a soft and diffuse shadow, and hairline separators. | Separates content blocks without heavy borders. Feels calm and not like a template. | `--color-bg`, `--color-surface`, `--radius-lg`, `--shadow-1` ([visual-language §2, §5](visual-language.md)). |
| **One sans-serif family, few weights** | A single sans-serif for everything; size and weight carry the hierarchy, not colour. | Highly readable on phones; nothing competes with the numbers. | One UI sans (`--font-sans`), a 7-step type scale. Our own addition: a serif only for the one-sentence finding. |
| **Numbers first, in large type** | Big figures on tiles; full names and units in small muted text underneath or beside. | The reader gets the answer before any chart. | Stat strips (`.stats`) and the grade letter. |
| **Small uppercase "eyebrow" labels** | Short tracked uppercase labels above section titles. | Orients the reader ("where am I, what is this block") without a second heading. | `.eyebrow` on every screen and card. |
| **Compact meta lines** | Bold number + muted label, separated by thin dividers ("77 sondaje · 2017–2026"). | Dense facts stay scannable. | Card meta lines ("3 alegeri analizate · 14 sondaje"). |
| **Quiet sticky header** | White bar, brand on the left, plain text links on the right; the active page is marked by colour/weight. | Navigation is always there but never loud. | `.site-header`; we mark the active page with ink + an underline instead of an accent colour (colour is reserved for data). |
| **Breadcrumbs and directory → detail** | Directory of pollster cards, each opening a pollster page. | Users learn one pattern and reuse it. | Leaderboard → pollster card → detail screens. |
| **One question per block** | Section titles phrased as plain questions ("how precise are the pollsters?"). | A question tells the reader why the block exists. | Every screen states its question; disclosures are titled as questions ("Cum citesc graficul?"). |
| **"How to read this" at the point of use** | A one-sentence reading guide under dense tables and charts. | No trip to a separate page. | `details.disclosure` "Cum citesc…?" under every chart. |
| **Chart captions and an annotated reference line** | A short caption under each chart; the election day is a labelled vertical line. | The chart explains itself. | Timeline: the result tick and the shaded final-window band are labelled directly. |
| **Honest suppression when data is thin** | An interval is not drawn when there are too few data points. | It avoids drawing meaningless precision. | The *principle* drives our insufficient-data states (hatched, no number). |
| **Plain-prose methodology with a worked example** | Short sections, one formula each, a concrete numeric example. | The example makes the formula concrete. | [Cum măsurăm](mockups/methodology.html): sentence → example + diagram → technical details. |
| **Disclosure as a fact on the row** | The sponsor of each poll is shown on its row, without commentary. | Transparency without judgement. | Client/sponsor appears in our data tables and in the transparency score (M-5.3). |

### 1.2 Mechanisms we deliberately don't adopt (different purpose)

These are product features, not design. They serve an aggregator; they do not
serve an investigation of pollster accuracy.

| Mechanism on the reference site | Why we don't adopt it | What we have instead |
|---|---|---|
| **Poll averages as a headline feature** (party tiles with the current average, trend charts as the main view) | We don't tell readers who is ahead. That is the aggregator's job. | A market average exists only as a **reference** for measuring houses: leave-one-house-out, campaign window only (M-3.1, M-3.2). It is never shown as "the current standings". |
| **Seat projections** | Out of scope: they forecast, we audit. | None. |
| **Coalition simulations** (Monte Carlo simulator, majority threshold) | Out of scope. | None. |
| **Accuracy approach**: the mean absolute error of each house's *last poll* per election, a 1–N rank, and a "favored party/candidate" column | A single last poll ignores the campaign; a rank without uncertainty overstates precision; "favored" implies intent (ADR-0003). It also mixes the industry-wide miss into each house's score. | Relative house effect (M-2.5) that removes the shared miss, campaign house effect (M-3.2), significance and intervals (M-4), a grade with a certainty level (M-5), and neutral wording ("overestimated by +3,1 p.p."). |
| **Aggregator-style poll feed** ("latest polls", counters of polls aggregated / institutes monitored as hero stats) | A feed invites horse-race reading; counters signal coverage, not findings. | The home view leads with findings; poll lists appear only as the evidence behind a finding ("Datele: sondajele folosite"). |

### 1.3 Presentation details we do differently

| Observed | Problem for our purpose | Our approach |
|---|---|---|
| Accuracy bars are green for the best house and red for the others. | A traffic light turns small, possibly insignificant differences into a verdict. | Neutral grade badges. Colour encodes direction (over = blue, under = orange), never good/bad. |
| The mean absolute error is written as "±2.0". | "±" reads as a margin of error. | "2,0 p.p. eroare medie"; "±" only for real intervals. |
| English terms in the Romanian UI ("Avg Error", "Delta", "Bias"). | Jargon stops non-experts. | Romanian glossary (T-051); technical names only in "Detalii tehnice". |
| Party colours as the line colours of multi-party charts. | Several party colours are close (red/orange, blue/navy) and collide with the over/under colours. | Party colour only as a small chip next to the label ([visual-language §3.3](visual-language.md)). |
| Ads and pop-ins between and over charts. | Breaks the reading flow and lowers credibility. | No ads inside investigative content (Follow-up for T-050/T-052). |
| Dark mode as the default. | The owner finds dark-first "AI-ish" (ADR-0009). | Light mode is primary; dark mode is an optional token mapping. |

---

## 2. FiveThirtyEight pollster ratings (538, now archived)

The 538 pollster ratings were the best-known public pollster scorecard. Letter
grades were replaced in 2024 by a 0.5–3.0 star rating that combines an
accuracy score ("POLLSCORE") with a 0–10 transparency score. ABC News shut 538
down in March 2025. The ratings are no longer updated, but the methodology
articles remain a useful reference. A successor exists in Nate Silver's
"Silver Bulletin" ratings.

### What works
- **One summary mark, several honest columns.** A single grade or star rating
  for scanning, then separate columns for accuracy, partisan lean (written as
  "R+1.2"/"D+0.8", a direction plus a magnitude), transparency, and the number
  of polls analysed. Readers can stop at the summary or go deeper.
- **The number of polls is shown next to the grade.** Readers can see that a
  grade based on 5 polls is weaker than one based on 500. This is the same idea
  as our certainty level (M-5.2), which we make more explicit.
- **Transparency counts as quality.** Disclosing methods (sample, wording,
  weighting) is part of the score. This matches M-5.3.
- **Directional lean as a signed short code.** "+1.2 toward X" is compact and
  neutral: it states a direction and a size, not a motive.

### What to avoid
- **Jargon in the main view.** "Predictive plus-minus", "POLLSCORE", or
  "mean-reverted bias" mean nothing to a general audience. We keep internal
  metric names in the details layer, after a plain-language label.
- **False precision.** 538 itself moved away from fine-grained letter grades
  (A+, A, A−, …) partly because they implied more precision than the data
  supports. With at most 3 elections per house in the MVP, our ± modifiers
  (M-5.2) should stay hidden until certainty is at least medium.
- **A dense table as the only entry point.** A sortable table of 500 rows suits
  experts, not newcomers. We start from a short list and a card.

---

## 3. Our World in Data (charts and explainers)

### What works
- **Chart titles that state the subject or finding, plus a one-sentence
  subtitle that defines the measure.** The reader learns what is measured
  before reading the axes.
- **Sources and notes under every chart**, and the same chart available as a
  table and as downloadable data. This supports ADR-0003's rule that every
  public claim links to its data.
- **Direct labels at the end of lines** instead of a separate legend, so the
  eye does not travel back and forth.
- **A calm, consistent house style.** Light background, one accent at a time,
  thin gridlines, generous whitespace. Credibility comes from restraint.
- **Layered explainers.** Each one starts with intuition, then the definition,
  then the caveats, then the technical notes.

### What to avoid
- **Many toggles on a single chart** (countries, metrics, time ranges). They
  are powerful, but a casual reader does not know where to start. Our screens
  open with one pre-selected view that answers the screen's question; the
  controls are secondary.

---

## 4. Pew Research Center "short reads" on polling methods

Example: the explainer on the margin of error in election polls.

### What works
- **Concrete numeric examples instead of formulas.** "±3 for each candidate
  means about ±6 for the gap between two candidates" shows how much noise to
  expect. Our "how we measure this" page uses the same technique, with one
  worked example per concept.
- **The questions readers actually ask, as section headings.**
- **An explicit statement of what the numbers cannot tell you.** This
  inspires our "Ce nu spunem" ("what we do not claim") box (ADR-0003).

### What to avoid
- **Long text blocks without a visual.** We pair every concept with one small
  diagram.

---

## Synthesis: principles adopted

1. **Answer first.** Each screen opens with a one-sentence, plain-Romanian
   headline that states the finding, with a magnitude and an uncertainty.
2. **One screen, one question.** The question is written on the screen (see
   [storyboard](storyboard.md)).
3. **One visual, then details on demand.** Progressive disclosure through
   "Cum citesc…?", "Detalii", "Datele" and "Detalii tehnice" layers.
4. **Colour encodes data, never verdicts.** No traffic lights. Over/under is
   blue/orange; party identity is a small chip next to the label; pollsters
   are never colour-coded (ink + shape + label).
5. **Uncertainty is part of the picture.** Intervals, hollow marks and "≈" for
   "cannot be told apart from zero", dashed outlines for low certainty, and
   hatching for insufficient data. Each state has its own visual.
6. **Show the comparison.** We separate the house's own deviation from the
   industry-wide miss. This is our main difference from existing accuracy tables.
7. **Neutral wording.** Every statement describes a measured deviation; none
   describes a motive. Every screen carries a "Ce nu spunem" box.
8. **Restraint, light-first.** A cool off-white page, white cards, hairlines,
   one sans-serif family for the UI, a serif reserved for the headline finding,
   tabular figures. No gradients, glass effects, or decorative icons.
9. **Design from the reference, purpose from the methodology.** Visual and UX
   patterns may come from sondajeromania.ro; features come only from
   METHODOLOGY.md (ADR-0009).

Details: [visual-language.md](visual-language.md).
