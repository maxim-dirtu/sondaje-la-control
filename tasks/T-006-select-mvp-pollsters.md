---
id: T-006
title: Select MVP pollsters (2–4)
status: review
phase: 0
depends_on: [T-005]
owner: agent-t006
branch: task/T-006-select-mvp-pollsters
methodology: [M-5.3]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
A documented, reproducible choice of 2–4 pollsters for the MVP, approved by the
owner.

## Context
[ADR-0007](../docs/decisions/0007-mvp-scope.md). This task also works as a
feasibility check for poll collection: it finds out how each house publishes
its results.

## Scope
**In:**
- `docs/reports/pollster-selection.md`: a scorecard of every pollster in the
  T-005 registry that was active in the 3 MVP elections
- A draft ADR `docs/decisions/draft-mvp-pollsters.md` proposing the selection

Scorecard criteria (score each one, with links as evidence):
1. **Coverage (required):** at least one poll inside the final window
   (M-1.3) for **each** of `parl-2024-cd`, `pres-2025-r1`, `pres-2025-r2`.
   Also count the total number of polls in the 120-day windows.
2. **Full topline:** the original publishes every option, including undecided
   and non-response.
3. **Transparency:** the M-5.3 checklist items that are published.
4. **Access:** the original report is available (own site, PDF), and its format
   is one of: text PDF, image or scanned PDF, HTML, media article only.
5. **Popularity:** how often major media cite the house (rough indicator).
6. **Diversity of the set:** different survey modes and client profiles, so
   that house effects can be compared. Describe them factually (ADR-0003).

**Out:**
- Collecting poll data, beyond what is needed to judge the criteria.

## Acceptance criteria
- [x] Every candidate pollster is scored on criteria 1–5, with evidence links.
- [x] The draft ADR proposes 2–4 houses, plus 1–2 reserves, with reasons.
- [x] The report lists the publication formats found for each house. T-011
      needs this to know which extraction paths to support.
- [ ] The owner has approved the selection. The coordinator then numbers the ADR
      and creates one data task per pollster (T-012 onward).

## Follow-ups
- **Owner decisions (draft ADR, Q-A to Q-E):** how CURS is used given the
  21-day window (A1 campaign house / A2 wider window / A3 two houses only);
  accepting media-only sources and expressed toplines for Sociopol; final-poll
  eligibility of polls published on or after election day; diaspora default;
  a 4th house.
- **METHODOLOGY M-1.3 (proposal):** state whether a poll published on or after
  election day can be a house's "final poll" (AtlasIntel 1–3 May 2025,
  published 5 May). Suggested default: eligible only if `published_date` <
  `election_date`; T-025 tests the alternative.
- **METHODOLOGY / T-025 (proposal):** include `window_days` = 28 in the
  sensitivity analysis; it is the smallest round value that covers CURS's
  parliamentary (gap 26) and round-1 (gap 24) polls.
- **DATA_MODEL §6.11 `topline_coverage` (proposal):** clarify how to record a
  publication that shows parties/candidates + "other" summing to 100 but no
  undecided share (Sociopol, CURS, IRSOP, ARA, INSCOP). Is that `full` (every
  option the publication shows) or `partial`?
- **DATA_MODEL §6.10 `format` (proposal):** values for broadcast video (ARA
  23–28 Apr 2025) and for polls known only from a verbal statement reported in
  an article (Sociopol round 2). Today they would be `other` / `html`.
- **T-011:** extraction paths needed by the proposed set: `pdf_text`, `html`,
  and manual double entry from images and rendered PDF pages (report §5).
- **Data tasks (T-012+):** search beyond the indexes (Sociopol 20–22 Nov 2024,
  BCS 26–29 Sep and 7–10 Nov 2024, AtlasIntel 1–3 May 2025 were missing);
  resolve the source disagreements listed in report §7.
- **T-005 Log note is superseded:** "AtlasIntel, CURS and Verifield have
  pre-election polls in all three elections" holds for the 120-day windows
  only, not for the 21-day final window.

## Log
- **2026-11-22: setup.** Worktree `E:\Projects\sondaje-wt\T-006`, branch
  `task/T-006-select-mvp-pollsters` from `main` (ecfde74). Every write used
  absolute worktree paths.
- **2026-11-22: windows.** Final windows from M-1.3 (`fieldwork_end` ≥
  election day − 21): parl 2024-11-10, r1 2025-04-13, r2 2025-04-27. For
  `pres-2025-r2`, R-84 also requires `fieldwork_start` after 2025-05-04, so
  pre-round-1 Dan–Simion head-to-heads (AtlasIntel 28 Apr–1 May, MKOR
  24–27 Apr, Noi, Cetățenii 24–30 Apr) do not count, although their fieldwork
  ends inside the 21-day window. 120-day windows from M-3.2 for the poll counts.
- **2026-11-22: sources.** Discovery: EN/RO Wikipedia wikitext (4 pages) and
  the structured poll lists of all 31 sondajeromania.ro institute pages.
  Gap searches: web search for each house lacking a final-window poll; the
  WordPress REST post lists of curs.ro and inscop.ro for Nov 2024 and
  Apr–May 2025; AtlasIntel's own poll pages (slugs found via search, as the
  site has no crawlable list); bcs.com.ro. Originals opened: every
  final-window poll of AtlasIntel, Sociopol, INSCOP, CIRA, BCS, ARA, IRSOP,
  MKOR, Noi, Cetățenii, FlashData, DataEcho, CURS (r2), Verifield (r2), plus
  CURS's, Verifield's and Avangarde's nearest earlier polls. PDFs checked with
  `pypdf` (text layer) and chart pages rendered with `pypdfium2`, both via
  `uv run --with` (no dependency change). Web Archive availability checked.
  Scratch files in the git-ignored `build/t006/`.
- **2026-11-22: coverage result.** Only AtlasIntel and Sociopol have a
  final-window poll in all three elections. The T-005 note listed AtlasIntel,
  CURS and Verifield; CURS's latest parl/r1 polls end 26/24 days before the
  vote and Verifield's 53/37 days. Sociopol's parliamentary poll (20–22 Nov
  2024, România TV) is not in any index; found by web search. Verifield's
  three November 2024 polls are presidential only (checked in G4Media and
  B1TV). INSCOP has no 2025 pre-election vote-intention poll (inscop.ro post
  list).
- **2026-11-22: scoring choices.** Transparency = the 7 M-5.3 items as
  DATA_MODEL §6.11 would record them for the final-window poll(s); a generic
  "calibration" sentence in AtlasIntel's boilerplate was **not** counted as a
  weighting description. Topline: "Full" only if undecided / non-response
  appear as options on some base; "Expressed" when parties + other sum to 100
  without them. Popularity is qualitative (poll count + outlets seen); no
  citation count was attempted.
- **2026-11-22: proposal.** AtlasIntel + Sociopol (meet coverage) + CURS
  (campaign house, owner option A1); reserves Verifield, MKOR. Reasons and
  trade-offs in the draft ADR. Affiliation records were not used as a
  criterion (ADR-0003; they feed M-5.1d).
- **2026-11-22: not verified.** Vote shares of Noi, Cetățenii (Google Sheets
  charts) and DataEcho (image PDF) were not read; AtlasIntel's own page for
  the 28 Apr–1 May 2025 poll was not located (HotNews carries the slides);
  the Avangarde March 2025 vote-question page was not checked. None of these
  changes the coverage result.

## Outcome
Scorecard and draft ADR delivered; the owner's approval is pending.

- `docs/reports/pollster-selection.md` (c5bfe4d, d03720b): all 15 registered
  houses scored on criteria 1–5, with evidence links to the specific
  final-window polls; criterion 6 (diversity) described factually; publication
  formats and the extraction paths T-011 needs (§5); data-quality findings for
  the poll tasks (§7).
- `docs/decisions/draft-mvp-pollsters.md` (66c703e): proposes **AtlasIntel,
  Sociopol, CURS**, with **Verifield** and **MKOR** as reserves, plus owner
  questions Q-A to Q-E.
- Key result: only AtlasIntel and Sociopol have a final-window poll in all
  three elections. CURS is proposed as a campaign house (owner option A1), as
  its parliamentary and round-1 polls end 26 and 24 days before the vote.
- Checks: `uv run pytest -q` (252 passed), `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run sondaje validate --quiet` (0 errors;
  the warnings come from existing data, which this task did not touch).

Known limitations: poll counts are approximate; the vote shares of
Noi, Cetățenii and DataEcho were not read (charts/images); popularity is a
qualitative indicator. See the Log ("not verified").
