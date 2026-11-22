---
id: T-007
title: Schema amendments from Phase 0 follow-ups
status: done
phase: 0
depends_on: [T-003, T-004, T-005]
owner: agent-t007
branch: task/T-007-schema-amendments
methodology: [M-1.5]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
The data model, the validator, and the existing data can express every
situation found in Phase 0, without workarounds.

## Context
The follow-ups raised by T-003, T-004, and T-005 (see their task files). The
most important one: in `parl-2024-cd`, PMP ran on Forța Dreptei's lists, but
`entity_map` has no relation for "ran on another party's list". PMP is
currently mapped as `not_registered`, so a poll share for PMP would be dropped
instead of being added to Forța Dreptei.

## Scope
**In:**
- **Shared files allowed:** `docs/DATA_MODEL.md` (bump the schema version and
  follow §9), and the related code: `src/sondaje/schema.py`,
  `src/sondaje/validation/`, and tests.
- Amendments:
  1. **`entity_map` relation for running on another party's list** (e.g.
     `ran_on_list_of`). A poll share for the entity is added to the host
     entity's share. Update the PMP row in
     `data/elections/parl-2024-cd/entity_map.csv`, with a source. Check whether
     other parl-2024-cd parties are in the same situation.
  2. **Person with two roles** (e.g. a list independent in one election and a
     presidential candidate in another): document the ID rule in §4.2. Either
     confirm the current `-<year>` suffix approach or replace it, and update
     the data if it changes.
  3. **Person IDs:** clarify which given name is used (first given name,
     everyday name, or full name).
  4. **§7:** document the validator's output format
     (`path:row: [R-xx] error|warning: message`), the `--against REF` option,
     and the interpretations T-003 recorded in its Log (R-20, R-43, overlap
     reporting).
  5. **Survey `mode`:** a convention for face-to-face polls that don't say
     CAPI or PAPI, and for "random digital recruitment" polls (T-005
     follow-up).
  6. **`verified`:** define what it means for alias and affiliation rows.
  7. **Fill `counterpart_entity_id`** in `pollster_affiliations.csv` where the
     counterpart is now a registered entity.

**Out:**
- The poll inventory (T-011), local elections (T-062), and crosstabs (I-014).

## Acceptance criteria
- [x] Each amendment is either done, or explicitly declined with a reason in
      the Log.
- [x] The DATA_MODEL version is bumped and the change list follows §9.
- [x] The validator and its tests are updated; every new rule has a passing and
      a failing fixture.
- [x] `uv run sondaje validate` reports 0 errors; pytest and ruff pass.

## Follow-ups
- **METHODOLOGY M-1.5 (shared, proposal).** Add after the first bullet:
  "A party that filed no lists of its own and whose candidates ran on another
  contestant's lists under a party-level arrangement (`entity_map` relation
  `ran_on_list_of`) is treated like an alliance member: its poll share is
  added to the host contestant's share before normalization (M-1.1). The
  adjustment is logged."
- **T-020 (data prep):** implement `ran_on_list_of` exactly like
  `alliance_member` (add the guest's share to `result_entity_id`), and log it.
- **Pollster tasks (T-012+):** a combined label such as "PMP+FD" or
  "Forța Dreptei (PMP)" gets `entity_id = fd` (the host's list), with a note on
  the `poll_results` row (DATA_MODEL §6.6). If a poll shows Alternativa Dreaptă
  or PNȚ Maniu-Mihalache separately, append an entity and a `parl-2024-cd`
  `entity_map` row `ran_on_list_of` → `fd`, with the same sources as the
  `pmp` row (both are named in them).
- **Coordinator / T-020: `adu` in parl-2024-cd.** Alianța Dreapta Unită (USR,
  PMP, FD) did not run; its members ran on two different ballots (USR on its
  own lists, PMP on the FD lists). A single `result_entity_id` cannot express
  a split, so `adu` stays `not_registered` (share dropped). If a 2024 poll
  shows ADU, M-1.5 needs a rule (drop, or exclude the poll).
- **Optional registry correction (T-005 owner):** under the new `mode`
  conventions, `typical_modes` of `dataecho` and `noi-cetatenii` could be
  `other` (random digital recruitment, no interview channel named). Left
  empty here, which is still correct ("not known").
- **Idea (not a task yet):** a machine-readable link between the two IDs of a
  person with two roles (e.g. a `same_person_as` column in `entities.csv`).
  Today the link is only in `notes` (§4.2). Not needed by any M-section.
- **Housekeeping:** `tasks/T-003-data-validation.md` contains literal `?`
  characters where `§`, `≤`, `±`, `…` were meant (an encoding loss in that
  file). Not changed here (out of scope).

## Log
- 2026-11-22: Claimed the task (`agent-t007`), worktree
  `E:\Projects\sondaje-wt\T-007`, branch `task/T-007-schema-amendments`.
- 2026-11-22: **Version.** DATA_MODEL 1.0 → **1.1** (minor, additive: two new
  enum values, three new rules, clarifications; no header changed, so no file
  is migrated structurally). `SCHEMA_VERSION` in `src/sondaje/schema.py`
  follows; a new test checks that the document, the code, and the new §9.1
  schema history agree.
- 2026-11-22: **(1) `ran_on_list_of` — done.**
  - Definition (§6.6): a *guest* party filed no lists and its candidates ran
    on the lists of a *host* (`result_entity_id`, party or alliance) under a
    **party-level** arrangement; the guest's poll share is added to the
    host's (same arithmetic as `alliance_member`). Individual members who join
    another party to run on its lists do not make their party a guest.
    Combined labels ("PMP+FD") resolve to the host.
  - Validation: R-40 now requires `result_entity_id` for `ran_on_list_of`;
    new **R-45** (E): only in list elections (parliamentary, European), guest
    and host of type `party`/`alliance`; new **R-46** (E): a
    `result_entity_id` is never itself a `poll_entity_id` in the same file
    (one-step mappings; works before `results.csv` has rows). R-41 already
    checks that the host is a contestant once results exist. R-46 applies to
    every relation; the existing data has no chains.
  - Data: `parl-2024-cd` `pmp` → `ran_on_list_of` `fd`. Sources (media,
    verified against the articles): ziare.com 2024-10-16 (FD president Orban
    and PMP president Tomac filed the FD lists for Bucharest; Tomac heads the
    Senate list and says PMP, Alternativa Dreaptă and PNȚ Maniu-Mihalache run
    under the FD name), ziare.com 2024-10-13 (Orban: all members of the four
    parties run on the FD lists), Antena 3 CNN (same filing). No official
    document states party membership of list candidates (BEC lists show names
    per competitor only), so `source_type = media`. `effective_date` =
    2024-10-13 (announcement). `verified = true`, as the other media-sourced
    rows of this file. `fd` is a competitor in RFCD_1.
  - Other parl-2024-cd parties checked (the entities mapped as
    `not_registered`): **PUSL**: HotNews (2024-10-15) reports five PUSL
    members running on PSD lists, who by law had to join PSD; no party-level
    arrangement was found → stays `not_registered`, source added to `notes`.
    **PRO România**: Victor Ponta ran on a PSD list as an individual; no
    party-level arrangement found → stays `not_registered`, `notes` extended.
    **ADU**: dissolved; its members ran on two ballots → stays
    `not_registered` (see Follow-ups). These are `notes` corrections of
    existing rows of an append-only file (non-key cells, allowed for a
    coordinator-assigned correction task, §2.2); `--against main` passes.
  - Proposed M-1.5 sentence: see Follow-ups (METHODOLOGY is not in scope).
- 2026-11-22: **(2) Person with two roles — done (confirmed the current
  rule).** §4.2 now says: one ID per (person, role); the first role keeps the
  plain slug, the second is a collision and gets the year of the election
  where that role first appears (`john-banu-muscel` /
  `john-banu-muscel-2025`); the ID is reused for the same role later; the
  second row's `notes` name the other ID. Replacing the rule (e.g. a role
  suffix) was rejected because it would rename an existing ID, which the
  append-only rule forbids. No data change.
- 2026-11-22: **(3) Person IDs — done.** §4.2: the given name is the
  **everyday** given name (the one in `short_name`), else the first given name
  on the ballot; the family name is the full ballot family name, all parts
  hyphen-joined. This matches all 69 existing person IDs (checked by reading
  `entities.csv`: e.g. `crin-antonescu`, `lavinia-sandru`, `daniel-funeriu`,
  `nicusor-dan`, `diana-iovanovici-sosoaca`, `ioan-sarmas`,
  `erich-mocanu-gollent`), so no ID changes.
- 2026-11-22: **(4) §7 — done.** Added: the output format
  `path:row: [R-xx] error|warning: message` (paths, file-level findings
  without row, summary line, exit codes, options), `--against REF` (in the
  preamble and in R-34), and the "one finding per problem" list. The T-003
  readings are now in the rule texts: R-01 (final newline, CSV parse; the
  "quote only when needed" style is not validated), R-03 (whitespace in any
  column, wrong field count), R-05 (type of an unregistered election
  directory; reserved `inventory.csv` is a warning), R-20 (`-rN` forbidden on
  parliamentary/European IDs; `local` reserved), R-43 (only when
  `results.csv` has rows), R-53 (missing totals), R-62 (empty entity counts),
  R-63 (raw cells), R-81 (skipped when both dates are empty). These describe
  what the code already did; no code change for them.
- 2026-11-22: **(5) Survey `mode` — done.** New enum value `face_to_face`
  (in-person, CAPI/PAPI not stated) rather than `other` + notes, because
  mode is an analytic variable and face-to-face vs. phone vs. online must stay
  machine-readable. Conventions below the §6.11 table: mode = interview
  channel, not recruitment; "random digital recruitment" → `cawi` if the
  questionnaire is stated to be online, else `other` with the published
  description in `notes` (counts as published for M-5.3); `mixed` for several
  channels. No existing poll data; `pollsters.typical_modes` unchanged (CURS
  `capi;cati` rests on its own statement that its face-to-face work is CAPI).
- 2026-11-22: **(6) `verified` — done.** New §5.3 for the pollster
  registries, written to match what T-005 did: pollsters (all of name,
  website, modes on the pollster's own pages), aliases (variant seen as
  written in the cited source, which clearly refers to the pollster),
  affiliations (`true` only if the source is a party to the relation — the
  pollster, the counterpart — or an official record; third-party media →
  `false`). All 19 existing affiliation rows and the alias rows already
  follow it. Other tables keep the general §5.1 wording (not requested).
- 2026-11-22: **(7) `counterpart_entity_id` — done.** Filled in six rows:
  `verifield` → `usr`, `crin-antonescu`, `nicusor-dan`; `atlasintel` →
  `nicusor-dan`; `cira` → `pnl` (2 rows). Only that cell changed (a
  character-level diff confirmed it); keys unchanged, so R-34 passes. New
  **R-35** (W) flags an affiliation whose `counterpart_name` equals an
  entity's `name`/`short_name` (case-insensitive) while
  `counterpart_entity_id` is empty; before the fill it reported exactly these
  six rows, now none. Other counterparts (media outlets, "Guvernul Ponta",
  associations, persons who are not contestants) are not entities.
- 2026-11-22: **Registry rule.** No registry ID was renamed or removed; the
  only registry edit is the non-key `counterpart_entity_id` cell (amendment
  7). `entity_map.csv` edits: the `pmp` row (relation, target, date, source)
  and two `notes` cells; all keys unchanged.
- 2026-11-22: **Tests.** New failing cases: R-35 (name; short name ignoring
  case), R-40 (`ran_on_list_of` without host), R-41 (host not on ballot; guest
  on ballot), R-45 (guest type, host type, presidential election), R-46
  (target mapped; and without results). New passing cases: R-35 linked,
  `ran_on_list_of` with a party host and with an alliance host, `mode` and
  `typical_modes` with `face_to_face`. Plus the schema-version test. The §10
  worked example and its byte-for-byte fixture are unchanged; the new cases
  mutate copies of it.
- 2026-11-22: Also updated `data/README.md` (one table cell: entity_map
  covers parties on another party's lists). `src/sondaje/cli.py` untouched.
- 2026-11-22: **Verification.** `uv sync`; `uv run pytest` (268 passed);
  `uv run ruff check .` (all checks passed); `uv run ruff format --check .`
  (all formatted); `uv run sondaje validate` and
  `uv run sondaje validate --against main`: 0 errors, 88 warnings (all R-33,
  entities without colour, as on `main`).

## Outcome
DATA_MODEL schema **1.1** (§9.1 history) with all seven amendments done, none
declined:
1. `entity_map.relation = ran_on_list_of` (§6.6) with R-40 extended and new
   R-45/R-46; `parl-2024-cd` `pmp` now maps to `fd` (media sources). PUSL and
   PRO România checked: individual candidacies only, they stay
   `not_registered` (sources in `notes`).
2. One person in two roles: current `-<year>` collision rule confirmed and
   documented (§4.2).
3. Person IDs: everyday given name + full family name (§4.2); matches all
   existing IDs.
4. §7: output format, `--against REF`, one-finding-per-problem, T-003 readings.
5. `mode`: new `face_to_face` value plus conventions (RDR → `cawi`/`other`).
6. `verified` for pollsters/aliases/affiliations (§5.3).
7. `counterpart_entity_id` filled in six rows; new warning R-35 keeps it so.

Key commits: `d787914` (claim), `861843a` (schema 1.1: docs, code, tests),
`6706186` (pmp mapping, PUSL/PRO România notes), `524894e` (counterpart IDs),
plus the final task-file commit.

Known limitations: the M-1.5 wording and the T-020 implementation of
`ran_on_list_of` are proposals (Follow-ups). The PMP evidence is media
reporting of party leaders' statements and the list filing, not an official
membership record (none exists). R-41 for the `pmp` row can only bite once
T-010 commits `parl-2024-cd/results.csv`.
