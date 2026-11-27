---
id: T-012
title: "Polls: AtlasIntel (MVP elections)"
status: done
phase: 1
depends_on: [T-011]
owner: Copilot (contributor agent)
branch: task/T-012-polls-atlasintel
methodology: [M-1.1, M-1.3, M-1.4, M-1.5, M-1.7, M-5.3]
created: 2026-11-22
updated: 2026-11-27
---

## Goal
Every published voting-intention poll by **AtlasIntel** (`atlasintel`) for the 3
MVP elections, captured as a **full topline**, with transparency metadata and
provenance.

Collection windows (fieldwork end date):
- `parl-2024-cd`: 120 days before 2024-12-01
- `pres-2025-r1`: 120 days before 2025-05-04
- `pres-2025-r2`: head-to-head polls with fieldwork between 2025-05-05 and
  2025-05-17. Pre-R1 hypothetical pairings are not R2 polls (R-84).

## Context
- Follow `docs/POLL_INGESTION.md` (from T-011) step by step.
- [ADR-0012](../docs/decisions/0012-mvp-pollsters.md) and its report
  [pollster-selection.md](../docs/reports/pollster-selection.md) give the
  rules, evidence and publication formats for this house. Read its §5.
- Expected volume: about 9 polls (1 excluded from metrics by M-1.7).
- Reports are on the pollster's own site as PDFs whose values sit in **chart
  images**, so expect manual double entry. Full toplines include "don't know"
  and null/blank, on two bases (use `share_base`).
- **Record the 1–3 May 2025 poll** (published 2025-05-05, after round 1) with
  its true `published_date`. The pipeline excludes it (M-1.7); the UI shows it
  with a notice.
- Some round-2 figures are reported as including the diaspora. Set
  `population_geo` and `target_scope` from the report or its partner (rule 3
  in ADR-0012). Where sources disagree on a methodology item, such as the
  parliamentary margin of error (±2 pp in the report vs ±3% in HotNews), use
  the pollster's report.
- Every option is recorded exactly as published. Never normalize, round, or
  guess.
- Candidates later excluded from the ballot, or who withdrew, are kept as
  published. Code handles them (M-1.5).
- Wording follows [ADR-0003](../docs/decisions/0003-neutral-language.md).

## Scope
**In:**
- `data/polls/atlasintel/` (polls, poll results, archive manifest, inventory)
- Append-only additions to the entity registry (only entities that T-004
  missed)

**Out:**
- Other pollsters, and analysis.

## Acceptance criteria
- [x] The inventory lists every publication found, including polls missing
      from the discovery indexes. Each one is either extracted or excluded
      with a reason.
- [x] Every extracted poll has an archived original (hash + Web Archive URL).
- [x] Every poll transcribed by hand passed the double-entry diff.
- [x] `uv run sondaje validate` reports 0 errors.
- [x] The Outcome reports polls per election, the % from the original source,
      and the gaps.

## Follow-ups
Proposals for the coordinator (shared files and tooling are out of this task's scope).
1. **Tool (T-011), `sondaje archive`:** the Web Archive serves some PDF captures
   `Content-Encoding: gzip`; the snapshot check compares the compressed bytes and
   reports `DIFFERENT` although the decompressed bytes are identical (doc 001,
   checked by hand). It should decompress before comparing. When Save Page Now
   answers 429 or refuses the connection it falls back to an existing snapshot but
   then cannot download it to check it (docs 003-006); a retry or a clearer message
   would help. It should also handle a Google Drive `view` URL (an HTML viewer, not
   the file): doc 002 needed `--file` and a hand-made snapshot of the direct-download URL.
2. **Methodology (M-1.4), diaspora in the round-1 polls:** the 1-3 May report and both
   round-2 reports have a `Diasporă` region column, so those three are
   `residents_and_diaspora` / `total`. The three round-1 polls known only from HotNews
   (10-13 Apr, 17-22 Apr, 28 Apr-1 May) are `domestic` because their articles do not
   say so, but HotNews published diaspora subgroup results of the 17-22 Apr and
   28 Apr-1 May polls, and the RO Wikipedia page notes that the 17-22 Apr sample
   includes the diaspora. **Owner decision (2026-11-27): applied.** 17-22 Apr
   and 28 Apr-1 May are now `residents_and_diaspora` / `total`. Their diaspora
   articles are archived as evidence (`atlasintel-doc-020`, `-021`) and linked
   in the inventory. 10-13 Apr stays `domestic`, because no diaspora results
   were published for it.
3. **Data model (§6.11), sponsor from co-branding:** for the 26-28 Nov and 1-3 May
   polls the report carries the HotNews logo and the title `Atlas-HotNews`
   but no "commissioned by" wording; they are recorded as `HotNews` / `media`.
   **Owner decision (2026-11-27): confirmed.**
   A one-line rule in POLL_INGESTION §0.1 on whether co-branding counts as a client
   statement would avoid case-by-case calls.
4. **Data model (§6.11), headline of a multi-scenario survey:** the 13-15 Mar report
   asks three round-1 scenarios; the headline was chosen as the scenario HotNews
   leads with (without Georgescu, with Simion), because the report labels the
   Georgescu scenario hypothetical. **Owner decision (2026-11-27): confirmed**
   (the headline is the ballot as it stood during fieldwork). A rule for the
   headline of such surveys is missing.
5. **Data model (§6.11), `population`:** the HotNews articles quote AtlasIntel that its
   samples are likely voters, while the reports say "Electoratul din România" and label
   the chart `[Toți alegătorii]`. Each poll follows its own publication (`likely_voters`
   for the three HotNews-only polls, `adults` for the reports), so the field is not
   comparable across the house's polls; M-5.3 does not use it.
6. **Registry:** the 9-12 Nov 2024 report and the round-2 question of the 26-28 Nov
   2024 report are about the 2024 presidential election, which is not registered;
   they would be new polls if that election is added.
7. **Missing reports:** no AtlasIntel report exists on atlasintel.org for 10-13 Apr,
   17-22 Apr and 28 Apr-1 May (the three HotNews-only polls). A search of
   AtlasIntel's social posts, or a request to AtlasIntel, could replace those media
   sources with the pollster's own slides (and give a chart for 10-13 Apr, whose
   round-1 topline is only in prose).

## Log
Dates are 2026-11-27 (the day of the task).

### Discovery (what was searched)
- Indexes: EN Wikipedia "Opinion polling for the 2024 Romanian parliamentary election" and
  "2025 Romanian presidential election" (raw wikitext), RO Wikipedia "Sondaje de opinie ..."
  for both elections, sondajeromania.ro `/sondaje/2024` and `/sondaje/2025`
  (`/institute/atlasintel` returns 404; the 2024 page lists only 26-28 Nov and two April
  2024 European-election polls, the 2025 page lists no AtlasIntel row).
- The pollster's site: the listing behind `atlasintel.org/polls/...` is script-rendered, so the
  public API it calls (`/api/public-polls/<category>`, all 4 categories, 639 polls) was read:
  8 Romanian entries (the 2023 national poll and the June 2024 Bucharest local-election
  report are out of scope; 9-12 Nov 2024 is presidential 2024 only; 5 are in the task).
- Partner outlets: HotNews (each poll's article, found via the Wikipedia citations, and
  the same-day related articles), Libertatea, G4Media; web searches for January 2025 and
  Aug-Nov 2024 AtlasIntel Romania polls found nothing new.
- Polls not on atlasintel.org: 21-24 Feb (a Google Drive copy of the report, linked by RO
  Wikipedia), 10-13 Apr, 17-22 Apr, 28 Apr-1 May (HotNews only).
- Window check: no AtlasIntel voting-intention poll was found for 2024-08-03 to
  2024-11-25 for the parliamentary election (the 9-12 Nov 2024 report asks only about the 2024
  presidential election, see the inventory), nor for 2025-01-04 to 2025-02-20.

### Decisions
- Hypothetical round-2 pairings inside round-1 polls are not round-2 polls (R-84) and are not recorded.
- One survey with several round-1 scenarios gives one poll per scenario (13-15 Mar: 3 polls,
  suffixes `-scenario-georgescu`, `-scenario-gavrila`).
- `question_type` is left empty everywhere: the publications do not say whether options were
  shown or read. `mode` is `other` everywhere (only the recruitment, "Atlas RDR", is described).
- Share base: a chart headed `[Toți alegătorii]` is `all_respondents`; `[Voturi valide]` or the
  ranking "fără cei care nu votează, nu știu, își anulează votul" is `expressed_option`.
- "Vot nul / Nu votez" (one combined bucket in the round-1 charts) is `other_non_vote`.
- Where AtlasIntel's own report and HotNews disagree, the report wins: margin of error of the
  26-28 Nov poll (report ±2 p.p., HotNews ±3%), universe of the 9-12 May poll.
- Sponsor: `HotNews` / `media` where the article says "pentru HotNews" (13-15 Mar by an erratum,
  10-13 Apr, 17-22 Apr, 28 Apr-1 May, both round-2 polls) and, from the pollster's own
  co-branding, for 26-28 Nov and 1-3 May (see Follow-ups 3). The 21-24 Feb poll is `not_disclosed`:
  G4Media says Nicușor Dan *published* the results, not that he commissioned them.
- The 1-3 May poll is recorded with its true `published_date` (2025-05-05); `validate` warns R-83
  as expected.

### Archive
- 19 documents (6 reports, one of them hosted on Google Drive; 9 articles; 4 chart images). Save
  Page Now failed for docs 003-006 (connection refused / HTTP 429 after a burst of requests); the
  tool then used existing snapshots but could not download them; all were checked by hand
  (gunzip + SHA-256) and are identical. Doc 002 (Drive) needed `--file` and a snapshot of the
  direct-download URL. HTML snapshots differ in bytes (dynamic pages); every number-bearing
  line of each downloaded article was found in its snapshot text. The three chart images of
  HotNews are identical to their snapshots.

### Double entry
Every poll was transcribed twice, from the archived files only, by two sub-agents in isolated
folders (`build/double-entry/<poll_id>/pass-a|pass-b/`): **pass A = claude-sonnet-5.5, pass B =
claude-opus-5.5** (the coordinator's rule: hand transcriptions on two different models). After
each pass the diff was run, every mismatch was resolved against the archived original, and the
diff was re-run until it reported 0 mismatches. No share value differed between the passes.

| Poll (document) | Mismatches in the first diff, and resolution |
|---|---|
| parl 26-28 Nov (doc-001) | 2: sponsor A empty/`not_disclosed`, B `HotNews`/`media` → `HotNews`/`media` (report branding, see Follow-ups 3) |
| r1 21-24 Feb (doc-002) | 2: `population` A empty, B `adults` → `adults` (universe label, as in the other reports); `question_type` A empty, B `prompted_list` → empty |
| r1 13-15 Mar (doc-003) | 8: `question_type` ×3 (→ empty); sponsor `HotNews` vs `HotNews.ro` ×3 (→ `HotNews`); scenario text of the headline row A empty, B text (→ the report's scenario title); scenario text of the Gavrilă scenario (→ the report's wording "fără Georgescu și fără Simion") |
| r1 10-13 Apr (doc-013, prose) | 6: labels of the two prose-only options A capitalised, B lowercase (→ the article's lowercase wording); second base A `likely_voters`, B `expressed_option` (→ `expressed_option`: the article says both "cei care votează cu cineva" and "cei care merg sigur la vot"; the heading matches the expressed rankings of the other two HotNews articles; both phrases are quoted in the notes) |
| r1 17-22 Apr (doc-010, 011, 012) | 1: `question_type` A empty, B `prompted_list` → empty |
| r1 28 Apr-1 May (doc-007, 008, 009) | 5: `population_geo` A empty, B `residents` → empty (the article does not say residents); "Cristian Terheș (PNCR)" typed with ț (t-comma) by A and ș by B, in both bases → ș (image and registry) |
| r1 1-3 May (doc-004) | 3: `question_type` (→ empty); sponsor and `sponsor_type` A empty/`not_disclosed`, B `HotNews`/`media` (→ `HotNews`/`media`, Follow-ups 3) |
| r2 9-12 May (doc-005) | 1: `population` A empty, B `adults` → `adults` (the report's universe wins over HotNews's wording) |
| r2 13-15 May (doc-006) | 0 |

Both passes agreed on `population_geo = residents_and_diaspora` for 1-3 May and both round-2
polls (the crosstab has a `Diasporă` region; checked on the rendered pages) and on `mode = other`.

### Review (POLL_INGESTION §8)
Every recorded value was re-checked by the contributor against the archived chart pages and
images (the first-round and round-2 pages of the reports, the HotNews chart images, and the
article prose for 10-13 Apr). Options and order are as published (no completed or implied
options); labels are verbatim with comma-below diacritics; each source disagreement is in `notes`.

### Gaps
- No AtlasIntel report for 10-13 Apr, 17-22 Apr, 28 Apr-1 May (HotNews only, `verified = false`);
  the 10-13 Apr round-1 topline is only in prose (`topline_coverage = partial`: a combined
  non-vote bucket and "alt candidat", no all-respondents values for Funeriu and Șandru).
- Question text is missing for the parliamentary poll (the report prints none). Weighting is not
  described in any publication. The size of the `expressed_option` base is never published.
- `published_date` of the reports is the date of the AtlasIntel listing or of the first partner
  article; no report prints a date. For 28 Apr-1 May the pollster-selection report mentions
  "1-2 May"; the first publication found is the HotNews article of 2025-05-02 06:04 (+03:00).

- **2026-11-27, owner decisions (coordinator):** diaspora (question 2),
  co-branding (question 3) and headline (question 4) under *Follow-ups*, all
  applied or confirmed. Two diaspora-subgroup articles were archived, and
  their inventory rows (one new, one previously `excluded`/`out_of_scope`)
  are now `verified` and linked to their polls. The inventory has 24 rows
  and the archive 21 documents.

## Outcome
Status: done (merged in #18). 9 AtlasIntel surveys recorded as **11 polls** (13-15 Mar has three scenarios)
with **159 result rows**; inventory 23 rows (13 verified, 10 excluded); 19 archived documents;
`uv run sondaje validate --against main` reports 0 errors (the only AtlasIntel warning is the
expected R-83 for the 1-3 May poll). Commits: `T-012: set status in-progress, owner and branch`,
`T-012: record AtlasIntel polls (9 surveys, 11 polls), inventory and archive manifest`, and the
commit of this file.

| Election | Surveys found → recorded | Polls | From the pollster's own report | Excluded publications |
|---|---|---|---|---|
| `parl-2024-cd` | 1 → 1 (26-28 Nov) | 1 | 1 of 1 (100%) | 9-12 Nov 2024 report (2024 presidential only, `out_of_scope`); HotNews article (`duplicate`) |
| `pres-2025-r1` | 6 → 6 (21-24 Feb, 13-15 Mar, 10-13 Apr, 17-22 Apr, 28 Apr-1 May, 1-3 May) | 8 | 3 of 6 surveys (5 of 8 polls): 21-24 Feb (Drive copy), 13-15 Mar, 1-3 May; the other 3 from HotNews | HotNews approval-ratings article and diaspora-subgroup article (`out_of_scope`); G4Media, 2 HotNews articles, Libertatea, HotNews trend article (`duplicate`) |
| `pres-2025-r2` | 2 → 2 (9-12 May, 13-15 May) | 2 | 2 of 2 (100%) | 2 HotNews articles (`duplicate`) |
| **Total** | **9 → 9** | **11** | **6 of 9 surveys (8 of 11 polls, 67% / 73%)** | 10 inventory rows |

- 1-3 May 2025 (published 2025-05-05, after the round-1 vote) is recorded with its true date;
  the 28 Apr-1 May poll (published 2025-05-02) is the round-1 final poll before election day.
- Polls found outside the discovery indexes: none of the 9 surveys was missing from the
  Wikipedia pages (the sondajeromania.ro 2025 page lists no AtlasIntel row); the report PDFs on
  atlasintel.org were found through the site's API, and the two non-headline scenario polls of
  13-15 Mar are in no index.
- Entity registry: nothing added (every polled candidate and party was already registered).
- Gaps: see the Log. Open questions for the owner: Follow-ups 2 and 3.
