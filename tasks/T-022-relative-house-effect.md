---
id: T-022
title: Relative house effect and relative accuracy
status: review
phase: 2
depends_on: [T-021]
owner: github-copilot-cli
branch: task/T-022-relative-house-effect
methodology: [M-2.5, M-2.6, M-2.8]
created: 2026-11-22
updated: 2026-11-28
---

## Goal
For each (house, election, entity), the error relative to the market, and for
each (house, election), the accuracy relative to the median house.

## Context
This is the core of I-002: it separates house-specific lean from
industry-wide misses.

## Scope
**In:**
- `src/sondaje/metrics/` and its tests
- **Shared file allowed** (coordinator's assignment, 2026-11-28):
  `docs/METHODOLOGY.md` sections M-2.5 and M-2.6, plus the conventions they
  need (new M-2.8, the cross-reference in M-2.7, one row of "Tunable
  parameters")

**Out:** significance testing (T-024); the campaign market (T-023, M-3).

## Acceptance criteria
- [x] If every house has the same error, all house effects are 0 (test).
- [x] A synthetic house with a +3 pp offset is recovered exactly (test).
- [x] The output tables have documented columns.

## Follow-ups
- **Owner decisions** (recorded in M-2.8, defaults implemented): (1) common
  comparison set per election; (2) leave-one-house-out reference for `he` and
  `RA`; (3) recency weights for the other houses' market error, equal weights
  as an option; (4) `RA` against the unweighted median of the other houses.
- **T-025:** add `weighting` = `equal` to the sensitivity grid. On real data
  it changes some house effects by several pp (`parl-2024-cd`, Sociopol on
  PSD: +8.22 with recency weights, +3.30 with equal weights), because CURS's
  final poll (26 days out) barely counts with recency weights.
- **T-025 / owner:** a final poll 24–26 days before the vote (CURS in
  `parl-2024-cd` and `pres-2025-r1`) carries the opinion movement after its
  fieldwork in its own `he` and `RA`. Whether to compare houses only on
  same-period polls is a methodology question beyond M-2.5.
- **T-043 (M-5.1a):** aggregating `RA` across elections. `k_common` differs
  between elections (7, 6, 2 in the MVP), and `RA` in a two-candidate round
  is in a larger range (−5 to +3.4 pp against about ±1 pp). Decide whether to
  aggregate `RA`, `RA` on `TE`, or a rank, before the trust score.
- **T-024 / T-040:** `he` with only two to four houses is a thin reference
  (I-013); with two houses the effects are mirror images. `house_effects`
  carries `supporting_party_id` for the party-level lean of I-016.
- **T-042 (M-3.3):** `he_final_vs_market` in M-3.3 should say whether it is
  the M-2.5 `he` (final polls, common set) or the M-3 campaign market.
- **Coordinator:** `cli.py` gets one import and one list entry for the new
  `relative` command; T-023 may touch the same lines (trivial conflict).

## Log
- 2026-11-28: input is `compute_errors()` output only (`final_entities`,
  M-2.1 `e`). Nothing from M-1 or M-2.1–M-2.4 is recomputed; the common
  "others" sums existing rows.
- 2026-11-28: **comparison set** (the T-021 follow-up). Real data, finals of
  `parl-2024-cd`: `k` = 12 (AtlasIntel), 8 (CURS), 7 (Sociopol); "others"
  holds 3.2%, 7% and 11% of the poll. Options: (a) own sets; (b) per entity,
  the houses that name it, without "others"; (c) common set per election
  (entities every house names + one common "others"); (d) `TE` on own sets.
  Chose (c): every house is measured on the same entities and "others" means
  the same thing. (b) builds each entity's market from a different subset of
  houses and cannot place an entity a house rolls into "others"; (d) still
  depends on merging, since merged errors of opposite sign cancel. Effect on
  `parl-2024-cd` `MAE`: AtlasIntel 2.02 → 3.23, CURS 3.92 → 4.20, Sociopol
  3.27 → 3.27; with own sets and a leave-one-out median, Sociopol's `RA` would
  be +0.30, with the common set it is −0.45. FD, POT, SENS, REPER, DREPT are
  merged and get no house effect. Presidential rounds: nothing merged.
- 2026-11-28: **leave one house out.** M-2.5 v0.1 said "all houses" (the house
  included). With the house in its reference, a +3 pp offset comes back as
  3 · (1 − w_h / Σw), not 3, which fails the acceptance criterion; with two
  equal houses it is halved. Chose the other houses only, for `he` and `RA`,
  as in M-3.2. Formulas of M-2.5 and M-2.6 updated.
- 2026-11-28: **weights.** M-2.5 specifies recency weights: kept as default
  (`w` of each other house's final poll, M-1.3). Added `weighting="equal"` as
  a sensitivity option (CLI `--weighting equal`), not in `MethodologyConfig`
  (outside the scope).
- 2026-11-28: **edge cases.** One house in an election: rows are kept, `he`
  and `RA` are NaN, `n_ref_houses` = 0. Two houses: mirror-image effects,
  stated in the summary. Verifield (final poll in round 2 only): absent from
  the other elections as subject and reference. Even number of other houses:
  the median is the mean of the two middle values (numpy). Common "others" is
  kept when any house has a non-zero share on either side, so `k_common` is
  the same for every house of an election; a two-candidate round has none.
- 2026-11-28: different targets (AtlasIntel compared with the total result in
  `pres-2025-r1`, the others with the domestic one, M-1.4) are compared through
  errors, each against its own target. Recorded in M-2.8.
- 2026-11-28: new section M-2.8 (new ID, nothing renumbered); M-2.7 now points
  to it; one row added to "Tunable parameters".
- 2026-11-28: output wording is neutral (ADR-0003); the summary states that
  the results are descriptive, with no significance test yet (T-024).
- 2026-11-28: rebased on `main` after T-023 merged. Conflicts in `cli.py`
  (both `market` and `relative` registrations kept) and in METHODOLOGY's
  "Tunable parameters" (T-023's rows kept, the `weighting` row added). Checks
  rerun; the real-data results are unchanged.

## Outcome
`sondaje.metrics.relative` computes, from `compute_errors()` output:
- `comparison_sets`: per election, the houses with a final poll, the common
  entities, the merged entities, `k_common` (M-2.8).
- `common_entity_errors`: each final poll's errors on the common set.
- `house_effects`: per (house, election, common entity) `e`, `market_e`
  (leave-one-house-out, recency-weighted), `he`, `n_ref_houses` (M-2.5).
- `relative_accuracy`: per (house, election) `mae_common`, `te_common`,
  `ref_mae` (median of the other houses), `ra`, `n_ref_houses` (M-2.6).
- `compute_relative` returns all of them in `RelativeMetrics`, whose
  docstring documents every column.
- `sondaje relative [--output DIR] [--weighting recency|equal]` prints the
  tables per election and writes `comparison_sets.csv`, `house_effects.csv`,
  `relative_accuracy.csv`.

Key commits: see `git log task/T-022-relative-house-effect`. Tests:
`tests/test_metrics_relative.py` (22 tests: the two acceptance criteria,
weighted and equal markets, two houses, one house, a house in one election
only, odd and even medians, the common set and its "others", input errors,
the synthetic pipeline, CLI, real-data invariants).

Known limitations: descriptive only (no significance, T-024); the reference
is 2–4 houses (I-013); merged entities get no house effect; early final polls
carry later opinion movement in their own errors.
