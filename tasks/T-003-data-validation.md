---
id: T-003
title: Data validation tooling
status: done
phase: 0
depends_on: [T-001, T-002]
owner: agent-t003
branch: task/T-003-data-validation
methodology: []
created: 2026-11-22
updated: 2026-11-22
---

## Goal
`uv run sondaje validate` catches every schema, integrity, and provenance
error in `data/` before it reaches the analysis.

## Context
CSV does not enforce a schema ([ADR-0004](../docs/decisions/0004-data-storage-csv-in-git.md)).
Several agents add data concurrently, so validation is their shared safety net.

## Scope
**In:**
- `src/sondaje/` validation module plus the CLI subcommand, and tests with
  valid and invalid fixtures
- One machine-readable schema definition in code, kept consistent with
  `docs/DATA_MODEL.md`
- The integrity rules **R-01…R-94** in DATA_MODEL.md §7, with their
  parameters (`share_sum_tolerance_pp`, `max_poll_age_days`, and an injectable
  `reference_date`, so that the fictitious 2099 example in §10 can be a test
  fixture). R-34 (append-only check against `main`) may be a separate command.

**Out:**
- Fixing the data itself.

## Acceptance criteria
- [x] Every rule in DATA_MODEL.md ?7 is implemented, or listed in the Log
      with the reason it was deferred.
- [x] Checks required columns, types, enums, and UTF-8 encoding.
- [x] Checks referential integrity: election, entity, pollster, poll, and
      document IDs.
- [x] Checks dates: fieldwork start ? end < election date (R-81; exit polls
      are out of scope), and publish date ? fieldwork end.
- [x] Checks sums: raw poll shares sum to 100 ? the tolerance for each
      (poll, share base), and domestic + diaspora = total for results.
- [x] Checks provenance: `source_url` and `retrieved_at` are not empty.
- [x] Detects duplicate polls (same pollster, fieldwork dates, and election).
- [x] Errors report `file:row: message`, and the exit code is non-zero on error.
- [x] Each check has at least one passing and one failing test fixture.

## Follow-ups
- **AGENTS.md ?8 (shared, proposal):** add `uv run sondaje validate` (and
  `uv run sondaje validate --against main` before handing off a data task) to
  the commands table and to the "all checks must pass" line.
- **DATA_MODEL.md ?7 (shared, proposals; the code follows the readings below):**
  - Message format: the tool prints `path:row: [R-xx] error|warning: message`;
    file-level findings (R-05, R-34 removals, missing files) have no row.
    ?7 could show this exact format.
  - R-34 is `sondaje validate --against <ref>`; ?7 could name the flag.
  - R-20: the grammar (?4.1) allows `-rN` "only for elections that can have
    several rounds", but R-20 only says "`-rN` ? `round = N`". The code
    rejects `-rN` on parliamentary and European IDs, and rejects type `local`
    as reserved until T-062. ?7 could say so explicitly.
  - R-43 is checked only when `results.csv` of the election has rows (like
    R-41/R-44); otherwise every `candidate_support` row written by T-004
    would warn until T-010 lands. ?7 could add the same parenthesis.
  - ?3.1 "the file ends with a newline" is enforced under R-01, and "a field
    is quoted only when needed" is **not** validated (Python's `csv` module
    does not expose the original quoting; the data is equivalent either way).
    ?7 R-01 could list the first and drop or soften the second.
  - Overlapping rules are reported once, under the more specific ID (see Log
    2026-11-22 "Duplicate reporting"). ?7 could note which one wins.
  - `data/polls/<id>/inventory.csv` (reserved, ?6.13) produces an R-05
    *warning* "reserved; not validated" if it appears before T-011 defines it.
- **T-011:** when ?6.13 is defined, add the `inventory.csv` table to
  `src/sondaje/schema.py` (and drop it from `RESERVED_FILES`); the schema
  tests in `tests/test_schema.py` will then require the column table and the
  ?6.14 header line to match.
- **CI / pre-commit (idea):** run `uv run sondaje validate --against main`
  automatically on every branch that touches `data/`.

## Log
- 2026-11-22: Claimed the task (`agent-t003`), worktree
  `..\sondaje-wt\T-003`, branch `task/T-003-data-validation`.
- 2026-11-22: **Design.** One schema definition in code,
  `src/sondaje/schema.py` (column types, `Req` flags, enum values, value
  ranges, foreign keys, keys, append-only flag, locations, ?6 section). The
  validator is the package `src/sondaje/validation/`: `loader.py` (file
  discovery, R-01/R-02/R-03/R-10 while parsing), `cells.py` (?3.2 types), and
  one module per ?7 family (`rules_files.py`, `rules_provenance.py`,
  `rules_registries.py`, `rules_elections.py`, `rules_polls.py`,
  `rules_dates.py`, `rules_sums.py`), plus `history.py` (R-34) and
  `command.py` (CLI). Parameters are constants in `validation/model.py`
  (`SHARE_SUM_TOLERANCE_PP = 2.0`, `MAX_POLL_AGE_DAYS = 365`) and fields of
  `ValidationConfig` together with `reference_date`.
- 2026-11-22: **No new dependency.** The standard library `csv` module
  (`strict=True`) is enough for ~thousands of rows and keeps `uv sync` light;
  `Decimal` is used for exact share sums.
- 2026-11-22: **CLI.** `uv run sondaje validate [--data-dir data]
  [--reference-date YYYY-MM-DD] [--against REF] [--strict] [--quiet]`.
  Exit 1 on any error (or any warning with `--strict`), else 0. Output is
  sorted by path and row, then a summary line `N error(s), M warning(s)`.
  Paths are shown relative to the working directory with `/` separators.
  stdout uses `backslashreplace` so that diacritics never crash a Windows
  console with a legacy code page.
- 2026-11-22: **All rules R-01?R-94 are implemented; none is deferred.**
  R-34 is the optional `--against REF` check (it needs git): every row of an
  append-only file (`registry/*.csv`, `elections/*/entity_map.csv`) at REF
  must still be at the same position with the same key; non-key fields may
  change; one error per file at the first difference; a deleted file with
  rows at REF is an error; an unknown REF is an R-34 error.
- 2026-11-22: **Readings of the spec** (also proposed under Follow-ups):
  - R-01 also covers "file ends with a newline" (?3.1), a malformed CSV
    (bad quoting, `csv.Error`), and an invalid UTF-8 byte (the file is then
    skipped). A row with a line break inside a field is reported and skipped.
  - R-03: a data row with the wrong number of fields (including an empty
    line) is reported under R-03 and skipped; leading/trailing whitespace is
    an R-03 error in **every** column (?3.1), not only `text`.
  - R-05: the type of an election directory is taken from the registry, or
    from the `pres-` prefix when the election is not registered yet (the MVP
    directories are header-only before T-004). A directory holding only
    `.gitkeep` still counts as a pollster directory and needs its 3 files.
  - R-20: `-rN` is an error on parliamentary and European IDs; type `local`
    is an error ("reserved until T-062"). A `-<tag>` part is ignored.
  - R-21 / R-84: the previous round is the same ID with `-r(N?1)`.
  - R-43 only when `results.csv` of the election has rows (as R-41, R-44).
  - R-53: if `results.csv` has rows but `results_totals.csv` lacks a scope
    (or the file), that is an R-53 error.
  - R-62: label consistency includes non-entity options (a label mapped to
    an empty `entity_id` in one poll and to an entity in another is an error).
  - R-63: the survey key uses the raw cells, so polls with empty fieldwork
    dates from the same document group together.
  - R-81 is skipped when both fieldwork dates are empty (R-86 warns).
- 2026-11-22: **Duplicate reporting** (one finding per problem): duplicate
  keys of `elections`/`entities`/`pollsters` are R-30, not R-04; duplicate
  aliases are R-31 only; an empty required provenance cell is R-10, not R-03;
  a `poll_results` row whose poll does not exist is R-06 (the same condition
  also appears in R-60's text); a full topline whose exact shares exceed
  100 + tol is R-91, not also R-90; the `raw_path` prefix in R-71 is enforced
  by the `path` type (R-03). Other overlaps are kept (e.g. R-05 for an
  unregistered directory with rows plus R-06 per row).
- 2026-11-22: **Fixtures and tests.** `tests/fixtures/example/` is DATA_MODEL
  ?10 byte for byte (a test re-extracts the blocks from the document and
  compares); it validates with 0 errors and the 2 expected R-33 warnings
  (delta, epsilon have no color). `tests/fixtures/presidential/` is a second
  fictitious data set (2099 presidential rounds 1 and 2, candidate support,
  an excluded candidate, a headline poll plus a scenario, a `<1%` share, a
  partial topline, an undisclosed sponsor, a scanned report) that validates
  with 0 issues. Failing fixtures are generated in `tests/test_validation_rules.py`
  as copies of these two with one mutation each; every test asserts the exact
  set of (rule, severity) pairs added. 106 failing cases cover every rule
  (several per rule where the rule has several clauses), plus 8 boundary cases
  that must pass (tolerance edges, `lt` shares, shared-precision periods,
  `-suffix` poll IDs). `tests/test_schema.py` parses the ?5.1/?6 column tables
  (names, types, Req, enum values, FKs) and the ?6.14 header block and
  compares them with `schema.py`, and checks every header in `data/`.
  `tests/test_validation_history.py` builds a throw-away git repository for
  R-34 (identity passed with `-c`, global config untouched).
- 2026-11-22: Updated `data/README.md` (one line: `--against main`).
- 2026-11-22: **Coordinator review fix.** On a scratch merge with T-004 and
  T-005 the real `data/` gives 0 errors and 88 R-33 warnings, which made two
  tests fail because they required exactly 0 warnings. The tests on the real
  `data/` (`test_repository_data_has_no_errors`,
  `test_default_data_dir_is_the_repository_data`) now assert 0 errors only,
  and accept any number of warnings. The strict 0-warning assertions remain
  for the fixtures. Checked by overlaying the T-004/T-005 data files on a
  copy of `data/` under the git-ignored `build/` (not committed): those tests
  pass, and `sondaje validate` reports 0 errors and 88 warnings.

## Outcome
`uv run sondaje validate` checks everything under `data/` against
`docs/DATA_MODEL.md` and implements every integrity rule R-01?R-94 (R-34 via
`--against main`), with the ?7 parameters and an injectable reference date.
The schema lives once in `src/sondaje/schema.py` and is tested against the
document and the committed headers. The repository `data/` validates with
0 errors and 0 warnings (also with `--against main`).

Key commits: claim; validator + schema + ?10 fixture; tests (per-rule
fixtures, presidential fixture, R-34, CLI, schema consistency); robustness
test, docs and task file.

Verification (2026-11-22): `uv sync`, `uv run pytest` (all pass),
`uv run ruff check .`, `uv run ruff format --check .`,
`uv run sondaje validate`, `uv run sondaje validate --against main`.

Known limitations: the "quote only when needed" style of ?3.1 is not
checked; R-34 needs git and compares keys by position only; the reserved
`inventory.csv` is not validated until T-011 defines it.
