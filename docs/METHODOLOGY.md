# Methodology Specification

**Version:** 0.1 (draft) · **Status:** working default, to be revised as tasks are delivered

This document is the single source of truth for every calculation. Section IDs
(`M-x.y`) are **stable**: never renumber them. Deprecated sections are kept and
marked as deprecated. Code cites these IDs in docstrings.

## Notation

| Symbol | Meaning |
|---|---|
| `s_j` | Poll share for party/candidate `j`, normalized (M-1.1), in [0,1] |
| `r_j` | Actual result share for `j`, in [0,1] |
| `k` | Number of parties/candidates compared in an election |
| `n` | Poll sample size |
| `h` | House (pollster), `E` election, `t` fieldwork end date |

All errors are expressed in **percentage points (pp)** unless stated otherwise.

---

## M-1 Data preparation

Implemented by `sondaje.prep` (T-020): one call turns the canonical CSVs into
one row per (poll, compared entity), plus one row per poll with its
eligibility flags, plus a log of every adjustment. Every poll is kept, including
the ones excluded from the metrics, so that they can be shown. The tunable
values named below (`share_base_priority`, `lt_fraction`, …) live in one
configuration object (`sondaje.config.MethodologyConfig`).

### M-1.1 Normalization to valid votes
Polls report undecided/refuse/other, but results do not. Remove those categories
and rescale:
`s_j = raw_j / Σ_i raw_i` over named parties/candidates (+ "others" if the
result also contains an "others" bucket built the same way).

- **Vote options** are the options of type `party`, `alliance`, `candidate`,
  `independent` (named) and `other` ("others"). Every other `option_type`
  (undecided, non-response, would not vote, none, blank or invalid, other
  non-vote answers) is removed.
- **Share base (OI-1).** When a poll publishes several share bases, the first
  one in this order that has at least one vote option is used:
  `expressed_option`, `all_respondents` (normalized), `likely_voters`,
  `other_subset` (`share_base_priority`). `expressed_option` is the pollster's
  own figure over valid answers, the one the public sees. `all_respondents`
  describes the same respondents, so after normalization it differs only by
  rounding. `likely_voters` and `other_subset` add a filter that is described
  only in `notes` and differs between houses, so they are used only when
  nothing else is published.
- **Values published as "<x" (OI-2)** (`share_qualifier = lt`) enter as
  `x · lt_fraction`, default `lt_fraction = 0.5` (that is, x/2). The poll and
  the affected row are flagged (`has_lt`), and each value is logged. T-025 tests
  `lt_fraction` = 0 and 1 as sensitivity.
- **Partial toplines.** When `topline_coverage = partial` and the base is
  `expressed_option`, the unpublished remainder (100 minus the sum of the
  published vote shares, when positive) is added to "others" before
  normalization, and the adjustment is logged. Spreading it over the published
  options would inflate them. With any other base the remainder may hold
  non-vote answers, so the published options are normalized as they are.
- **Sample size `n` (OI-5)**, used from M-3.4 and M-4.1 onward, is the number of
  respondents behind the normalized shares: `sample_size_expressed` when
  published; otherwise `sample_size` × the share of all respondents who named
  a vote option, when the poll publishes an `all_respondents` base ("<x"
  values as above); otherwise `sample_size`, which overstates `n` (so it
  understates sampling error). The method used is stored per poll
  (`n_method`). `n` is empty when no sample size is published.

### M-1.2 Comparison set
Compare only entities present in both the poll and the result. Entities below a
threshold (default 1% in the result) are merged into "others". This prevents
small-party noise from dominating the log-odds metrics.

- The threshold applies to the result share in the poll's target scope
  (M-1.4). A contestant exactly at the threshold is kept.
- "Others" is built the same way on both sides, so both sides sum to 1. In the
  **result**, it holds every contestant that is not compared on its own: those
  below the threshold, and those the poll does not name. In the **poll**, it
  holds the `other` options, the named contestants below the threshold, and
  the partial-topline remainder (M-1.1). A poll without an `other` option
  therefore has `s_others = 0`.
- The "others" row is part of the comparison (and counts in `k`) whenever
  either side is above zero. Each merge into "others" is logged.

### M-1.3 Accuracy window and recency weight
- Only polls with fieldwork **ending ≤ 28 days** before election day are used for
  accuracy metrics (parameter `window_days`, default 28; owner decision
  2026-11-22, [ADR-0012](decisions/0012-mvp-pollsters.md); previously 21).
  `days_before_election` = election day − `fieldwork_end`, in days; a poll
  exactly 28 days out is inside the window.
- Weight: `w = exp(−days_before_election / τ)`, `τ = 7` by default.
- The "final poll" of a house is its latest poll inside the window that is
  eligible under M-1.7. "Latest" means the latest `fieldwork_end`; ties go to
  the later `published_date`, then to the larger `poll_id`.
- **Scenarios (OI-3).** A poll with `headline = false` (a scenario or a second
  question of the same survey) is excluded from every metric, so that a survey
  counts once. It is kept, prepared, and shown for transparency.
- **No fieldwork end (OI-4).** A poll without a published `fieldwork_end` has
  no date `t`, so it is excluded from every metric: all of them are windowed
  (this window, and the campaign window of M-3). `fieldwork_start` and
  `published_date` are not used as a substitute. The poll is kept and shown, and
  the missing dates lower its transparency score (M-5.3).

### M-1.4 Domestic vs. total result
Most Romanian polls sample the resident population only. The default comparison
target is the **domestic (in-country) result**. A pollster that explicitly
includes the diaspora is compared to the total. The target used is stored per
poll.

### M-1.5 Alliances, withdrawals, rounds
- An alliance mapping table maps poll entities to result entities (e.g. joint
  lists).
- A candidate who withdraws after the poll, or who is not on the final ballot,
  is excluded, and the remaining shares are renormalized. The adjustment is
  logged.
- Each presidential round is a separate election `E`.
- A lean toward a party in presidential elections is attributed through the
  candidate → supporting-party mapping (I-016). When a candidate has several
  supporting parties, the error is attributed to the candidate only, until a
  rule is specified.
- **Parties on another party's list** (`ran_on_list_of` in the entity map,
  DATA_MODEL 1.1): a party that filed no lists of its own, and whose
  candidates ran on another contestant's lists under a party-level
  arrangement, is treated like an alliance member. Its poll share is added to
  the host contestant's share before normalization (M-1.1). The adjustment is
  logged.
- **Poll shares for entities with no result entity** (`not_registered`, for
  example ADU in 2024): only that share is dropped, and the remaining shares
  are renormalized. The poll is kept, and the adjustment is logged. (Owner
  decision, 2026-11-22.)
- The `entity_map` relations apply to every poll of the election, whatever
  their `effective_date`: the poll is compared with the ballot as it was on
  election day. Shares that map to the same contestant are added.
- A candidate's "supporting party" is the party or alliance that nominated or
  endorsed the candidate (`candidate_support.csv`). It is recorded only when
  there is exactly one; with none or several, the error stays with the
  candidate.

### M-1.6 Independence unit
Polls from the same house for the same election are **not independent**. The
statistical unit for cross-election inference is the pair `(house, election)`
(`unit_id` in the prepared tables).

### M-1.7 Publication timing
A poll whose first publication (`published_date`) is **on or after election
day** is shown to users, with an explicit notice that it was published after
the vote, but it is **excluded from every calculation**: errors (M-2), market
average and campaign metrics (M-3), significance (M-4), and the trust score
(M-5). It can never be a house's final poll (M-1.3); the final poll is the
latest poll published before election day. Owner decision 2026-11-22
([ADR-0012](decisions/0012-mvp-pollsters.md)).

---

## M-2 Accuracy & error metrics

### M-2.1 Signed error
`e_j = 100 · (s_j − r_j)`. Positive values mean overestimation; negative values
mean underestimation.

### M-2.2 Mean absolute error
`MAE = (1/k) · Σ_j |e_j|`

### M-2.3 Total error ("misallocated share")
`TE = ½ · Σ_j |e_j|`

### M-2.4 Log-odds accuracy (Arzheimer & Evans, 2014)
`A'_j = ln[ (s_j/(1−s_j)) / (r_j/(1−r_j)) ]`, `B = mean_j |A'_j|`.
On this scale, errors on small and large parties are comparable.

### M-2.5 Relative house effect (final polls)
`he_{h,j,E} = e_{h,j,E} − ē_{·,j,E}`, where `ē_{·,j,E}` is the recency-weighted
mean signed error of **all houses** for `j` at election `E`. This separates the
house's own error from an industry-wide miss. In the MVP, "all houses" means the
houses in the dataset. Whether to use a broader reference market is open (I-013).

### M-2.6 Relative accuracy
`RA_{h,E} = MAE_{h,E} − median_h'(MAE_{h',E})`. Negative values mean the house
was better than the typical pollster.

---

## M-3 Campaign-long behaviour

### M-3.1 Market average
For each `j`, a smoothed curve over all polls (LOESS or a weighted rolling
mean; method recorded in output) as a function of `t`.

### M-3.2 Campaign house effect
`che_{h,j,E} = weighted mean over t of ( s_{h,j}(t) − market_j(t) )`, computed
over the full campaign window (default: 120 days before the election). The
market average used for each poll **excludes that house's own polls**
(leave-one-house-out).

### M-3.3 Convergence flag
The flag is raised when `|che|` over the early campaign is large and the gap
closes sharply in the final window:
`|che_early| ≥ c1` and `|he_final_vs_market| ≤ c2·|che_early|`.
Defaults: `c1 = 2 pp`, `c2 = 0.33`. Both are to be calibrated (T-042).

### M-3.4 Herding
`ratio = Var_observed(s_{h,j}) / Var_expected`, where
`Var_expected = mean( s(1−s)/n · deff )` plus the variance of the market trend
over the same period. A `ratio` well below 1 (default flag: < 0.5, minimum 5
polls) means the house's polls are more stable than sampling theory allows.

---

## M-4 Statistical significance

### M-4.1 Single-poll sampling error
`SE_j = sqrt( r_j(1−r_j) / n ) · sqrt(deff)`, `deff = 1.5` by default.
`z_j = (s_j − r_j) / SE_j`.

### M-4.2 Sign test across elections
For a fixed `(h, j)`, count the elections where `he > 0`. Apply a binomial test
against p = 0.5.

### M-4.3 t-test on house effects
One-sample t-test of `he_{h,j,E}` across elections `E` (unit: M-1.6).

### M-4.4 Hierarchical Bayesian model (target model)
```
e_{i,j}   = b_{h[i],j} + γ_{E[i],j} + ε_i,     ε_i ~ N(0, σ_i²),  σ_i from M-4.1
b_{h,j}   ~ N(0, τ_b²)          house bias, partially pooled
γ_{E,j}   ~ N(0, τ_γ²)          shared election-level miss
```
Report the posterior mean of `b`, its 90% credible interval, and
`P(b > 0)` / `P(b < 0)`.

---

## M-5 Trust score

### M-5.1 Components
Each component is converted to a 0–100 percentile among the houses rated.

| ID | Component | Default weight | Source |
|---|---|---|---|
| M-5.1a | Relative accuracy | 35% | M-2.6, recency-weighted across elections |
| M-5.1b | Systematic bias | 30% | max_j \|b_{h,j}\| × P(sign), from M-4.4 |
| M-5.1c | Transparency | 15% | Checklist in M-5.3 |
| M-5.1d | Behaviour | 10% | Penalties from M-3.3, M-3.4, and party-commissioned polls |
| M-5.1e | Track record | 10% | Number of elections covered |

### M-5.2 Shrinkage and certainty
`score = (N · raw + N0 · 50) / (N + N0)`, where `N` is the number of elections
covered and `N0 = 3`.
The certainty level is *low* when N < 3, *medium* when 3 ≤ N < 6, and *high*
when N ≥ 6.
Grades: A ≥ 85, B ≥ 70, C ≥ 55, D ≥ 40, F < 40 (± modifiers, defined later).
**No grade is given when N < 3** ("no grade yet"); the findings and their
uncertainty are still shown. While every pollster has N ≤ 3 (the MVP), grades
are labelled **provisional**. With N = 3 and N0 = 3 the maximum score is 75,
so grade A cannot be reached yet ([ADR-0010](decisions/0010-grades-and-card-framing.md)).

### M-5.3 Transparency checklist
Each item scores 1 if published for the poll: sample size, fieldwork dates,
mode (CATI/CAWI/CAPI/mixed), exact question wording, weighting description,
margin of error, client/sponsor. The house score is the mean over its polls.
The client/sponsor item scores 1 only when the **pollster itself** discloses
the client (in its own material for the poll, DATA_MODEL §6.11
`sponsor_source = pollster`). A client named only by the media or by the
client is recorded (POLL_INGESTION §0.1) but scores 0 here. M-5.1d uses every
recorded client, whoever named it.

### M-5.4 Weight calibration
The weights must be validated out-of-sample: score computed on elections before
`E`, compared with accuracy at `E`. Until then, the defaults above apply.

---

## M-6 Adjusted poll (planned)
For a new poll, the adjusted share is `s_adj,j = s_j − b̂_{h,j}`, and its
interval combines the M-4.1 sampling error with the posterior uncertainty of
`b`. Shown only when the certainty level is medium or higher.

---

## Open specification issues

None are open. OI-1…OI-5, raised by T-001, were resolved in T-020: OI-1, OI-2
and OI-5 in M-1.1, OI-3 and OI-4 in M-1.3. The options and reasons are in the
T-020 task Log.

---

## Tunable parameters

| Parameter | Default | Section | Calibrated by |
|---|---|---|---|
| `window_days` | 28 | M-1.3 | T-025 sensitivity analysis (incl. 21 and 35 days) |
| `tau` | 7 | M-1.3 | T-025 |
| `small_party_threshold` | 1% | M-1.2 | T-025 |
| `campaign_days` | 120 | M-3.2 | T-023 |
| `deff` | 1.5 | M-4.1 | literature / T-040 |
| `c1`, `c2` | 2 pp, 0.33 | M-3.3 | T-042 |
| `herding_flag` | 0.5 | M-3.4 | T-041 |
| `N0` | 3 | M-5.2 | T-043 |
| Trust weights | see M-5.1 | M-5.1 | T-043 |

## References
- Arzheimer, K. & Evans, J. (2014). *A new multinomial accuracy measure for
  polling bias.* Political Analysis 22(1).
- Silver, N. / FiveThirtyEight. *Pollster Ratings methodology.*
- Jackman, S. (2005). *Pooling the polls over an election campaign.*
  Australian Journal of Political Science 40(4).
