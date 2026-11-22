---
id: T-001
title: Define data model and CSV schemas
status: review
phase: 0
depends_on: []
owner: agent-t001-2
branch: task/T-001-data-model
methodology: [M-1, M-5.3]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
A complete, documented data model and CSV layout that every data-collection and
analysis task can rely on without further discussion.

## Context
- [ADR-0004](../docs/decisions/0004-data-storage-csv-in-git.md): canonical data is
  CSV in git, split into files so that agents don't collide.
- [ADR-0007](../docs/decisions/0007-mvp-scope.md): MVP scope (3 elections, 2–4
  pollsters), full toplines, and archived originals.
- [METHODOLOGY M-1](../docs/METHODOLOGY.md) lists the fields the calculations need
  (sample size, fieldwork dates, target scope, alliances).
- M-5.3 lists the transparency fields captured per poll.

## Scope
**In:**
- `docs/DATA_MODEL.md` (new; this task owns it)
- `data/README.md` and the directory layout under `data/`, with header-only
  CSV files where useful
- ID conventions: elections (MVP: `parl-2024-cd`, `pres-2025-r1`,
  `pres-2025-r2`; the pattern must also fit future ones such as `ep-2024` and
  `pres-2024-r1`), entities (parties/candidates), pollsters, and polls
- Entities to cover: elections, entities (parties/candidates), per-election
  alliance/label mapping, pollsters, polls (one row per poll), poll results
  (one row per poll × option: the **full topline** as published, including
  "other", undecided, and non-response, each tagged with an option type), and
  election results (scope: `domestic` | `diaspora` | `total`)
- Poll metadata: fieldwork start/end, publish date, sample size, mode, sampled
  population (e.g. all adults / likely voters; residents / including the
  diaspora), question type (prompted list / open), client/sponsor and sponsor
  type, question wording, whether the weighting and the margin of error were
  published, `source_url`, `source_type` (`pollster` | `media` | `wikipedia` |
  `other`), `verified` (whether checked against the original source),
  `retrieved_at`, and `notes`
- Archive fields for the original report: `archive_url` (Web Archive),
  `sha256`, and `extraction_method` (`pdf_text` | `html` | `manual_double_entry`)
- File layout **per pollster** for poll data (ADR-0007), and per election for
  results
- Append-only rule for shared registry files (`entities`, `pollsters`)

**Out:**
- Validation code (T-003) and real data (T-004, T-005, Phase 1).

## Acceptance criteria
- [x] `DATA_MODEL.md` documents every column: name, type, required/optional,
      allowed values, and an example. (§6, 12 files; types in §3.2; header
      lines in §6.14, checked against the tables by script.)
- [x] The layout lets the Phase 1 tasks run in parallel without touching the
      same files (except append-only registries). (§2.2: T-010 writes only
      `elections/<id>/results*.csv` + manifest; each pollster task only
      `polls/<pollster_id>/`; shared writes are append-only: registries and
      `entity_map.csv`.)
- [x] Every input needed by M-1, M-2, M-3, M-4.1, and M-5.3 is present.
      (§8 coverage matrix.)
- [x] Raw shares are stored exactly as published. The docs state that
      normalization happens in code, never in data. (§1 principle 1,
      `share_raw`, data/README.md.)
- [x] A worked example (one fictitious poll, clearly labelled as fictitious and
      kept out of `data/`) shows every file involved. (§10: `parl-2099-cd`,
      `example.org` URLs; every file except the presidential-only
      `candidate_support.csv`, which is shown as a sample row, and the reserved
      inventory.)

## Follow-ups
- **T-003:** implement §7 rules R-01…R-94 and the parameters
  (`share_sum_tolerance_pp`, `max_poll_age_days`, injectable `reference_date`
  so the 2099 example can be a fixture). R-34 (append-only check against
  `main`) may be a separate command.
- **T-003 task file** says "fieldwork start ≤ end ≤ election date"; the model
  uses `fieldwork_end < election_date` (R-81, exit polls out of scope). The
  coordinator may align the T-003 wording.
- **T-004:** also register well-known withdrawn/excluded/never-registered
  candidates that polls included (entity + `entity_map` row), not only the
  entities in the official results; otherwise every pollster task appends the
  same rows and they collide.
- **T-004 / T-010:** `registry/entities.csv` has two writers in parallel;
  T-010 should append only entities that T-004 missed, after rebasing on
  T-004's merge.
- **METHODOLOGY M-1.1 (proposal):** state which `share_base` T-020 uses when a
  poll publishes several (suggested default: `all_respondents` if present,
  else `expressed_option`), how `share_qualifier = lt` values enter the
  normalization, and how `headline = false` scenarios are treated (suggested:
  excluded from metrics, kept for transparency).
- **METHODOLOGY M-1.3/M-3 (proposal):** define `t` for a poll without
  `fieldwork_end` (suggested: excluded from windowed metrics; R-86 warns).
- **METHODOLOGY M-4.1 (proposal):** whether `n` is `sample_size` or
  `sample_size_expressed` when shares are on the expressed base.
- **AGENTS.md §6 (proposal):** mention the extra `source_type` values
  `official` and `aggregator` and link DATA_MODEL.md §5.1.
- **T-011:** define §6.13 (inventory) and may extend the `extraction_method`
  enum (e.g. OCR) through §9.
- **T-062:** extend the election ID grammar and `body` enum for local elections.
- **Idea (I-014 related):** crosstabs extracted from the archived reports would
  need a separate per-pollster file (`poll_crosstabs.csv`); not designed here.

## Log
- 2026-11-22: Resumed after the first agent (agent-t001) was cancelled right
  after claiming. Rebased the branch on `main` (T-002 skeleton, ADR-0009),
  owner set to `agent-t001-2`.
- 2026-11-22: Layout: `data/registry/` (5 append-only registries),
  `data/elections/<election_id>/` (results, totals, entity map, candidate
  support, manifest) and `data/polls/<pollster_id>/` (polls, poll_results,
  manifest, reserved inventory), per ADR-0004/0007. Created header-only files
  for the registries and the 3 MVP election directories so T-004 and T-010
  start from the exact headers; pollster directories are left to the pollster
  tasks (`data/polls/.gitkeep`). No real data added.
- 2026-11-22: Poll **labels** are resolved per row (`option_label` verbatim +
  `entity_id`) instead of a shared per-election label table: a shared label
  table would be written by every pollster task. Consistency is enforced by
  R-62. The per-election `entity_map.csv` covers the alliance mapping and
  withdrawals/exclusions (M-1.5) and is append-only.
- 2026-11-22: Withdrawn/excluded/never-registered contestants are explicit
  `entity_map` rows (no target) rather than implied by absence from the
  results, so T-020 can log the reason and T-003 can flag unmapped entities
  (R-44).
- 2026-11-22: Added `share_base` (all respondents vs. respondents who named an
  option, etc.) because Romanian reports often publish both bases; each is
  stored as published. Sum checks run per base.
- 2026-11-22: Added `undecided_or_non_response` (the common combined "NS/NR"
  bucket), `none`, `blank_or_invalid`, `other_non_vote` to the option types
  required by the task, so no published option has to be split or guessed.
- 2026-11-22: `share_raw` keeps the published precision (`30` vs `30.0`);
  `<1%` is stored as `1` + `share_qualifier = lt`. Sum tolerance ±2.0 pp
  (rounding with ~10 integer options), with `lt` rows treated as an interval.
- 2026-11-22: `headline` + `scenario` model surveys that ask several
  variants for one election (e.g. different candidate lists), so duplicate
  detection (R-93) and market averages do not double-count a survey.
- 2026-11-22: The provenance block (`source_url`, `source_type`,
  `retrieved_at`, `verified`, `notes`) is on every data file, including
  `poll_results` (AGENTS.md §6 "every row"). `source_type` extends the task's
  list with `official` (AEP/BEC, needed for results/registries) and
  `aggregator` (sondajeromania.ro), so they are not hidden in `other`.
  `verified = true` is forbidden for Wikipedia/aggregator rows (R-14).
- 2026-11-22: Archive fields live in one `archive_manifest.csv` schema used
  for both poll reports and official result files (T-010's committed
  manifest); polls reference a `document_id`, and `extraction_method` is per
  poll because one document can be extracted in different ways.
  `archive_url` is mandatory for poll documents (ADR-0007), optional for
  result files.
- 2026-11-22: Transparency (M-5.3) is derived from the poll columns
  (non-empty `sample_size`, fieldwork dates, `mode`, `question_wording`;
  `weighting_published`, `moe_published`; `sponsor_type ≠ not_disclosed`)
  instead of seven separate flags, to avoid redundant, inconsistent data.
- 2026-11-22: `target_scope` is stored per poll (M-1.4) and must agree with
  `population_geo` (R-64); default `domestic`.
- 2026-11-22: `fieldwork_end < election_date` (not ≤): fieldwork on election
  day means an exit poll, out of scope. R2 polls must start after R1 (R-84),
  matching the pollster template.
- 2026-11-22: Results store votes only (shares derived); `results_totals.csv`
  holds `valid_votes` per scope. Domestic + diaspora = total is exact (R-51).
- 2026-11-22: Election ID grammar `<type>-<year>[-<body>][-<tag>][-r<round>]`
  with an optional `tag` for same-year collisions (e.g. a re-run); `status`
  (`held`/`annulled`/`scheduled`) records annulled elections such as a future
  `pres-2024-r1` backfill.
- 2026-11-22: Worked example uses a fictitious election `parl-2099-cd` and
  `example.org` URLs so it can never be mistaken for real data; its CSV
  headers, sums, and FKs were checked with a throwaway script (not committed).
- 2026-11-22: Checks: `uv run pytest` (8 passed), `uv run ruff check .`,
  `uv run ruff format --check .` all pass (no code changed).

## Outcome
`docs/DATA_MODEL.md` (schema version 1.0) defines the complete data model:
principles (raw values as published; normalization only in code), the
`data/` layout and file ownership (append-only registries vs. owned files),
the CSV dialect and column types, ID conventions (elections, entities,
pollsters, polls, documents), the provenance block and archive fields, 12
file schemas with every column specified, header lines, 50+ numbered
integrity rules (R-01…R-94) for T-003, a METHODOLOGY coverage matrix, the
schema change process, and a fully fictitious worked example covering every
file. The inventory (§6.13) is reserved for T-011.

Also added `data/README.md` and the header-only CSVs for the 5 registries and
the 3 MVP election directories, plus `data/polls/.gitkeep`.

Key commits: `53f7d95` (resume), `7e0599a` (DATA_MODEL.md), `2671991`
(data layout), `4121f86`, `9176b79` (refinements).

Known limitations: no machine-readable schema (T-003 owns the code schema);
local elections and crosstabs are not modelled yet; several M-1 choices
(which base, `lt` values, non-headline scenarios) are proposed under
Follow-ups for METHODOLOGY.