---
id: T-018
title: Protocol and data-model clarifications from the first collection round
status: done
phase: 1
depends_on: [T-016]
owner: copilot-agent
branch: task/T-018-protocol-clarifications
methodology: [M-1.4]
created: 2026-11-27
updated: 2026-11-28
---

## Goal
Write down the conventions that T-012…T-015 and the owner decided case by
case, so the next collection round applies them the same way.

## Context
The owner decided these cases in chat on 2026-11-27. The decisions are on PRs
#13, #16, #17, #18 and #19. This task writes them down; it does not reopen
them. It waits for T-016, which also edits POLL_INGESTION §0.1 and
DATA_MODEL §6.11.

## Scope
**In:** `docs/POLL_INGESTION.md` and `docs/DATA_MODEL.md` (shared files
allowed for this task); data fixes only where a convention below shows that
an existing row is inconsistent.

1. **Headline of a multi-list survey:** the list that matches the ballot as
   it stood during fieldwork (CURS Jan 2025: Georgescu list; AtlasIntel
   13–15 Mar 2025: list without Georgescu).
2. **Co-branding as a client statement:** "Atlas-HotNews" or the outlet's logo
   on the pollster's own report counts as the client (AtlasIntel).
3. **Diaspora evidence (M-1.4):** published diaspora subgroup results of the
   same poll count as an explicit statement that the sample includes the
   diaspora. Archive that publication as evidence (AtlasIntel 17–22 Apr and
   28 Apr–1 May).
4. **Share bases:**
   - the only published base "valid answers of likely voters" →
     `expressed_option`, with the wording in `notes` (Sociopol);
   - a second such base published next to an expressed base →
     `other_subset` (Verifield).
5. **`question_type = prompted_list`** only when the published wording lists
   the options (Verifield).
6. **"Telephone interviews"** without the word CATI → `cati`; graphics that
   show candidates only as photos → label from the caption, explained in
   `notes` (Sociopol).
7. **`population`** used consistently: `likely_voters` from a media quote vs
   `adults` from the report (AtlasIntel). Pick one rule and fix the rows.
8. **Subnational polls** (CURS Bucharest-only reports): record the owner's
   MVP decision (excluded as `out_of_scope`) and how a later phase would add
   them.
9. **Polls without fieldwork dates** (Verifield Aug 2024): recorded, outside
   the M-1.3 windows (R-86). Say so in the protocol.

**Out:** methodology changes beyond writing down these decisions.

## Acceptance criteria
- [x] Each convention is written in POLL_INGESTION.md, or in DATA_MODEL.md
      where it concerns a column.
- [x] Every existing row that contradicts a convention is fixed, and each fix
      is logged.
- [x] `uv run sondaje validate --against main`, pytest and ruff pass.

## Follow-ups
Proposals for the coordinator (no new task IDs created):

1. **Owner confirmation of two judgement calls** (see Log, open questions 1
   and 2): the `population` rule that moved three AtlasIntel rows, and the
   reading of "din următorii" as `prompted_list` for two Sociopol rows.
2. **Sociopol 3–7 Mar 2025 headline** (open question 3): decide which list is
   the headline when the candidacy was disputed during fieldwork.
3. **Subnational phase:** when the owner wants Bucharest-only (or other
   regional) polls, a task has to add the schema change, the area-level
   results, and the M-1.4 methodology change that POLL_INGESTION §0.5 item 8
   lists; the three CURS inventory rows (`out_of_scope`) are not archived yet.
4. **Validation idea (T-003 area):** a warning for `question_type =
   prompted_list` with an empty `question_wording` would catch a wording-less
   `prompted_list` (none exists today: the Sociopol and Verifield rows that have
   the type all quote their wording).

## Log
- 2026-11-28 · Locked the task: branch `task/T-018-protocol-clarifications`,
  worktree `E:\Projects\sondaje-wt\T-018`. Read the owner decisions on PRs #13,
  #16, #17, #18, #19 and #21 and Follow-ups of T-012…T-016.
- 2026-11-28 · The nine conventions are written in POLL_INGESTION §0.5 (new),
  with pointers in §0.1, §0.4, §3 and §8, and in DATA_MODEL §6.11 (`headline`,
  `fieldwork_end`, `population` + conventions, `population_geo`,
  `question_type`, `mode`, `sponsor_source`), §6.12 (`share_base`) and §6.13
  (`out_of_scope`). No schema change (no column, enum value or rule), so the
  schema version stays 1.3.
- 2026-11-28 · Co-branding (item 2) is worded as the `sponsor_source =
  pollster` bullet of T-016 (the pollster's co-branding with the client on its
  own report counts), as T-016 Follow-up 1 asked.
- 2026-11-28 · Checked every `polls.csv` row of `atlasintel` (11), `sociopol`
  (19), `curs` (10) and `verifield` (5), and the share bases of their
  `poll_results.csv`, against the nine conventions. The sources are the
  `notes` of each row (the raw files are not in the worktree); for the one
  point where the notes were not enough, I read the HotNews article of
  17–22 Apr 2025 again.

Data fixes (the only changes to data; commit "fix rows that contradict the
conventions"):

| poll_id | column | old | new | reason |
|---|---|---|---|---|
| `atlasintel-pres-2025-r1-20250413` | `population` | `likely_voters` | `adults` | Item 7: the article states the universe "electoratul din România"; the quote about the house's samples is general. Quote kept in `notes`. |
| `atlasintel-pres-2025-r1-20250422` | `population` | `likely_voters` | empty | Item 7: the article states no universe (the chart label "[Toți alegătorii]" labels a base) and only quotes AtlasIntel's founder on its samples in general. Quote kept in `notes`. |
| `atlasintel-pres-2025-r1-20250501` | `population` | `likely_voters` | `adults` | Item 7: the article states the universe "electoratul din România". Quote kept in `notes`. |
| `atlasintel-pres-2025-r1-20250503` | `notes` | "(open question for the owner)" | "(owner decision 2026-11-27: co-branding counts as a client statement, POLL_INGESTION §0.1)" | T-016 Follow-up 1: stale text; the owner confirmed it. No value changed. |
| `verifield-pres-2025-r1-20250328` | `poll_results.share_base` (9 rows, orders 1–9) | `other_subset` | `expressed_option` | Item 4: the slide's only base is "voturi exprimate a celor care se duc la vot – 59% din esantion". The base wording was already in each row's `notes`; the poll's `notes` now explain the choice. |
| `sociopol-pres-2025-r1-20250115` | `question_type` | empty | `prompted_list` | Item 5: the quoted wording says "cu cine ati vota din urmatorii?", the same construction as the "dintre următorii" rows. `notes` say why. |
| `sociopol-pres-2025-r1-20250130` | `question_type` | empty | `prompted_list` | Same reason and wording as above. |

Rows checked and left as they are:
- Item 1: CURS 21–25 Jan 2025 (Georgescu list = headline) and AtlasIntel
  13–15 Mar 2025 (without Georgescu) agree. Sociopol Jan and Feb 2025
  (Georgescu list = headline) are consistent with the CURS case; Sociopol
  3–7 Mar 2025: see open question 3.
- Item 2: the seven AtlasIntel polls with the HotNews branding on the report
  (28 Nov 2024, 13–15 Mar ×3, 1–3 May, 9–12 May, 13–15 May 2025) are
  `media` / `pollster`. No other house has co-branding.
- Item 3: 17–22 Apr and 28 Apr–1 May are `residents_and_diaspora` with their
  evidence documents (`atlasintel-doc-020`, `-021`, inventory `verified`);
  10–13 Apr is `domestic`. No other poll of the four houses has published
  diaspora subgroup results in its archived sources.
- Item 4: Sociopol: every poll is `expressed_option`. Verifield 6 May 2025: the
  expressed base is `expressed_option`, the base "of respondents who say they
  will vote" is `other_subset` (a second base). Verifield 14–18 Feb 2025:
  `all_respondents` + `expressed_option`.
- Item 5: the four Verifield and nine Sociopol rows that had `prompted_list`
  before this task all quote a wording that lists the options; AtlasIntel
  ("aceștia ar fi candidații") and CURS stay empty. The scenario-b rows of
  Sociopol Jan 2025 have no quoted wording, so they stay empty.
- Item 6: every "interviuri telefonice" row is already `cati` (e.g. Sociopol
  7 Mar, 18 Mar, 31 Mar–4 Apr, 24–26 Apr 2025); the photo-only graphics already
  say in `notes` which document gives the labels.
- Item 7: Sociopol (`adults` = the stated universe; the "decided voters"
  filter is a share base) and CURS (`adults`) agree with the rule; Verifield
  states no universe (empty). AtlasIntel reports: `adults`.
- Item 8: the three CURS Bucharest-only reports (Aug 2024, Oct 2024, Feb 2025)
  are `out_of_scope` with the area in `notes`. No other house has one.
- Item 9: only `verifield-parl-2024-cd-20240828` has no fieldwork dates (R-86,
  expected); `poll_id` uses `published_date`.

Open questions (nothing was changed for them beyond the rows above):
1. **`population` rule.** I picked "the universe this poll's publication
   states; a general statement about the house's samples is not enough". The
   alternative reading takes the AtlasIntel founder's quote ("samples target
   likely voters, not the whole adult population") as the answer for every
   AtlasIntel poll, which would make the five reports `likely_voters` as well,
   against their own "Electoratul din România". The owner should confirm the
   rule; the field is not used by M-5.3.
2. **"din următorii" = `prompted_list`.** The conventions as given by the task
   say "only when the wording lists the options". I applied the rule in both
   directions, as T-015 did, which turns two Sociopol rows. If the owner reads
   the rule as one-directional only, those two rows go back to empty.
3. **Sociopol 3–7 Mar 2025 headline.** The headline is the Georgescu list
   ("dacă lui Călin Georgescu i se permite candidatura") and scenario-b is
   without him. The archived sources do not show what the ballot was during
   those days; the wording itself shows that the candidacy was disputed. Not
   changed, because the ballot status would have to be inferred. If the owner
   decides it was already off the ballot, the two rows swap `headline`.

## Outcome
Nine conventions are written down: POLL_INGESTION §0.5 (new) holds all nine,
with pointers from §0.1, §0.4, §3 and §8; DATA_MODEL §6.11–§6.13 carry the
column rules (`headline`, `fieldwork_end`, `population`, `population_geo`,
`question_type`, `mode`, `sponsor_source`, `share_base`, `out_of_scope`). No
schema change, no version bump. Fourteen data values changed (table in the
Log): three AtlasIntel `population` values, nine `share_base` values of one
Verifield poll, and two Sociopol `question_type` values; seven `notes` cells
were updated to match (one of them only drops the stale "open question" text).

Checks (worktree, 2026-11-28): `uv sync` ok; `uv run pytest` 423 passed;
`uv run ruff check .` passed; `uv run ruff format --check .` passed (39 files);
`uv run sondaje validate --against main` 0 errors, 91 warnings (89 × R-33
colours, 1 × R-83, 1 × R-86; all expected).

Known limits: the raw files are not in the worktree, so rows were checked
against their `notes` (and one article re-read); the three open questions above
need the owner.
