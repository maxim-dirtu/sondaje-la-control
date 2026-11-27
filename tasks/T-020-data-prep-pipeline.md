---
id: T-020
title: Data preparation pipeline
status: done
phase: 2
depends_on: [T-002, T-003]
owner: github-copilot-cli
branch: task/T-020-data-prep-pipeline
methodology: [M-1.1, M-1.2, M-1.3, M-1.4, M-1.5, M-1.6, M-1.7]
created: 2026-11-22
updated: 2026-11-28
---

## Goal
One function call turns the canonical CSVs into a tidy, analysis-ready table:
one row per (poll, entity) with `s`, `r`, days before the election, recency
weight, `n`, target scope, and house.

## Context
All metrics build on this table. Develop it against **synthetic fixtures**;
real data is not required to start.

## Scope
**In:**
- `src/sondaje/prep.py` (or similar) and its tests
- A single config object holding the tunable parameters, with defaults taken
  from the METHODOLOGY table
- **Shared file allowed:** `docs/METHODOLOGY.md` section M-1, for
  clarifications, and to resolve the open specification issues OI-1…OI-5

**Out:**
- Any metric calculation.

## Acceptance criteria
- [x] OI-1…OI-5 in METHODOLOGY are resolved: the sections are updated and the
      rows are removed from the open-issues table. The choices are in the Log.
- [x] Every M-1.x rule has at least one unit test with hand-computed expected
      values.
- [x] Docstrings cite the M-ID they implement.
- [x] Withdrawals and alliance mappings are applied, and each adjustment is
      logged.
- [x] Ruff and pytest pass.

## Follow-ups
- METHODOLOGY "Tunable parameters" table: add `share_base_priority` (M-1.1,
  OI-1) and `lt_fraction` (M-1.1, OI-2, default 0.5, T-025 tests 0 and 1).
  T-020 could edit only M-1 and the open-issues table.
- AGENTS.md §8 commands table: add `uv run sondaje prep [--output build/prep]`.
- T-025 sensitivity list: add `lt_fraction` (0, 0.5, 1) and the share-base
  order (`all_respondents` first changes the base of 7 of the 45 real polls).
- OI-5 refinement (optional): `n` is not reduced when M-1.5 drops a
  withdrawn/excluded contestant's share, and for `likely_voters` /
  `other_subset` bases the published subset size (e.g. Verifield "59% of the
  sample") is only in `notes`. A numeric column would let `n` follow the base.
- Owner confirmation of the OI-1…OI-5 resolutions and of the clarifications
  C-1…C-5 below (all are marked as T-020 choices in METHODOLOGY M-1).

## Log
- 2026-11-28: Resumed after the previous agent was cancelled. Reviewed its
  uncommitted work: `pandas` (named in ADR-0005 as the analysis library) and
  `src/sondaje/config.py` (one frozen `MethodologyConfig` with the METHODOLOGY
  defaults; CRLF normalized). Both kept. Rebased on `main` (task files and
  PLAN.md only). Owner set to `github-copilot-cli`.
- 2026-11-28: Design. `sondaje.prep.prepare(data_dir, config)` loads `data/`
  through `sondaje.validation.loader` (columns read by name, so an added
  column such as T-016's `sponsor_source` changes nothing) and returns three
  pandas tables: `rows` (one per poll × compared entity), `polls` (one per poll,
  with `eligible`, `in_window`, `final_poll`, `exclusion_reason`), and
  `adjustments` (one per changed value, with its M-ID). Every poll is kept, also
  the excluded ones, so the UI can show them. The "others" bucket has
  `entity_id = _others` (not a valid slug, so it can never clash with an
  entity). A load error, an unknown election, or an unmapped polled entity
  (R-44) raises `PrepError`. New command `sondaje prep [--data-dir]
  [--output DIR]` prints a summary and can write the three tables as CSV.
- 2026-11-28: **OI-1 (share base).** Options: (a) `expressed_option` first,
  then `all_respondents` normalized (suggested default); (b) `all_respondents`
  first; (c) `likely_voters` first (a turnout-screened figure). Choice: (a),
  then `likely_voters`, then `other_subset`. Reason: `expressed_option` is the
  figure the pollster publishes and the public sees; `all_respondents` covers
  the same respondents, so after normalization it differs only by rounding;
  the subset bases use filters described only in `notes`. Effect on real data:
  38 polls use `expressed_option`, 6 `all_respondents` (AtlasIntel polls that
  publish no expressed base, incl. both round-2 polls), 1 `other_subset`
  (Verifield 24–28 Mar 2025, its only base). With `all_respondents` first, 7
  polls would change base.
- 2026-11-28: **OI-2 ("<x" values).** Options: x/2 (suggested), 0, x. Choice:
  x/2 (`lt_fraction = 0.5`), with `has_lt` flags on the poll and row and one
  logged adjustment per value. Reason: the midpoint of the possible range, so
  the error is at most x/2 either way; T-025 tests 0 and 1. Effect on real
  data: only AtlasIntel 10–13 Apr 2025 (two "<1%" candidates). That topline is
  partial on the expressed base, so the remainder rule (C-1) absorbs the
  difference: its `s` values do not change with `lt_fraction`.
- 2026-11-28: **OI-3 (scenarios).** Options: exclude (suggested); include all;
  include and down-weight. Choice: excluded from every metric, kept and
  prepared for transparency (`exclusion_reason = not_headline`). Reason: one
  survey must count once; the headline poll is the pollster's own choice
  (R-63). Effect: 7 real scenario polls excluded.
- 2026-11-28: **OI-4 (no `fieldwork_end`).** Options: exclude from windowed
  metrics (suggested); use `fieldwork_start`; use `published_date` as `t`.
  Choice: exclude from every metric (all metrics are windowed: M-1.3 and the
  M-3 campaign window); no substitute date. Reason: `published_date` is only an
  upper bound of the fieldwork end, so it could pull a poll into a window it
  does not belong to. Effect: 1 real poll (Verifield, published 2024-08-28,
  95 days before the parliamentary election: outside the accuracy window
  anyway, lost only for M-3). M-5.3 already scores the missing dates.
- 2026-11-28: **OI-5 (`n`).** Options: `sample_size` always;
  `sample_size_expressed` if published, else `sample_size` × expressed share
  (suggested). Choice: the suggested rule, with the expressed share taken
  from the poll's `all_respondents` base (vote options, "<x" per OI-2, capped
  at 100%), and `sample_size` as the last fallback; `n_method` records which.
  Reason: the normalized shares rest on the respondents who named an option;
  `sample_size` overstates `n` and so understates sampling error. Effect: no
  real poll publishes `sample_size_expressed`; 13 polls use the scaled
  `n`, 31 fall back to `sample_size` (CURS, Sociopol, most Verifield), 1 has
  no sample size (Verifield 2024-08-28).
- 2026-11-28: Clarifications added to M-1 (not open issues, but needed to make
  the rules mechanical; for owner confirmation):
  - **C-1 partial toplines** (M-1.1): with `topline_coverage = partial` on the
    `expressed_option` base, the unpublished remainder (100 − Σ published vote
    shares) goes to "others"; with other bases the options are normalized as
    published. Effect: 5 real polls (AtlasIntel 10–13 Apr; four Sociopol
    January polls), remainder 1–3 pp each.
  - **C-2 "others"** (M-1.2): built the same way on both sides; in the result
    it holds every contestant not compared on its own (below 1% in the target
    scope, or not named by the poll); a poll with no `other` option has
    `s_others = 0`; the row is kept whenever either side is above 0. Both sides
    sum to 1 for every poll (tested on the real data too).
  - **C-3 final poll ties** (M-1.3): latest `fieldwork_end`, then later
    `published_date`, then larger `poll_id`. The window is inclusive (28 days in).
  - **C-4 mapping dates** (M-1.5): `entity_map` relations apply to every poll of
    the election, whatever their `effective_date`; shares mapping to the same
    contestant are added (e.g. `pmp` → `fd` in 3 CURS and Verifield polls).
  - **C-5 supporting party** (M-1.5): `supporting_party_id` is set only when a
    candidate has exactly one supporting party (nominated or endorsed). Real
    data: among compared candidates only Lasconi → `usr`; Simion (AUR + POT),
    Antonescu and Dan (several) stay with the candidate; Terheș and Șandru
    have one party each but fall below 1% and merge into "others".
- 2026-11-28: Real-data smoke test (`uv run sondaje prep`): 45 polls, 36
  eligible, 17 in the 28-day window, 10 final polls, 268 rows, 62 adjustments.
  The final polls match ADR-0012 (AtlasIntel, CURS, Sociopol in all three
  elections; Verifield in round 2 only). Excluded: 7 scenarios (OI-3),
  AtlasIntel 1–3 May 2025 (published 5 May, M-1.7), Verifield 2024-08-28 (no
  fieldwork dates, OI-4).

## Outcome
- **Done.** `src/sondaje/prep.py` (`prepare`, `summarize`, the `prep`
  command), `src/sondaje/config.py` (`MethodologyConfig`), `pandas`
  dependency, `tests/test_prep.py` (35 tests: every M-1.x rule and OI
  resolution on a synthetic 2099 dataset with hand-computed values, plus
  real-data invariants), METHODOLOGY M-1 updated and the open-issues table
  emptied.
- **Key commits:** `T-020: add pandas (ADR-0005) and the methodology config
  object…`, `T-020: add the M-1 data preparation pipeline…`, `T-020: unit
  tests for every M-1 rule…`, `T-020: resolve OI-1...OI-5 and clarify M-1…`.
- **Known limitations:** `n` is an upper bound for 31 of 45 real polls (no
  expressed sample published); `n` ignores M-1.5 drops; the comparison set is
  per poll, so two polls of one election can compare different entity sets
  (e.g. domestic vs total target, or different named candidates). Metric
  tasks group by `entity_id` and must handle that.