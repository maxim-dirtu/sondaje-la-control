---
id: T-014
title: "Polls: CURS (MVP elections)"
status: review
phase: 1
depends_on: [T-011]
owner: copilot (Sonnet)
branch: task/T-014-polls-curs
methodology: [M-1.1, M-1.3, M-1.4, M-1.5, M-1.7, M-5.3]
created: 2026-11-22
updated: 2026-11-27
---

## Goal
Every published voting-intention poll by **CURS** (`curs`) for the 3 MVP
elections, captured as a **full topline**, with transparency metadata and
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
- Expected volume: about 7 polls. The house publishes national reports as text
  PDFs and as slide images on its own site (curs.ro), and reports 6 of the 7
  M-5.3 transparency items, including weighting.
- Both collection modes occur: face-to-face and CATI. Record the mode per poll
  as the report states it (see DATA_MODEL §6.11 conventions for reports that
  say "face-to-face" without naming CAPI or PAPI).
- The round-2 poll is known through TVR Info only. Record it as media-only
  (`verified = false`) and say so in `notes`.
- The latest parliamentary and round-1 polls end 26 and 24 days before the
  vote, inside the 28-day final window (ADR-0012).
- Every option is recorded exactly as published. Never normalize, round, or
  guess.
- Wording follows [ADR-0003](../docs/decisions/0003-neutral-language.md).

## Scope
**In:**
- `data/polls/curs/` (polls, poll results, archive manifest, inventory)
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
- **Subnational polls (coordinator/owner).** CURS publishes Bucharest-only
  omnibus reports with parliamentary or presidential voting intention
  (Aug 2024, Oct 2024, Feb 2025). They are excluded as `out_of_scope`: the poll
  files have no `population_geo` value for a Bucharest-only sample, and the
  national results are not the right comparison. If the owner wants them, a
  schema/METHODOLOGY change is needed first.
- **Annulled 2024 presidential election.** The 2024 reports ask the round-1
  vote intention for the annulled November 2024 election (not in the
  registry). They are not recorded. A task could add that election if it is
  wanted for house-effect work.
- **`sondaje archive` re-run.** When the first run could not download the
  snapshot (WinError 10061), re-running the command on the same bytes reports
  "kept from the manifest" and does not repeat the snapshot check. Proposal:
  re-check on re-run, or add `--check-only`. Here the three unchecked
  snapshots were compared by hand (see the manifest notes).
- **`sondaje archive` and gzip.** A raw Wayback download with `curl` returns
  gzip bytes unless `--compressed` is used; the tool is not affected, but
  POLL_INGESTION §4 could mention it for manual checks.
- **CURS exit polls** (4 May and 18 May 2025, 1 Dec 2024) are out of scope
  (DATA_MODEL 6.11) and were not opened; the curs.ro posts of two of them are
  in the inventory as `exit_poll`.
- **Option labels for combined lists.** Three 2024 polls print "Alianța PMP - FD"
  or "Alianța Politică PMP - FD". They map to `fd` under the DATA_MODEL 6.6
  rule for combined labels (`option_type = party`). If the coordinator prefers
  a registered alliance entity for this label, the three rows change.

## Log
- **2026-11-27, discovery.** Sources searched: (1) the curs.ro WordPress
  REST API (`/wp-json/wp/v2/posts` for 2024-06-01 to 2025-07-30, 19 posts;
  `/pages`, `/types`, `/search?search=sondaj`): the post list is complete and
  there is no other post type with polls; (2) sondajeromania.ro
  (`/sondaje/2024`, `/sondaje/2025`, `/institute/curs`): lists CURS
  13-27 Aug, 11-16 Oct and 30 Oct-5 Nov 2024 for the parliamentary election
  and 21-25 Jan 2025 (parliamentary row) and 26-30 May 2025; (3) the EN
  Wikipedia pages (parliamentary polling 2024 and the 2025 presidential
  article): the curs.ro posts of Oct and Nov 2024, Jan, Mar and Apr 2025 and
  the TVR Info article; (4) the TVR Info article of 2025-05-13 and web
  searches for the Oct-Nov 2024, April 2025 and May 2025 polls (Adevărul,
  Digi FM, TVR Info). The RO Wikipedia pages could not be read as raw text
  (not used). **Found outside the indexes:** the 6-22 Aug and 10-23 Sep 2024
  reports (parliamentary).
- **Polls per election (own report vs media).** `parl-2024-cd`: 5 polls, all
  from CURS's own text PDFs. `pres-2025-r1`: 3 surveys = 4 poll rows (the
  Jan 2025 report has two candidate lists), all from CURS's own PDFs.
  `pres-2025-r2`: 1 poll, media-only (TVR Info article and the CURS slide it
  embeds), `verified = false`. So 9 of 10 poll rows come from the pollster's
  own report; the T-006 estimate (3 + 3 + 1) missed the two 2024 reports above.
- **Exclusions** (all in the inventory): out of window: Jul 2024 report
  (18-26 Jul), Jun/Jul 2024 report (published 2024-07-03; the PDF was not read
  for dates), Dec 2024 report (10-17 Dec; no voting intention), May 2025
  report (27-30 May); out of scope: women-on-lists survey (no voting
  intention), three Bucharest-only reports, Apr 2025 hypothetical round-2
  pairings (asked before round 1, R-84); exit polls: the 1 Dec 2024 PDF and
  the 5 May 2025 post; duplicates: Adevărul (r2) and Adevărul and Digi FM
  (Apr 2025). Excluded publications were not archived.
- **Double entry (r2 poll, the only hand transcription).** The 8-11 May 2025
  poll exists as a slide image and article text. Pass A: `claude-sonnet-5.5`;
  pass B: `claude-opus-5.5`; each in its own sub-agent, given only the
  archived slide and article, a brief, a copy of POLL_INGESTION.md and
  DATA_MODEL.md, and the entity registry (no values for this poll in the
  protocol copy). `double-entry-diff`: **0 mismatches** on the first run (polls
  and options, every cell). Both passes chose the same share base
  (`expressed_option`), left `population_geo` and `question_type` empty and
  recorded no sponsor. Pass A's rows were reviewed value by value against the
  archived slide and article and committed with rewritten notes. The other
  eight reports are text PDFs and were extracted from the text layer
  (`extract-pdf`, drafts under `build/drafts`), completed by hand where the
  tool missed a label printed over two lines (ADU, Antonescu in Jan 2025,
  Terheș), and reviewed against the rendered pages; a script also checked the
  labels, the values in page order and the sample sizes against the text layer.
- **Choices.**
  1. *Base:* the slides carry a "VOTAT" marker (respondents who named a vote)
     and the shares sum to 100 with no undecided option, so every poll is
     `expressed_option`; base sizes are not published. The Jan 2025 slides
     have no marker and are recorded the same way, with a note.
  2. *Mode:* "față-în-față, la domiciliul respondenților" without CAPI/PAPI →
     `face_to_face` (parl Aug, Sep, Nov 2024); the Oct 2024 and 2025 reports
     say CATI → `cati`; r2: CATI per the article.
  3. *Population:* "populația adultă rezidentă din România" → `adults`,
     `residents`, `domestic`. The r2 article says only "reprezentativ la nivel
     național", so `population_geo` is empty (`target_scope = domestic`).
  4. *Sponsor:* no client in any report or article; `not_disclosed`.
     sondajeromania.ro says "beneficiar nedeclarat"; RO Wikipedia's
     "autofinanțat" is unsourced and not recorded.
  5. *Weighting:* recorded as published for all polls (age of the
     electorate; regional distribution in Mar 2025; round-1 vote in May 2025;
     Jan 2025 says only "ponderate").
  6. *Dates:* `published_date` = date of the curs.ro post (WordPress `date`)
     because the PDFs are undated; r2 = TVR Info `article:published_time`.
  7. *Headline of Jan 2025:* slide 6 (Georgescu list) is the headline because
     the report shows it first; slide 7 (Simion list) is `scenario-b`.
  8. *Overlap:* the posts of 2024-08-25 (fieldwork 6-22 Aug) and 2024-09-15
     (13-27 Aug) are two reports with different values; both are recorded.
  9. *Labels:* "Alianța PMP - FD" / "Alianța Politică PMP - FD" → `fd`
     (combined-label rule, DATA_MODEL 6.6); "Alianța Dreapta Unită (USR – PMP –
     Forța Dreptei)" → `adu`. No entity was added to the registry.
  10. *2024 presidential questions* (annulled election) and the 2025
      hypothetical parliamentary questions are not recorded.
- **Archive.** All 10 documents have a Web Archive snapshot. Save Page Now
  returned HTTP 429 or errors for doc-004, doc-005, doc-006, doc-009 and doc-010
  and the closest existing snapshot was used (dates in the manifest notes).
  doc-005, doc-009 and doc-010: the tool could not download the snapshot to
  compare it; checked by hand (doc-005 and doc-010 identical SHA-256; doc-009
  HTML differs in bytes, same article text and values).
- **Gaps.** `question_type` and `sample_size_expressed` are never published;
  no report states the base size; the r2 poll has no own-site source (media-only,
  `verified = false`); the Jun/Jul 2024 PDF was excluded without reading its
  fieldwork dates (published a month before the window); CURS exit polls were not
  opened.

## Outcome
Status: **review**. Branch `task/T-014-polls-curs`; commits are listed in
`git log main..task/T-014-polls-curs`. Data: `data/polls/curs/` (24 inventory
rows, 10 archived documents, 10 polls, 66 result rows).

| Election | Polls | Source | Notes |
|---|---|---|---|
| `parl-2024-cd` | 5 (6-22 Aug, 13-27 Aug, 10-23 Sep, 11-16 Oct, 30 Oct-5 Nov 2024) | 5 of 5 from CURS's own PDFs, `verified = true` | 2 of 5 not in any index. Latest ends 26 days before the vote (inside the 28-day window). |
| `pres-2025-r1` | 3 surveys, 4 poll rows (21-25 Jan with two candidate lists, 19-22 Mar, 3-10 Apr 2025) | 4 of 4 from CURS's own PDFs, `verified = true` | Latest ends 24 days before the vote. |
| `pres-2025-r2` | 1 (8-11 May 2025) | media-only: TVR Info article + CURS slide, `verified = false`; double entry, 0 mismatches | Not on curs.ro. |

- **Share from the pollster's own source:** 9 of 10 poll rows (the r2 poll is
  media-only).
- **Excluded:** 14 inventory rows (see the Log): 4 out of window, 5 out of
  scope (incl. the Apr 2025 round-2 pairings), 2 exit polls, 3 duplicates.
- **Gaps:** see the Log (no question type, no base size, no own-site source for
  round 2).
- **Verification:** `uv sync; uv run pytest` (352 passed), `uv run ruff check .`
  and `uv run ruff format --check .` pass; `uv run sondaje validate --against
  main`: 0 errors (88 warnings, all R-33 entity colours).
- **Open questions for the owner:** Bucharest-only reports (excluded; do you want
  them?), the Jan 2025 headline list, the two overlapping August 2024 reports,
  and the `fd` mapping of "Alianța PMP - FD".
