# Design references

**Task:** T-031 · **Reviewed:** 2026-11-22 · **Related:** ADR-0008, I-018

This review covers four references that explain polls or pollster quality to
non-experts. For each one it records what works for a general audience and
why, and what this project should avoid. Following ADR-0008 and I-018, we take
**general ideas only**. No code, assets, logos, colours, or text are copied.
Quotations are kept to single UI labels, so that the observation can be
checked.

The question behind the review: *what makes a person who has never heard of a
"house effect" understand, within seconds, how far a pollster can be trusted?*

---

## 1. sondajeromania.ro (primary reference)

Pages reviewed: home, `/parlamentare` (averages, trends, polls table, accuracy
section), `/institute` (pollster directory), `/institute/<slug>` (pollster
page), `/metodologie`.

It is a poll **aggregator** (see [PLAN: Related work](../PLAN.md#related-work)).
The owner considers it the reference for clarity and tone.

### What works for non-experts, and why

| Pattern | Why it works |
|---|---|
| **Numbers first, in large type.** Each party gets a tile with its share in big figures, the full party name, and a small change indicator. | The reader gets the answer before any chart. The number is the headline. |
| **One question per block.** The accuracy block is titled as a plain question ("how precise are the pollsters?") with a short ranked bar list underneath. | A question as a title tells the reader why the block exists. The bar list can be read in one glance. |
| **A "how to read this" note under the accuracy table.** One sentence explains what the header row and the cells mean. | Readers are told how to read a dense table at the point of use, not on a separate page. |
| **Sponsor disclosure on every poll row** ("commissioned by …" or "undeclared client"). Documented political affiliations are marked with a small info marker. | Transparency is shown as a fact on the row, without commentary. The methodology page says plainly that an affiliation is not a quality judgement. |
| **Intervals on averages, and suppression when data is thin.** The averages chart shows a 95% range, and the range is hidden when a party has fewer than 3 polls. | It is an honest default: no interval is drawn when it would be meaningless. We reuse the *principle* for our insufficient-data states. |
| **Plain-prose methodology page.** Short sections ("how are averages calculated?"), each with one formula and a worked example (e.g. 30% official vs. 32% polled means 2 points of error). | The worked example makes the formula concrete. Every section is short enough to read on a phone. |
| **Pollster page = history + accuracy.** Activity span, number of polls per election type, the error per past election as a bar, then the full poll table. | It answers "who is this pollster and how did they do?" in one scroll. |
| **Calm visual tone.** Dark neutral background, a single sans-serif family, thin rules, few decorations, direct labels. | Nothing competes with the data. |

### What to avoid (and what we do instead)

| Observed | Problem for our purpose | Our approach |
|---|---|---|
| The accuracy table labels a column "favored party" (the party a house overestimated most). | "Favored" suggests intent. ADR-0003 forbids implying intent. | "Overestimated most: X (+2.8 pp)" with an interval. |
| Accuracy bars are green for the best house and red for all the others, so an error of 3.4 and one of 4.0 look equally "bad". | A traffic-light colour turns small, possibly insignificant differences into a verdict. | Neutral bars. The colour encodes direction (over/under), never good/bad. Differences that are within the uncertainty are drawn as such. |
| Houses are ranked 1–5 on a single election's final poll, without uncertainty. | A rank suggests a precision that one poll cannot give. | Grades with a certainty level. No ordinal ranks inside a grade group (see [leaderboard](mockups/leaderboard.html)). |
| The "last poll before the election" can be several weeks old (one row has fieldwork about 7 weeks before the vote). | Opinion moves; an old poll is penalised for real change. | The accuracy window (M-1.3, 21 days by default) is stated on the chart. A house without a poll in the window is shown as "no final poll", not as inaccurate. |
| The mean absolute error is written as "±2.0". | "±" reads as a margin of error, which is a different concept. | Write "2.0 pp average error". Use "±" only for real intervals. |
| English terms mixed into the Romanian UI ("Avg Error", "Delta", "Bias"). | Jargon stops non-experts. | A Romanian glossary (T-051). Technical terms appear only in the "details" layer. |
| Some party colours have low contrast on the dark background (a navy party colour on near-black). | It fails WCAG contrast. Colour-blind readers lose the party identity. | A light background. Party colours are checked for ≥ 4.5:1 contrast and are always paired with a text label. |
| Ads and pop-ins appear between, and on top of, charts. | They break the reading flow and lower credibility. | No ads inside the investigative content (Follow-up for T-050/T-052). |

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
   "how to read this", "details", "data", and "methodology" layers.
4. **Colour encodes data, never verdicts.** No traffic lights. Over/under is
   blue/orange; party identity is a small chip next to the label.
5. **Uncertainty is part of the picture.** Intervals, hollow marks for
   "cannot be told apart from zero", dashed outlines for low certainty, and a
   hatched area for insufficient data. Each state has its own visual.
6. **Show the comparison.** We separate the house's own deviation from the
   industry-wide miss. This is our main difference from existing accuracy tables.
7. **Neutral wording.** Every statement describes a measured deviation; none
   describes a motive.
8. **Restraint.** A light paper-like background, serif headlines, tabular
   figures, thin rules. No gradients, glass effects, or decorative icons.

Details: [visual-language.md](visual-language.md).
