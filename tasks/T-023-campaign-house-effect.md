---
id: T-023
title: Market average and campaign house effect
status: review
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
- [x] A synthetic house with a constant +3 pp offset over a moving trend is
      recovered within ±0.5 pp.
- [x] Leave-one-house-out is verified by a test.
- [x] The smoothing method and its parameters are recorded in METHODOLOGY.

## Follow-ups
- **Move the M-3 parameters into `MethodologyConfig`.** They live in
  `sondaje.metrics.market.MarketConfig` for now, so that this task does not
  edit `config.py` while T-021 runs in parallel. T-025 needs them in one place.
- **Declare `numpy` as a direct dependency.** `market.py` imports numpy, which
  is installed through pandas. It was not added with `uv add` to avoid a
  `pyproject.toml`/`uv.lock` conflict with T-021.
- **T-025 sensitivity:** `bandwidth_days` 7/14/21, `max_gap_days`,
  `regime_min_dropped`, and "others" in or out of M-3.
- **Owner decisions** listed under *Outcome* (D-1…D-5); the coordinator turns
  them into an ADR or METHODOLOGY changes if the owner changes a default.
- **Scope alignment (M-1.4):** AtlasIntel publishes `total`-scope polls in
  2025 and the other houses `domestic`. M-3 pools them as published, so part
  of an AtlasIntel campaign deviation may come from the diaspora. A possible
  fix (shift each `total` poll by `r_domestic − r_total`) uses result data in a
  campaign metric and needs an owner decision.
- **I-013:** a reference built from more houses would make `che` less
  dependent on the other three MVP houses.
- **T-042** (convergence) can use `house_deviations()` directly: it returns
  each poll's deviation from the leave-one-house-out market, with dates.

## Log
- 2026-11-28: Task locked (branch `task/T-023-campaign-house-effect`,
  worktree `sondaje-wt/T-023`).
- 2026-11-28: **Input.** `campaign_rows()` takes `prepare().rows` and keeps
  `eligible` rows with `days_before ≤ campaign_days`. No M-1 rule is
  recomputed. `y = 100·s`, `var = 100²·s(1−s)/n·deff` (M-4.1, `n` from OI-5).
  A poll that does not name `j` has no row for `j` and is not used for `j`.
- 2026-11-28: **Smoothing method (M-3.1). Options considered:**
  1. *Weighted rolling mean* (box window): simple, but it jumps when a poll
     enters or leaves the window and lags at both ends of the campaign.
  2. *LOESS with a span in number of polls:* the span changes meaning when one
     house is left out, and with 1–5 polls per house in some elections it
     covers the whole campaign.
  3. *Kernel smoother over all polls (local constant or local linear,
     bandwidth in days):* stable with irregular dates. But the level at a
     date depends on which houses polled near that date, and the most frequent
     house (Sociopol, 12 of 22 round-1 polls) dominates the reference.
  4. *Trend plus house offsets* (partially linear model, as in Jackman 2005
     but with a kernel trend): each poll = trend + its house's offset. The
     offsets sum to zero over houses, so the market is the average house.
  5. *Full state-space / Bayesian model* (random-walk trend, joint house
     effects): the best in principle, but heavier (PyMC, T-040). Leave-one-out
     inference with it is costly, and it would duplicate M-4.4.

  **Choice: 4, in two linear steps.** (a) The house offsets are fitted by
  backfitting with a Gaussian kernel mean as the trend, solved exactly as a
  linear system, not iterated. (b) The curve is a local linear Gaussian-kernel
  smoother of the house-adjusted polls, with a 14-day bandwidth. **Why:** with
  4 houses and uneven frequencies, an equal-weight average house is a fairer
  reference than "whoever polled most". The offsets remove the house mix from
  the trend, so a trend is not invented when houses take turns. I first tried
  a local linear trend in step (a) as well. With houses that have one poll
  each (round 2, the parliamentary election) the slope is then not
  identified, and the solver turned the differences between houses into a
  trend. Example: for AtlasIntel round 2 the reference market became a line
  through Verifield (12 days out, Simion 55.4), CURS and Sociopol, and
  AtlasIntel's effect was −1.8 pp instead of −3.7 pp. A kernel mean has no slope, so it
  attributes such differences to the houses. A trend is then learned only
  from changes within houses and from houses polling at the same time. Local
  linear in step (b) avoids the lag of a kernel mean in the last days, which
  matters for T-042. **Effect:** on synthetic data the method is
  linear in the poll values. This gives an exact sampling SE (checked
  numerically by moving one poll at a time), exact antisymmetry in
  head-to-head rounds (`che_ion = −che_maria`, markets sum to 100), and an
  exact leave-one-house-out check.
- 2026-11-28: **Parameters.** `bandwidth_days = 14`: polls come every 1–3
  weeks per house; 14 days follows changes over about a month without
  following single polls. `max_gap_days = 28` (2 bandwidths, kernel weight
  0.14): beyond that, a "market" would be a guess, so a house alone in a
  period is not evaluated there. `max_extrapolation_days = 7`: a short
  extrapolation of the trend is allowed (Verifield's round-2 poll is 5 days
  before the next poll), a longer one is not. `campaign_days = 120` is kept:
  every MVP poll inside it was collected for M-3 (ADR-0012), and T-025 tests
  others. `min_polls = 3` for status `ok`.
- 2026-11-28: **Ballot regimes.** In pres-2025-r1, the polls before 11 March
  2025 included Călin Georgescu (33–50% dropped by M-1.5). After M-1.5
  renormalization, Simion goes from 2–16% before the change to 32–37% after it. A smoother
  across that jump would give large, artificial deviations to the houses
  polling near it. The regime is taken from data, not from a date:
  `prepare().adjustments` rows `M-1.5` / `excluded|withdrawn` with
  `share_raw ≥ 10 pp`. In the real data, this gives 7 round-1 polls in the
  regime `with:calin-georgescu` and nothing else. Sosoacă (2–4 pp) stays below
  the threshold, and the Gavrilă scenario is not a headline poll.
  Alternatives: a date-based break (needs `effective_date` facts in code), or
  dropping the pre-change polls (loses Verifield's and CURS's only early
  round-1 polls).
- 2026-11-28: **Uncertainty.** `se = max(se_sampling, se_spread)`.
  `se_sampling` alone assumes the deviation is constant and understates the
  error when it varies over the campaign. `se_spread` alone is unstable with 2
  polls and undefined with 1. The 90% interval matches M-4.4. A simulation
  with 200 seeds (4 houses, 20 polls each, curved trend, n = 3000) gave a
  mean error of −0.03 pp, an SD of 0.27 pp, and a 90% interval coverage of
  0.88. Correlation between polls of the same house beyond sampling (M-1.6)
  is not modelled here; it is covered by the cross-election unit in M-4.
- 2026-11-28: **Tests** (`tests/test_metrics_market.py`, 25 tests). A
  constant +3 pp offset with reference offsets +1/−1/0: linear trend 2.9999,
  curved trend 2.985, curved + sampling noise 2.958 (90% interval
  [2.52, 3.40]). Leave-one-house-out: the market at a house's polls equals
  the market fitted without that house; +20 pp on the house's polls leaves
  its reference unchanged and moves `che` by exactly +20. Edge cases: a house
  alone in a period, an entity polled by one house only, three single-poll
  houses, round-2 head-to-head, regimes, the sampling SE against numeric
  gradients, and an integration test through `prepare()` and the CLI.
- 2026-11-28: **Dependencies.** None added. numpy comes with pandas (see
  Follow-ups). The CLI command `sondaje market` is registered in `cli.py` on
  its own line.
- 2026-11-28: **Real-data smoke test** (`uv run sondaje market`): 36
  eligible polls, all inside the 120-day windows. Results are under
  *Outcome*. Status `ok` is reached only in round 1 (AtlasIntel, Sociopol,
  CURS) and for CURS in the parliamentary election. Every round-2 estimate
  and every Verifield estimate is `few_polls`.

## Outcome
**Done.** `src/sondaje/metrics/market.py` implements M-3.1 and M-3.2:
`campaign_rows`, `ballot_regimes`, `smoother_weights`, `market_curve`,
`house_deviations`, `campaign_house_effects`, `analyze`, and the CLI command
`sondaje market [--data-dir] [--output DIR]`. The CLI writes `campaign.csv`,
`market.csv`, `deviations.csv`, and `effects.csv`. METHODOLOGY M-3.1/M-3.2
and the M-3 tunable-parameter rows are updated.

Key commits: `T-023: market average and campaign house effect (M-3.1,
M-3.2)`; `T-023: record the M-3.1 smoothing method and the M-3.2 estimator in
METHODOLOGY`.

**Owner decisions (recommended default → consequence):**
- **D-1 Reference = equal-weight average of the other houses** (recommended).
  The alternative is to weight by number of polls. With equal weights,
  Sociopol's 12 round-1 polls count as one house. With poll weights,
  Sociopol would set the market for everyone else.
- **D-2 Ballot regimes from M-1.5 drops of 10 pp or more** (recommended). The
  alternative is one curve across the change. Splitting gives Verifield's and
  CURS's early round-1 polls a fair reference. Without the split, the
  Georgescu jump would show up as house effects.
- **D-3 Keep "others" in M-3, labelled** (recommended). The alternative is to
  leave it out of M-3. Its deviation mixes measurement with how many options
  a house names (for example, AtlasIntel parliamentary −6.3 pp, because it
  names 12 parties).
- **D-4 Pool `domestic` and `total` polls as published** (recommended for
  now). The alternative is to align the scopes (see Follow-ups). Part of
  AtlasIntel's 2025 deviations may come from the diaspora.
- **D-5 Show `few_polls` estimates with their interval** (recommended). The
  alternative is to hide them. Showing keeps Verifield (a campaign house,
  ADR-0012) visible; the wide intervals carry the uncertainty.

**Known limitations:** the uncertainty does not include the choice of
reference houses (I-013). Correlation within a house beyond sampling error is
not modelled. With one or two polls, `che` is close to a single-poll
comparison.