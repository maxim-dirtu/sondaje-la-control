---
id: T-021
title: Error metrics
status: review
phase: 2
depends_on: [T-020]
owner: github-copilot-cli
branch: task/T-021-error-metrics
methodology: [M-2.1, M-2.2, M-2.3, M-2.4]
created: 2026-11-22
updated: 2026-11-28
---

## Goal
Signed error, MAE, total error, and log-odds accuracy per poll and per final
poll of each (house, election).

## Context
See [METHODOLOGY M-2](../docs/METHODOLOGY.md).

## Scope
**In:**
- `src/sondaje/metrics/` and its tests
- **Shared file allowed:** `docs/METHODOLOGY.md` section M-2, for edge-case
  clarifications only (e.g. a share of 0 in log-odds)

**Out:**
- Comparisons between houses (T-022).

## Acceptance criteria
- [x] Each metric is tested against a hand-computed example.
- [x] Edge cases (zero shares, a missing entity) behave as documented in the
      spec.
- [x] Docstrings cite the M-IDs.

## Follow-ups
- **T-022 / owner: common comparison set.** `k` differs between houses of the
  same election (real data, parl-2024-cd finals: 12, 7 and 8 compared entities),
  because each poll names its own entities (M-1.2). `MAE` is a mean over `k`
  rows, so a house that names more small parties is averaged over more small
  errors. `TE` does not have this problem. Decide in T-022 whether the
  comparison between houses uses a common set per election, or `TE`, or both.
- **T-025:** add `zero_floor` (M-2.7) to the sensitivity grid, next to
  `lt_fraction`, and to the "Tunable parameters" table of METHODOLOGY (outside
  this task's scope).
- **Coordinator:** `cli.py` gets one import and one list entry for the new
  `errors` command; T-023 may touch the same lines (trivial merge conflict).

## Log
- 2026-11-28: input is `Prepared.rows` and `Prepared.polls` only. No M-1 logic
  is recomputed. The module reads `eligible`, `in_window`, `final_poll`.
- 2026-11-28: metrics exist for every **eligible** poll, not only in-window
  ones. Out-of-window polls keep their metrics with `in_window = false` (useful
  for error against time, M-3); final polls are always in the window. Ineligible
  polls (scenarios, published on or after election day, no fieldwork end) are
  absent from the metric tables; they stay in `Prepared.polls` for display.
- 2026-11-28: **Undefined log-odds** (a share of 0 or 1) is not specified in
  M-2.4. Options: (a) leave the term out of `B` and report how many were left
  out; (b) clip the shares to `[f, 1 − f]`; (c) drop the whole poll's `B`.
  Chose (a) as the default, and (b) as the option `zero_floor`. Reason: the
  common case is an `_others` share of 0 because the poll published no "others"
  option, which is a format artefact, and any floor dominates `B` (ln(.01/.99
  against .05) is −1.65 against typical terms of 0.2 to 0.5). (a) can slightly
  favour polls that omit "others"; `b_undefined` is always shown next to `B`,
  and MAE and TE still include the term. Written as M-2.7.
- 2026-11-28: a "missing entity" cannot occur after M-1.2: an entity of the result
  that the poll does not name sits in the result's "others", and the poll's
  "others" is 0 (or its `other` option). A NaN share in the input is an error
  (`MetricsInputError`), never filled in.
- 2026-11-28: "others" is a compared entity in `k`, `MAE`, `TE`, and `B` (it
  is part of the comparison, M-1.2). Because both sides sum to 1, `Σ e = 0`
  and `TE` = sum of the overestimates; tests check this on every poll, on
  synthetic and real data.
- 2026-11-28: new section M-2.7 (new ID, nothing renumbered) holds the
  conventions above. M-2.1 to M-2.4 are unchanged.
- 2026-11-28: added the `sondaje errors` command (prints the final-poll table,
  `--output` writes `entity_errors.csv`, `poll_errors.csv`, `final_polls.csv`,
  `--zero-floor` is the sensitivity option). It lives in `metrics/errors.py`
  and is registered in `cli.py` on its own line. `cli.py` is outside the literal
  scope; the change is two lines, the same pattern as `prep`.
- 2026-11-28: `metrics/__init__.py` is the agreed one-line docstring, so as to
  not conflict with T-023.

## Outcome
`sondaje.metrics.errors` computes, from `prepare()` output:
- `entity_errors`: per (eligible poll, entity) signed error `e` in pp (M-2.1)
  and log-odds error `A'` (M-2.4).
- `poll_errors`: per eligible poll `k`, `MAE` (M-2.2), `TE` (M-2.3), `B` with
  `b_terms` and `b_undefined` (M-2.4).
- `compute_errors` returns both in `ErrorMetrics`, with `final_polls` and
  `final_entities` for the final poll of each (house, election).
- `sondaje errors [--output DIR] [--zero-floor F]` for the table.

Key commits: see `git log task/T-021-error-metrics`. Tests:
`tests/test_metrics_errors.py` (31 tests; hand-computed values for each metric,
the zero-share and missing-entity cases, excluded and out-of-window polls, final
poll selection, CLI, real-data invariants).

Known limitations: `MAE` is not computed over a common comparison set across
houses (see Follow-ups); `B` omits undefined terms by default (M-2.7).
