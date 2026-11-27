---
id: T-016
title: "Sponsor source: credit M-5.3 'client disclosed' only when the pollster discloses it"
status: done
phase: 1
depends_on: [T-012, T-013, T-014, T-015]
owner: copilot-t016
branch: task/T-016-sponsor-source
methodology: [M-5.3, M-5.1d]
created: 2026-11-27
updated: 2026-11-28
---

## Goal
The data records **who** named a poll's client, so that the transparency
checklist (M-5.3) credits only the pollster's own disclosure. Media-sourced
clients still count for party-commissioned flags (M-5.1d).

## Context
- Owner decision, 2026-11-27 (T-011, question 2): when the pollster's
  publication names no client, a client stated explicitly by the media is
  recorded as the sponsor
  ([POLL_INGESTION.md §0.1](../docs/POLL_INGESTION.md)). First case: Verifield
  round 2 (`verifield-pres-2025-r2-20250506`, client named by HotNews).
- M-5.3 currently maps "client/sponsor published" to
  `sponsor_type ≠ not_disclosed` (DATA_MODEL §6.11). After that decision, a
  pollster would get credit for a disclosure that the media made.
- Waits for T-012…T-015, so that every poll file is migrated once.

## Scope
**In:**
- A way to record the sponsor's source in `polls.csv`, e.g. a
  `sponsor_source` column (`pollster` | `media`, empty when
  `not_disclosed`). The design is part of the task; record it in the Log.
- **Shared files allowed:** `docs/DATA_MODEL.md` (column, rule, changelog,
  M-5.3 mapping) and `docs/METHODOLOGY.md` (M-5.3 wording).
- Schema and validation code, with tests. Migration of every
  `data/polls/*/polls.csv`, filling the new column from each poll's sources
  and `notes`. Never guessed: an unclear case is flagged in the Log.
- `docs/POLL_INGESTION.md` §0.1 updated to fill the new column.

**Out:**
- Computing the transparency score (T-043).

## Acceptance criteria
- [x] M-5.3 credits "client/sponsor" only for a pollster-disclosed client;
      METHODOLOGY and DATA_MODEL say so.
- [x] Every existing poll has the new field filled, or empty for
      `not_disclosed`, with validation rules and tests.
- [x] `uv run sondaje validate --against main`, pytest, and ruff pass.

## Follow-ups
Proposals for the coordinator (no new task IDs created):

1. **T-018 item 2 (co-branding):** DATA_MODEL §6.11 and POLL_INGESTION §0.1
   now say that the pollster's co-branding with the client counts as the
   pollster naming the client (`sponsor_source = pollster`). T-018 should
   write its "co-branding counts as the client" convention in the same words,
   and can then drop the stale "(open question for the owner)" from the notes
   of `atlasintel-pres-2025-r1-20250503` (the owner confirmed it on
   2026-11-27; this task did not edit any `notes` cell).
2. **Capital's Sociopol PDF** (T-013 Follow-up 1): if it is recovered and its
   methodology page reads "Realizat pentru România TV", set
   `sociopol-pres-2025-r1-20250411` to `sponsor_source = pollster` (see Log,
   open question 1).
3. **"Potrivit surselor" clients:** POLL_INGESTION §0.1 never records a
   rumoured client, but `verifield-parl-2024-cd-20240828` records USR from
   Libertatea's "potrivit surselor Libertatea" (T-015, merged). The owner may
   want §0.1 to say whether an outlet attributing the client to its sources
   counts as "states it explicitly" (open question 2).
4. **T-043 (transparency score):** read the client item as
   `sponsor_source = pollster`, not `sponsor_type ≠ not_disclosed`
   (DATA_MODEL §6.11 mapping). With today's data, 10 of 45 polls earn it.

## Log
- **2026-11-28 Resume.** A previous agent (cancelled after ~5 min) had
  committed the start and left uncommitted edits in DATA_MODEL §6.11
  (column, conventions, M-5.3 mapping), `schema.py` and `rules_polls.py`
  (R-65 extension, R-79). Reviewed: sound, kept and committed; rebased on
  `main` (26baf3a). Owner set to `copilot-t016`.
- **2026-11-28 Design.** A new column `polls.sponsor_source`
  (`pollster` | `media`, empty iff `sponsor_type = not_disclosed`), placed
  before the provenance block (DATA_MODEL §9). Alternatives rejected:
  (a) a new `sponsor_type` value would lose the client's type, which M-5.1d
  needs; (b) a document reference column would not say who named the client
  when the cited document is a media page that hosts the pollster's report
  (e.g. `verifield-doc-001`), and `notes` already cite the documents;
  (c) a boolean `sponsor_published_by_pollster` reads the same but leaves no
  room for a third value later (e.g. a regulator). Two values were enough for
  all 45 polls: `media` covers everyone who is not the pollster (an outlet,
  the client outlet, the client presenting the poll, a regulator quoting a
  broadcast), because M-5.3 only asks whether the pollster disclosed it.
  `self` also needs a value (who stated the self-funding). Schema 1.3.
- **2026-11-28 Rules.** R-65 (E) extended: `sponsor_source` set iff
  `sponsor_type ≠ not_disclosed`. New R-79 (W, last free number of §7.5):
  `sponsor_source = media` without `notes` (POLL_INGESTION §0.1 asks for the
  citing notes; a warning, like R-69/R-77). Tests: 5 failing cases (R-65 ×3,
  R-03 bad enum, R-79) and 2 passing cases (cited media, `self`).
- **2026-11-28 Migration.** A throw-away script (under `build/`, git-ignored)
  added the column with `csvio.write_rows`; a check confirmed that removing
  the column gives back the old files byte for byte. Each value was decided
  from the poll's `notes`, the T-012…T-015 Logs and, where these left a
  doubt, the archived snapshots (Web Archive) of the documents, opened on
  2026-11-28:
  - Sociopol slides `sociopol-doc-019` (17–21 Mar) and `-030` (21–23 Apr):
    no client on the slide → `media` (client from Gândul / România TV text).
  - `sociopol-doc-033` (24–26 Apr): România TV's own on-screen "DATE TEHNICE
    SONDAJ" graphic → `media`.
  - `sociopol-doc-001` (round 2): the director is quoted verbatim, "Este
    comandat de România TV." → `pollster`.
  - AtlasIntel charts `atlasintel-doc-008`, `-009`, `-011` (HotNews articles
    of 22 Apr and 1 May): AtlasIntel pages footed "Sondaj Atlas - Alegeri
    Prezidențiale", no HotNews branding → `media` (client from HotNews text).
  - Verifield slides `verifield-doc-004`, `-011`, `-013`: no client →
    `media`; `verifield-doc-006` is a USR-branded slide crediting Verifield
    (the client's slide) → `media`.

  | poll_id | sponsor_type | sponsor_source | Who named the client |
  |---|---|---|---|
  | atlasintel-parl-2024-cd-20241128 | media | pollster | report co-branded "Sondaj Atlas-HotNews" (doc-001; owner decision) |
  | atlasintel-pres-2025-r1-20250224 | not_disclosed | (empty) | none |
  | atlasintel-pres-2025-r1-20250315 (+ scenario-georgescu, scenario-gavrila) | media | pollster | HotNews logo on the report cover (doc-003) |
  | atlasintel-pres-2025-r1-20250413 | media | media | HotNews article only, "pentru Hotnews" (doc-013) |
  | atlasintel-pres-2025-r1-20250422 | media | media | HotNews article, "realizat pentru HotNews" (doc-010); charts unbranded |
  | atlasintel-pres-2025-r1-20250501 | media | media | HotNews article lead, "pentru HotNews" (doc-007); charts unbranded |
  | atlasintel-pres-2025-r1-20250503 | media | pollster | HotNews logo on the report cover (doc-004) |
  | atlasintel-pres-2025-r2-20250512 | media | pollster | HotNews logo on the report cover (doc-005) |
  | atlasintel-pres-2025-r2-20250515 | media | pollster | report cover logo and footer "Sondaj Atlas - HotNews" (doc-006) |
  | curs-* (10 polls) | not_disclosed | (empty) | none |
  | sociopol-parl-2024-cd-20241018 | not_disclosed | (empty) | none |
  | sociopol-parl-2024-cd-20241122 | not_disclosed | (empty) | none |
  | sociopol-pres-2025-r1-20250115 (+ scenario-b) | media | media | client's article, "realizat la comanda Romania TV" (doc-007) |
  | sociopol-pres-2025-r1-20250130 (+ scenario-b) | media | media | Știripesurse article, "la comanda România TV" (doc-009) |
  | sociopol-pres-2025-r1-20250214 (+ scenario-b) | media | media | client's article lead, "pentru România TV" (doc-010) |
  | sociopol-pres-2025-r1-20250307 (+ scenario-b) | media | media | client's article, "realizat la comanda România TV" (doc-015) |
  | sociopol-pres-2025-r1-20250318 | not_disclosed | (empty) | none |
  | sociopol-pres-2025-r1-20250321 | media | media | Gândul article (doc-018); the Sociopol slide names none |
  | sociopol-pres-2025-r1-20250404 | media | media | CNA decision quoting România TV's on-screen data (doc-022) |
  | sociopol-pres-2025-r1-20250411 | media | media | EVZ "date tehnice" (doc-026); **open question 1** |
  | sociopol-pres-2025-r1-20250417 | media | pollster | Sociopol report, methodology page "Realizat pentru România TV" (doc-027) |
  | sociopol-pres-2025-r1-20250423 | media | media | client's article (doc-029); the Sociopol slide names none |
  | sociopol-pres-2025-r1-20250426 | media | media | România TV on-screen technical data (doc-033) |
  | sociopol-pres-2025-r1-20250430 | media | pollster | Sociopol report, methodology page 4 (doc-034) |
  | sociopol-pres-2025-r2-20250512 | media | pollster | director quoted verbatim on România TV (doc-001) |
  | verifield-parl-2024-cd-20240828 | party | media | Libertatea, "potrivit surselor Libertatea" (doc-003); **open question 2** |
  | verifield-parl-2024-cd-20241009 | party | media | Digi24 / HotNews "la comanda USR" (doc-005, -007); USR's slide |
  | verifield-pres-2025-r1-20250218 | candidate | media | Libertatea, "comandat de echipa lui Crin Antonescu" |
  | verifield-pres-2025-r1-20250328 | candidate | media | Libertatea, "la comanda lui Nicușor Dan" (doc-010) |
  | verifield-pres-2025-r2-20250506 | candidate | media | HotNews headline (doc-002); the report names none |

  Totals: 10 `pollster`, 21 `media`, 14 empty (`not_disclosed`).
- **2026-11-28 Open question 1 (`sociopol-pres-2025-r1-20250411`).** EVZ's
  "Sondaj Sociopol, date tehnice" block (doc-026) reproduces the items of
  Sociopol's methodology page almost word for word (universe, sample,
  fieldwork, sample type, method, margin, weighting, rounding, other errors),
  and opens with "Sondajul a fost realizat pentru România TV." Sociopol's own
  pages read "Realizat pentru: România TV" (seen on doc-027). The client line
  is therefore probably copied from Sociopol, but it is reworded and the
  Sociopol document of this poll was not archived (Capital's PDF was
  unreachable, T-013). Recorded as `media` (the conservative value: no credit
  without the pollster's own document); `pollster` if the owner reads the
  block as Sociopol's technical sheet republished.
- **2026-11-28 Open question 2 (`verifield-parl-2024-cd-20240828`).** The
  client comes from "potrivit surselor Libertatea". Kept as recorded by T-015
  (`party` / USR) with `sponsor_source = media`; whether such a client meets
  §0.1's "states it explicitly" is for the owner (Follow-up 3).
- **2026-11-28 Docs.** DATA_MODEL: version 1.3, column row, `sponsor` and
  `sponsor_type` descriptions, M-5.3 mapping and conventions (§6.11), header
  (§6.14), R-65 and R-79 (§7.5), §8 rows M-5.1d / M-5.3, changelog (§9.1),
  worked example row and R-65 sentence (§10). METHODOLOGY M-5.3: client item
  only for a pollster disclosure; M-5.1d uses every recorded client.
  POLL_INGESTION §0.1: how to fill `sponsor_source`; §11 Verifield example
  names the value. No `notes` cell was edited.
- **2026-11-28 Checks.** `uv sync`; `uv run pytest` (359 passed);
  `uv run ruff check .` (passed); `uv run ruff format --check .` (passed);
  `uv run sondaje validate --against main` (0 errors, 91 warnings, none
  R-65/R-79).

## Outcome
**Done.** `polls.csv` gains `sponsor_source` (schema 1.3): `pollster` when the
pollster's own material names the client (including co-branding and a quoted
statement of its director), `media` when only an outlet or the client does,
empty for `not_disclosed`. M-5.3 credits the client item only for
`pollster`; M-5.1d keeps reading `sponsor_type`. R-65 enforces the pairing,
R-79 warns on a `media` value without citing notes. All 45 polls migrated
(10 `pollster`, 21 `media`, 14 empty), plus the test fixtures and the §10
worked example.

**Key commits:** `0d593c2` start; `ea0d53f` column and rules; `2622179`
migration; `2a2981b` docs and tests; final commit with Log/Outcome.

**Known limitations:** two values decided conservatively and flagged for the
owner (Log, open questions 1 and 2). `notes` cells were not rewritten, so
the stale "(open question for the owner)" on
`atlasintel-pres-2025-r1-20250503` stays (Follow-up 1).
