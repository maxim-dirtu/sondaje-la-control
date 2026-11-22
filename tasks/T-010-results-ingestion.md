---
id: T-010
title: "Results ingestion: Parliamentary 2024 and Presidential 2025 (R1, R2)"
status: done
phase: 1
depends_on: [T-002, T-003, T-004]
owner: agent-t010
branch: task/T-010-results-ingestion
methodology: [M-1.4]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
A reproducible downloader that produces the official results of the 3 MVP
elections for the `domestic`, `diaspora`, and `total` scopes.

## Context
- prezenta.roaep.ro (AEP) publishes final per-polling-station results (PV) as
  CSV.
- The open-source project
  [gov2-ro/prezenta.roaep.ro](https://github.com/gov2-ro/prezenta.roaep.ro)
  already downloads these files. Study it for URL patterns and file formats.
  Check its license before reusing any code. If no license is found, reuse
  knowledge only.
- The BEC final official results are the control totals.

## Scope
**In:**
- `src/sondaje/ingest/results.py` and a CLI command
  `sondaje ingest-results <election_id>`
- The results files for `parl-2024-cd` (Chamber of Deputies list vote),
  `pres-2025-r1`, and `pres-2025-r2`
- Raw downloads go to `data/raw/` (git-ignored). Their source URLs and SHA-256
  hashes are recorded in a committed manifest.
- An entity missing from the registry may be appended to the entities file
  (append-only). T-004 is a dependency, so rebase on its merge first; only
  entities that T-004 missed may be appended.

**Out:**
- Results below the national level (county, polling station). Propose them as
  a follow-up.
- The Senate results.

## Acceptance criteria
- [x] Re-running the command reproduces the committed results files exactly.
- [x] domestic + diaspora = total for every entity.
- [x] The valid-vote totals and the per-entity votes match the BEC final report.
      The comparison is recorded in the Log.
- [x] `uv run sondaje validate` passes. Tests cover parsing and aggregation, on
      a small fixture.

## Follow-ups
- **DATA_MODEL §6.9, proposal (schema change):** add a `blank_votes` column.
  Parliamentary PVs count blank ballots ("voturi albe", field g) separately
  from valid and null votes (parl-2024-cd: 38,288). They are neither
  `valid_votes` nor `invalid_votes`, so they are only in `notes` now.
- **DATA_MODEL §6.9, clarification:** `registered_voters` maps to different PV
  fields per election type: parliamentary field a1 (permanent lists only; the
  PV's a also counts supplementary lists, special ballot box extracts, and
  postal-vote lists), presidential field a (permanent lists in Romania, abroad,
  and for postal voting). For `diaspora` the PVs publish a small
  permanent-list figure (5,864; 8,320) that is not a turnout base. State this
  in §6.9 so T-020 does not compute diaspora turnout from it.
- **DATA_MODEL §6.9 / R-51:** parl-2024-cd `diaspora.invalid_votes` is empty
  because the official figures do not add up (see Log). If the coordinator
  prefers a value, the options are the constituency-43 PV figure (4,987, then
  R-51 fails) or a documented derived value (5,288); both need a decision.
- **Archive snapshots:** `archive_url` is empty in the three election manifests
  (optional for elections, R-71). A small follow-up could save Web Archive
  snapshots of the 15 source URLs.
- **Sub-national results (out of scope here):** the pipeline already downloads
  and parses the station PVs and the constituency PVs. County- or
  station-level results would need a new file in DATA_MODEL §2.1.
- **Senate results (out of scope here):** `pv.json` of parl-2024 also holds the
  Senate PVs (category `S`, `S_C`); adding `parl-2024-sen` is a new
  `SOURCES` entry plus a registry row.
- **AGENTS.md §8, proposal:** add `uv run sondaje ingest-results <election_id>`
  to the commands table.
- **T-020 (M-1.4), note:** PNL has no list in the diaspora constituency of
  parl-2024-cd (it is absent from the constituency-43 PV), so its diaspora
  result is 0 and its domestic share is higher than its total share.

## Log
- 2026-11-22: Locked the task (branch `task/T-010-results-ingestion`,
  worktree `sondaje-wt/T-010`).
- 2026-11-22: **gov2-ro/prezenta.roaep.ro.** The repository has no license
  (GitHub API `license: null`, no LICENSE file), so **no code was reused**. Only
  knowledge was taken from its README, `dl-pvs.py`, and `docs/`: the URL
  pattern `https://prezenta.roaep.ro/<type><ddmmyyyy>/data/csv/sicpv/pv_<stage>_<scope>_<category>.csv`,
  the `pv.json` structure (`scopes.<scope>.categories.<category>.table/files`),
  and the CSV column descriptions (BEC decision 161D/2024). The rest was
  learned from the files themselves.
- 2026-11-22: **Access.** prezenta.roaep.ro closes the connection for curl's
  default user agent; the command sends `User-Agent: sondaje-la-control/0.1`.
  A redirect (the site answers 302 for a missing file) is an error. The
  `pv_final_*` CSV names from the gov2-ro docs do not exist for these
  elections; the per-station files are `pv_part_cntry_<cd|prsd>.csv` (latest
  PV version of every station; `pv.json` lists the national CSV as stage
  FINAL) and `pv_part_cntry_<cd|prsd>_c.csv` (postal vote).
- 2026-11-22: **Design choice: what is committed.** The committed values come
  from the **BEC and constituency-bureau final PVs**, read from AEP's
  `pv.json` (SICPV), which holds every one of these PVs in machine-readable
  form: `total` = BEC national PV (`CD_BEC`, `PRSD_BEC`), `diaspora` = PV of
  constituency 43 (`CD_CE_43`; `PRSD_BESVS`), `domestic` = sum of the
  in-country constituency PVs. The per-polling-station PVs are aggregated as an
  independent **cross-check** and never written. Why: the BEC final report is
  authoritative (task Context); the constituency PVs are what the BEC report
  totals (national = Σ constituencies exactly, checked by the command); this
  needs no hand-made reconciliation table, so re-running is fully
  reproducible. Station data could differ from the PVs after bureau
  corrections; here it does not (0 differences, below). The command stops,
  writing nothing, if (a) domestic + diaspora ≠ national for any contestant or
  for the valid votes, (b) any contestant's votes or any totals field used
  differ from the text layer of the BEC national PV PDF, or (c) a contestant
  cannot be resolved to exactly one registry entity.
- 2026-11-22: **Scope rules.** In parliamentary `pv.json`, Bucharest has one
  constituency PV (`CD_BEMB`) and six sector PVs (`CD_BES`) that are its
  sub-totals: the sectors are skipped (42 domestic PVs). In presidential
  `pv.json` there is no Bucharest-wide PV and the six sector PVs are top level
  (41 + 6 = 47 domestic PVs). Postal votes are counted by constituency 43, so
  they are in `diaspora` (DATA_MODEL §6.8).
- 2026-11-22: **Totals fields** (per PV form, from the PV labels):
  parliamentary `registered_voters` = a1, `voters` = b, `valid_votes` = e,
  `invalid_votes` = f, blank votes (g) in `notes`; presidential a, b, c, d.
  Details and the definitional difference are in each `results_totals.csv`
  row's `notes` and in Follow-ups.
- 2026-11-22: **parl-2024-cd diaspora `invalid_votes` left empty.** The BEC
  national PV reports 172,178 null votes; domestic (166,890) + constituency 43
  (4,987) = 171,877; difference 301. The national PV's footnote says its null
  count includes null postal votes and null inner envelopes; 301 equals the
  sum of field b2 of the 141 postal-vote PVs (doc-005). Since the published
  figures do not add up (R-51), the diaspora cell is empty and the row's
  `notes` gives the numbers; `total` keeps the BEC figure. No other field
  disagrees in any election.
- 2026-11-22: **T-004 Follow-up resolved.** The difference T-004 saw
  (`pv_aggregated.json` PSD 2,030,023 vs RFCD_1 2,030,144) is the postal vote:
  `pv_aggregated.json` category `CD` aggregates the 19,918 polling stations
  only; the postal votes are in category `CD_C` (PSD 121). 9,239,605 + 4,036
  postal valid votes = 9,243,641 = BEC. `pv_aggregated.json` is not used.
- 2026-11-22: **Entities.** All contestants resolve to `entities.csv` by name
  (comma-below diacritics, case and "X- Y" spacing normalized), filtered by
  the entity types allowed for the election (R-52): 101 (parl-2024-cd), 11
  (pres-2025-r1), 2 (pres-2025-r2). John-Ion Banu-Muscel resolves to
  `john-banu-muscel` (independent) in parl and `john-banu-muscel-2025`
  (candidate) in pres. **No entity was appended.**
- 2026-11-22: **Dependency.** Added `pypdf` (BSD-3-Clause, pure Python) with
  `uv add pypdf`, to read the text layer of the BEC national PV for the
  automatic control check. `pypdfium2` was used once, ad hoc
  (`uv run --with pypdfium2`), to render the scanned BEC reports for the manual
  check; it is not a dependency.
- 2026-11-22: **Sources archived** (per election, `archive_manifest.csv`,
  raw copies in `data/raw/elections/<id>/`): doc-001 `pv.json` (committed
  values), doc-002 BEC national PV PDF with text layer (automatic check),
  doc-003 BEC final report scan from the BEC website (RFCD_1.pdf, RFT1.pdf,
  RFT1_2.pdf; manual check), doc-004 station CSV, doc-005 postal-vote CSV. All
  15 URLs answered 200; SHA-256 in the manifests.
- 2026-11-22: **BEC cross-check.** (1) Automatic, every run: all contestants'
  votes and the totals fields used match the BEC national PV text (doc-002):
  parl 101 contestants + 5 fields (a1, b, e, f, g), pres-r1 11 + 4, pres-r2
  2 + 4. (2) Manual, on the signed scans (doc-003, rendered page by page): every
  totals field and every contestant's votes match the committed `total` rows
  (parl: all 101, compared by rank on pages 2–8; r1: all 11; r2: both).

  | Election | BEC report | registered_voters | voters | valid_votes | invalid_votes | Contestants |
  |---|---|---|---|---|---|---|
  | parl-2024-cd | RFCD_1, 4.12.2024 | 18,013,618 (a1) | 9,454,678 | 9,243,641 | 172,178 (+38,288 blank) | 101/101 match |
  | pres-2025-r1 | RFT1, 6.05.2025 | 17,996,367 | 9,571,899 | 9,430,274 | 141,388 | 11/11 match |
  | pres-2025-r2 | RFT2, 20.05.2025 | 17,996,537 | 11,641,999 | 11,507,695 | 134,234 | 2/2 match |

  Split by scope (committed; domestic + diaspora = total for every row):

  | Election | valid domestic | valid diaspora | voters domestic | voters diaspora |
  |---|---|---|---|---|
  | parl-2024-cd | 8,475,817 | 767,824 | 8,679,169 | 775,509 |
  | pres-2025-r1 | 8,464,268 | 966,006 | 8,598,729 | 973,170 |
  | pres-2025-r2 | 9,871,299 | 1,636,396 | 9,996,457 | 1,645,542 |

  Per entity (largest; domestic / diaspora / total = BEC): parl `psd`
  1,999,293 / 30,851 / 2,030,144; `aur` 1,463,732 / 201,411 / 1,665,143;
  `pnl` 1,219,810 / 0 / 1,219,810; `usr` 958,897 / 187,460 / 1,146,357;
  `sos` 558,204 / 121,763 / 679,967; `pot` 492,259 / 104,486 / 596,745;
  `udmr` 573,722 / 11,675 / 585,397. pres-r1 `george-simion` 3,275,571 /
  587,190 / 3,862,761; `nicusor-dan` 1,732,379 / 247,388 / 1,979,767;
  `crin-antonescu` 1,827,660 / 65,270 / 1,892,930; `victor-ponta` 1,206,976 /
  23,188 / 1,230,164; `elena-lasconi` 221,213 / 31,508 / 252,721. pres-r2
  `nicusor-dan` 5,445,052 / 723,590 / 6,168,642; `george-simion` 4,426,247 /
  912,806 / 5,339,053.
- 2026-11-22: **Station cross-check: 0 differences** in all three elections,
  per scope, for every contestant, valid votes, and voters. Rows aggregated:
  parl 19,918 station PVs (18,968 domestic, 950 abroad) + 141 postal;
  pres-r1 and pres-r2 19,944 station PVs (18,979 domestic, 965 abroad) + 141
  postal each.
- 2026-11-22: **Reproducibility.** A downloaded file whose SHA-256 equals the
  committed manifest's keeps the manifest's `retrieved_at`; a changed file gets
  today's date and is flagged. `uv run sondaje ingest-results <id> --refresh`
  (fresh download of all 15 files) for the three elections reported
  "unchanged" for all nine committed files and `git status` showed no change.
- 2026-11-22: **Checks.** `uv run sondaje validate`: 0 errors, 88 warnings
  (all R-33, entities without colour, from T-004). `uv run pytest`: 271 passed
  (19 new in `tests/test_ingest_results.py`, offline, on the fictitious
  fixture `tests/fixtures/ingest/parl-2099-cd/` used with the DATA_MODEL §10
  example registry). `ruff check` and `ruff format --check`: clean.

## Outcome
`uv run sondaje ingest-results <election_id>` (`src/sondaje/ingest/results.py`,
registered in `src/sondaje/cli.py`) downloads the official sources of
`parl-2024-cd`, `pres-2025-r1`, and `pres-2025-r2` to `data/raw/`, checks
them, and writes `results.csv`, `results_totals.csv`, and
`archive_manifest.csv` for each election.

| Election | results.csv rows | Contestants | results_totals.csv | Sources archived |
|---|---|---|---|---|
| parl-2024-cd | 303 | 101 | 3 rows | 5 |
| pres-2025-r1 | 33 | 11 | 3 rows | 5 |
| pres-2025-r2 | 6 | 2 | 3 rows | 5 |

Values: BEC/constituency final PVs (`pv.json`); controlled against the BEC
national PV (automatic, text layer; manual, signed scans): all match.
Station-level aggregation agrees exactly. `data/README.md` notes that these
files are generated.

Key commits: `113d02e` (command), `35112ea` (data), `bda186a` (tests and
fixtures); final commits update the README, this file, and the status.

Known limitations: parl-2024-cd `diaspora.invalid_votes` is empty (official
figures do not add up); blank votes are only in `notes`; `archive_url` is
empty; the command is configured for the three MVP elections only (new
elections need a `SOURCES` entry). See Follow-ups.
