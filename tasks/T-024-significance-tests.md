---
id: T-024
title: Significance tests
status: review
phase: 2
depends_on: [T-022]
owner: claude-opus (github-copilot-cli)
branch: task/T-024-significance-tests
methodology: [M-4.1, M-4.2, M-4.3]
created: 2026-11-22
updated: 2026-11-28
---

## Goal
For every (house, entity): sampling z-scores per poll, and a sign test and a
t-test across elections, using (house, election) as the unit.

## Context
These tests separate systematic lean from noise. They are the frequentist
precursor of the Bayesian model (T-040).

## Scope
**In:** `src/sondaje/stats/` and its tests.
**Out:** the Bayesian model (T-040).

## Acceptance criteria
- [x] The results match SciPy reference values in the tests.
- [x] The unit of independence follows M-1.6 (tested).
- [x] Combinations with fewer than 3 elections are flagged as insufficient
      instead of being tested.

## Follow-ups
- **METHODOLOGY M-4 (shared file, not in scope).** Proposed spec text for the
  choices below (see *Log*): M-4.1 runs on every eligible poll, `z = e / SE`
  with `SE` in pp, empty `z` without `n` (`no_sample_size`) or with `r` = 0 or 1
  (`result_share_0_or_1`); M-4.2/M-4.3 are two-sided by default, use one `he`
  per (house, election), leave out elections without a reference house and the
  common "others", drop ties (`|he| ≤ 1e-9` pp) from the sign test only, and
  need at least 3 elections (`insufficient (< 3 elections)` otherwise); results
  on ≤ 3 elections are marked `preliminary`; candidates are identified with
  their single supporting party across elections (`--attribution party`).
- **Spec question: candidate → party attribution across elections (M-1.5,
  I-016).** With "exactly one supporting party", only `elena-lasconi → usr`
  applies in the real data: `george-simion` has `aur` (nominated) and `pot`
  (endorsed), `nicusor-dan` has several endorsements. Should only `nominated`
  support count? Then `aur` would reach 3 elections (parl-2024-cd,
  pres-2025-r1, pres-2025-r2) for every house that polled all three.
- **Spec question: are the two rounds of one presidential election separate
  units for cross-election tests?** M-1.5 makes each round an election `E`, so
  they count as two units here, but they are two weeks apart with the same
  houses; their errors are unlikely to be independent.
- **Spec question: two-house elections and two-entity races.** With two houses
  `he` values are mirror images (M-2.8), and in a two-candidate round the `he`
  of the two candidates are mirror images too (pres-2025-r2). Both still enter
  the tests as one value per unit; the spec could say whether to keep them.
- **Spec question: multiple comparisons.** One test per (house, entity) gives
  many tests (32 combinations on the real data); no correction (Holm, BH) is
  applied. T-040 may make this moot.
- **`sondaje.metrics.relative.NOT_SIGNIFICANCE`** still says "no significance
  test yet (T-024)". It could point to `sondaje significance` (relative.py is
  outside this task's scope).

## Log
- 2026-11-28: Branch `task/T-024-significance-tests`. Added `scipy` (runtime
  dependency, `uv add scipy`: only `scipy` 1.18.1 enters `uv.lock`) for
  `binomtest`, `ttest_1samp`; no other dependency changed.
- 2026-11-28: **Inputs, nothing recomputed.** `poll_z_scores` reads
  `ErrorMetrics.entities` (`s`, `r`, `e`) and `ErrorMetrics.polls` (`n`,
  `n_method` from prep, M-1.1 OI-5). `z = e / SE` with `SE = 100·sqrt(r(1−r)/n)
  ·sqrt(deff)` in pp, which equals `(s − r)/SE` of M-4.1 without recomputing
  the error. `deff` is `MethodologyConfig.deff` (default 1.5), the same
  parameter `metrics.market.campaign_rows` uses for M-3.2; the CLI passes
  `Prepared.config`. The tests take `he` from
  `compute_relative(...).house_effects` (M-2.5). No accessor had to be added.
- 2026-11-28: **M-4.1 scope.** Every eligible poll (in or out of the window),
  with `in_window` and `final_poll` carried, so that z can be plotted against
  time. Polls without `n` keep their rows: `se`, `z` empty, `z_status =
  no_sample_size`. `r` = 0 or 1 gives `SE` = 0: `z_status =
  result_share_0_or_1`, `z` empty (no infinite value). The "others" row gets a
  z like any compared entity (M-1.2).
- 2026-11-28: **Unit (M-1.6).** `house_effects` holds only the final poll of
  each (house, election), so each unit gives one `he`; extra polls of the same
  unit cannot change `n` (tested: three extra non-final polls leave
  `lean_units` and `tests` identical). Two rows for one (house, election,
  entity) raise `MetricsInputError`.
- 2026-11-28: **What enters the cross-election tests.** Left out: rows with
  empty `he` (election with a single house: no reference, so no unit) and the
  common "others" (its content differs per election, so it is not one entity
  across elections). It still gets an M-4.1 z.
- 2026-11-28: **Entity identity across elections (`lean_id`).** Default
  `--attribution party`: a candidate with exactly one supporting party
  (`supporting_party_id`, M-1.5) is counted as that party, so a lean can be
  followed from parliamentary to presidential elections (I-016). If two rows of
  one unit would share a party, both keep their own `entity_id` (same spirit
  as M-1.5's "several parties → candidate"). `--attribution entity` keeps
  every entity separate. The `entities` column lists what fed each test.
- 2026-11-28: **Ties and sides.** `|he| ≤ 1e-9` pp is a tie (float noise from
  `e − market_e`). Ties are left out of the sign test (usual convention: a
  tie has no sign; `n_ties` is reported) but kept in the t-test as ordinary
  values. Both tests are **two-sided** by default (`--alternative greater|less`
  available): the question is whether there is a lean in either direction.
  `sign_p_min` reports the smallest p-value the sign test could give
  (`2·0.5^m`, two-sided), e.g. 0.25 with 3 elections. The t-test is empty when
  all values are equal (sd 0).
- 2026-11-28: **Threshold.** Fewer than 3 elections (`MIN_ELECTIONS`):
  `status = insufficient (< 3 elections)`, every test column empty, only the
  descriptive columns (elections, `mean_he`, `sd_he`, sign counts) filled in.
  `preliminary = true` for every result on ≤ 3 elections.
- 2026-11-28: **Real data** (`uv run sondaje significance`): 36 eligible
  polls, 213 z rows, none without `n`. Final polls: 30 of 53 (entity, poll)
  rows lie outside the 95% sampling band (|z| > 1.96); n_method is
  `sample_size` for 26 of 36 polls, which overstates n. Cross-election: **0 of
  32 (house, entity) combinations tested**, all `insufficient (< 3
  elections)`: candidates appear in at most 2 elections (the two rounds), and
  only `usr` links two election types (via `elena-lasconi`), so 2 elections.

## Outcome
- **New package `src/sondaje/stats/`**, module `significance.py`:
  `sampling_se`, `poll_z_scores` (M-4.1), `lean_units` (M-1.6 units),
  `sign_test` (M-4.2), `t_test` (M-4.3), `cross_election_tests`,
  `compute_significance`, `summarize`, and the CLI command
  `sondaje significance [--data-dir] [--output DIR] [--weighting recency|equal]
  [--attribution party|entity] [--alternative two-sided|greater|less]`, which
  writes `z_scores.csv`, `lean_units.csv`, `tests.csv`. Registered in
  `cli.py` (one line plus import).
- **Tests:** `tests/test_stats_significance.py` (36 tests): z by hand, `deff`
  from config, `n`/`n_method` carried, missing `n` kept and marked, `r` = 0;
  sign test and t-test against `scipy.stats.binomtest`/`ttest_1samp` (two- and
  one-sided), the 0.25 floor with 3 elections, ties; M-1.6 (extra polls do not
  change `n` or any statistic; duplicate units rejected); the
  `insufficient (< 3 elections)` flag; party vs. entity attribution; neutral
  wording; CLI.
- **Key commits:** `T-024: set status in-progress`, `T-024: add scipy for the
  binomial and t tests`, `T-024: add M-4.1 z-scores and M-4.2/M-4.3
  cross-election tests`.
- **Known limitations:** on the MVP data nothing reaches 3 elections, so no
  cross-election test runs yet (see *Follow-ups* for the attribution and
  rounds questions). M-4.1 measures sampling error only; `n_method =
  sample_size` overstates `n`. No multiple-comparison correction.
