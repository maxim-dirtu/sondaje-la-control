---
id: T-015
title: "Polls: Verifield (MVP elections)"
status: review
phase: 1
depends_on: [T-011]
owner: Copilot (Sonnet)
branch: task/T-015-polls-verifield
methodology: [M-1.1, M-1.3, M-1.4, M-1.5, M-1.7, M-3.2, M-5.3]
created: 2026-11-22
updated: 2026-11-27
---

## Goal
Every published voting-intention poll by **Verifield** (`verifield`) for the 3
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
- Expected volume: about 4–5 polls. Verifield is a **campaign house**: only
  its round-2 poll falls in the 28-day final window, so its polls feed the
  campaign metrics (M-3) in all three elections and the final-poll metrics
  for round 2 only. It gets "no grade yet" in the MVP (ADR-0010).
- The round-2 report is a text PDF with a full topline, hosted by HotNews. The
  other polls are known through media (Digi24, Libertatea): record them as
  media-only (`verified = false`) and archive the articles.
- Polls were commissioned by clients that the pollster's publications or the
  media name (see `pollster_affiliations.csv`). Record `sponsor` and
  `sponsor_type` exactly as the source states, and leave them out when it
  doesn't say. Never characterize a client or a result (ADR-0003).
- Every option is recorded exactly as published. Never normalize, round, or
  guess.

## Scope
**In:**
- `data/polls/verifield/` (polls, poll results, archive manifest, inventory)
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
- **Protocol (POLL_INGESTION.md §7, §9):** state a rule for `question_type`
  (this task used `prompted_list` only when the published wording itself
  presents a list: "dintre următorii", "următoarele partide sau alianțe"; empty
  otherwise) and for a base such as "voturi exprimate a celor care se duc la
  vot" (recorded as `other_subset`, as in T-011).
- **Toolkit (`sondaje archive`):** when the snapshot step fails, the download
  stays under the next `document_id` (`data/raw/.../verifield-doc-009.jpg`
  was left behind and the id was then given to another document). Name raw
  files after the document only once the manifest row is written, or remove the
  file on failure. Also, the byte comparison is skipped when the local
  connection to web.archive.org is refused; a retry option would help.
- **Toolkit (`double-entry-diff`):** options are matched by exact label. The
  Oct 2024 slide has two rows labelled "Altul"; the passes agreed, but the
  matching of duplicate labels is untested (suggest matching by
  `option_order` as a fallback).
- **Methodology (M-1.3):** the Aug 2024 poll has no fieldwork dates (R-86); say
  whether such a poll is placed by `published_date` or excluded from windows.
- **Registry:** `app` (Alianța Pentru Patrie) was appended to `entities.csv` and
  to `parl-2024-cd/entity_map.csv` (`not_registered`) with `verified = false`;
  an official source for the party name is still missing (T-004 follow-up).
- **Discovery:** the Facebook posts of the clients (Nicușor Dan, 31 Mar 2025;
  USR, Oct 2024), News.ro's first report of the Oct 2024 poll, and the full
  USR report of the 15–30 Aug 2024 survey were not archived (not reachable
  without a login or not found); a later pass could try them.

## Log
- **2026-11-27, set-up:** worktree `E:\Projects\sondaje-wt\T-015`, branch
  `task/T-015-polls-verifield`. The T-011 poll `verifield-pres-2025-r2-20250506`
  (docs 001 and 002) is kept as it is and not collected again. `data/raw/` of
  a fresh worktree holds no copy of docs 001–002 (git-ignored); not needed.
- **2026-11-27, discovery.** Searched: EN Wikipedia "Opinion polling for the 2024
  Romanian parliamentary election" (no Verifield row), EN Wikipedia "…2025
  Romanian presidential election" (Verifield 14–28 Feb, 24–28 Mar, 6 May), RO
  Wikipedia "Sondaje de opinie pentru alegerile parlamentare din România, 2024"
  (Verifield 7–9 Oct 2024), sondajeromania.ro `/institute/verifield` (parliamentary
  poll of 24–28 Mar 2025 only, which is after `parl-2024-cd`); web searches
  and Google News RSS queries ("Verifield sondaj" with prezidențiale, parlamentare,
  USR, Nicușor Dan, Crin Antonescu, turul doi, and by month from Aug 2024 to
  May 2025); the partner outlets Digi24, Libertatea, G4Media, B1TV, HotNews,
  Radio România, Stiripesurse. Findings outside the indexes: the Libertatea
  article of 2024-08-28 (known from `pollster_affiliations.csv`, not from the
  indexes), the earlier HotNews report of the Oct 2024 poll, the earlier
  Stiripesurse report of the Feb 2025 poll. No Verifield poll was found for Dec
  2024–Jan 2025, April 2025 or after 6 May 2025. The Ziare.com "sondaj intern
  USR" of 2–7 Apr 2025 names no pollster, so it is not a Verifield publication and
  has no inventory row.
- **2026-11-27, scope decisions.** The Verifield waves of 15–30 Aug, 1–6 and 8–14
  Nov, and 20–21 Nov 2024 (Digi24, B1TV, G4Media, HotNews) report a
  presidential question only (presidential 2024 is not in the registry); they are
  `excluded` / `out_of_scope` (no election id). The 24–28 Mar 2025 survey also asked
  a parliamentary question, and the Aug and Oct 2024 surveys also asked
  presidential questions: those parts are not recorded (election not in the
  registry). I could not see the USR/Verifield reports themselves, so I cannot
  rule out a parliamentary question in the 15–30 Aug and November waves that
  the media did not report (open question).
- **2026-11-27, archive.** Docs 003–013 archived with `sondaje archive`.
  Save Page Now was refused or rate-limited on several calls, so docs 006, 007,
  008 and 009 use existing Wayback captures (dates in the manifest notes). Docs
  003 and 008 could not be byte-compared; all HTML snapshots were opened and
  checked for the figures and dates used (manifest notes); the five images are
  byte-identical to their snapshots. Retry of the Feb slide after a failed run
  created doc-013; the orphan raw file left by the failed run was deleted.
- **2026-11-27, registry.** `app` (Alianța Pentru Patrie, printed on the Aug 2024
  slide) was not in `entities.csv`: appended with the Libertatea article as
  source (`verified = false`), plus a `not_registered` row in
  `data/elections/parl-2024-cd/entity_map.csv` so that R-44 holds. This
  second file is outside the literal scope of the task text; the ownership table of
  DATA_MODEL (line 109) lets pollster tasks append to entity maps. Please check it against the
  other T-012–T-014 branches (both append at the end of the file).
- **2026-11-27, double entry** (4 polls × 2 passes; every poll was transcribed
  by hand from images): pass A = sub-agent on **claude-sonnet-5.5**, pass B =
  sub-agent on **claude-opus-5.5**; each given only the archived inputs, a
  copy of the protocol and DATA_MODEL, the registry copies and a brief with the
  document ids (no values; no one saw the other pass). Under
  `build/double-entry/<poll_id>/` (git-ignored). Diff results:
  - `verifield-parl-2024-cd-20240828`: 1 mismatch, `question_type` (A empty, B
    `prompted_list`). Resolved against the slide, whose wording presents "următoarele
    partide sau alianțe": `prompted_list`.
  - `verifield-parl-2024-cd-20241009`: 0 mismatches.
  - `verifield-pres-2025-r1-20250218`: 6 mismatches, the `source_url` of the
    six expressed-option rows (A: the slide, B: the Stiripesurse article).
    Resolved against the archived pages: the slide shows the total base
    only, the expressed-option values are in the Stiripesurse text under
    "cei cu opțiuni exprimate", so B was right and A was corrected.
  - `verifield-pres-2025-r1-20250328`: 0 mismatches.
  After the corrections all four re-diffs reported 0 mismatches.
- **2026-11-27, review against the originals (§8).** Every value, label, order
  and base was compared with the archived slides (the Oct slide upscaled) and
  the HTML. Two corrections to cells on which both passes agreed:
  (1) Oct 2024, label of the PUSL row: both passes typed "PU-SL"; the slide
  prints a middle dot, so the label is "…(PU·SL)" (note in the row).
  (2) Mar 2025: both passes used `expressed_option` for a slide base
  "voturi exprimate a celor care se duc la vot – 59% din esantion"; changed to
  `other_subset` with the label in `notes`, as T-011 did for the same kind of
  base in the round-2 report (p. 5).
  Other points checked: the Oct 2024 values sum to 101.1 and the slide has two
  "Altul" rows (as printed; stated in the poll `notes`); Stiripesurse's list
  for the total base omits Lavinia Șandru (the slide is used); EN Wikipedia gives
  "14–28 Feb 2025", the articles say 14–18 February.
- **2026-11-27, gaps.** Aug 2024 poll: no fieldwork dates, sample size, mode,
  margin of error, weighting or population are published (leaked to Libertatea
  "potrivit surselor"); R-86 warns that it cannot enter M-1.3 windows. Feb 2025:
  no margin of error, no weighting; the expressed base has no published
  respondent count. Mar 2025: the base respondent count is not published. All four
  new polls are media-only (`verified = false`): no Verifield report was found
  for them; the slides are Verifield's, republished by the media. The sponsors
  of all four are stated only by the media (owner decision of 2026-11-27; the
  article is archived and cited in `notes`): USR (party) for Aug and Oct 2024,
  "echipa lui Crin Antonescu" (candidate) for Feb 2025, Nicușor Dan (candidate)
  for Mar 2025.
- **2026-11-27, validation.** `uv run sondaje validate --against main`: 0 errors,
  90 warnings (89 × R-33 entity colours, 1 × R-86 for the Aug 2024 poll).

## Outcome
**Polls recorded (5 in the files; 4 new in this task, 1 from T-011):**

| Election | Polls found | Polls recorded | From Verifield's own publication | Notes |
|---|---|---|---|---|
| `parl-2024-cd` | 2 | 2 (`…-20240828`, `…-20241009`) | 0 of 2 (media-hosted Verifield/USR slides; `verified = false`) | Aug 2024: no fieldwork dates. Oct 2024: 7–9 Oct, n = 1,009, CATI, MoE ±3.09, client USR. |
| `pres-2025-r1` | 2 | 2 (`…-20250218`, `…-20250328`) | 0 of 2 (media-hosted Verifield slides; `verified = false`) | Feb: 14–18 Feb, n = 1,000, CATI, client Crin Antonescu's team, two bases. Mar: 24–28 Mar, n = 1,100, CATI, MoE 2.95, client Nicușor Dan. |
| `pres-2025-r2` | 1 | 1 (`verifield-pres-2025-r2-20250506`, collected by T-011, listed here, not collected again) | 1 of 1 (the report PDF `verifield-doc-001`) | Three bases. |

Total: 5 polls, 1 of 5 (20%) from the pollster's own report; 4 of 5 (80%)
from media republications of Verifield slides.

- **Found outside the indexes:** the Aug 2024 poll (Libertatea) and the earlier
  first publications (HotNews 14 Oct 2024, Stiripesurse 5 Mar 2025).
- **Excluded (8 inventory rows):** 4 × `out_of_scope` (the presidential-only
  waves of Aug–Nov 2024: Digi24, B1TV, G4Media, HotNews); 4 × `duplicate`
  (Libertatea 15 Oct 2024, HotNews 14 Oct 2024, Radio România 31 Mar 2025,
  G4Media 7 May 2025; HotNews and Radio România are archived and linked to
  their polls). Details in the inventory.
- **Gaps:** see the Log; the main ones are the Aug 2024 poll (no fieldwork
  dates, R-86), the missing margin of error for Feb 2025 and Aug 2024, no
  Verifield report for any of the four new polls, and the client posts that were
  not archived.
- **Key commits:** `7453e23` (status), `9881def` (inventory, archive, APP
  entity), `5732cd8` (poll data); see `git log` for the final one.
- **Verification:** `uv run sondaje validate --against main`: 0 errors,
  90 warnings (89 × R-33, 1 × R-86); pytest, ruff check and ruff format
  results in the final report.
