---
id: T-011
title: Poll ingestion toolkit
status: done
phase: 1
depends_on: [T-001, T-002, T-006]
owner: copilot-t011
branch: task/T-011-poll-ingestion-toolkit
methodology: [M-1.1, M-5.3]
created: 2026-11-22
updated: 2026-11-27
---

## Goal
Shared tooling and a written protocol that let the per-pollster tasks capture
**full toplines** reliably, whatever the publication format.

## Context
- [ADR-0007](../docs/decisions/0007-mvp-scope.md): full toplines, and the
  original report is archived.
- The formats to support come from the T-006 report: text PDF, image or scanned
  PDF, HTML, media article.
- Discovery indexes, used to *find* polls but never as the final source:
  Wikipedia "Opinion polling for ..." pages and sondajeromania.ro.

## Scope
**In:**
- **Poll inventory:** a per-pollster file listing every discovered publication
  (URL, election, how it was found, status:
  `found | archived | extracted | verified | excluded` with a reason).
  **Shared file allowed:** `docs/DATA_MODEL.md`, to add the inventory section.
- **Archiving:** `sondaje archive <url>` downloads the file to `data/raw/`
  (git-ignored), records its SHA-256, and requests a Web Archive snapshot. The
  archive URL is stored.
- **Extraction helpers:** turn text PDF tables into a draft CSV (e.g.
  pdfplumber), and HTML tables into a draft CSV. A draft is always reviewed
  before it is committed.
- **Protocol for manual entry** (images, articles): two independent
  transcription passes (e.g. two agents), compared automatically by a diff
  command. Mismatches are resolved against the original and logged.
- `docs/POLL_INGESTION.md`, a step-by-step protocol that the pollster tasks
  follow.

**Out:**
- Collecting the polls themselves (T-012 onward).

## Acceptance criteria
- [x] Each supported format is demonstrated end to end on one real report from
      an MVP pollster. The demo data may be committed if it is complete.
- [x] The double-entry diff detects a deliberately introduced mismatch (test).
- [x] The protocol states which data is never guessed and how gaps are recorded.
- [x] Ruff and pytest pass.

## Follow-ups
- **T-013 (Sociopol):** the România TV article of 2024-11-24
  (`sociopol-doc-003`) also quotes an earlier, undated Sociopol party ranking
  ("penultimul sondaj": PSD 33%, PNL 19%, AUR 18%, USR 12%, SOS 6%, UDMR 5%).
  It has no fieldwork or publication date in that article; T-013 should look
  for its own publication before deciding whether it can be recorded. The
  article's 4–8 Nov 2024 presidential poll is for an election that is not in
  the registry.
- **Share base for "expressed votes of likely voters"** (Verifield p. 5; INSCOP
  publishes the same base): recorded as `other_subset` with `notes`. If the
  analysis needs it, a new `share_base` value would be a schema change
  (owner question 1 below).
- **AGENTS.md §8 command table** (coordinator): add `archive`, `extract-pdf`,
  `render-pdf`, `extract-html`, and `double-entry-diff`, and point to
  `docs/POLL_INGESTION.md`.
- **PLAN.md** (coordinator): T-011 deliverables and the three demonstration
  polls, so that T-012…T-015 do not collect them again.
- **Optional tooling idea:** OCR for chart images (AtlasIntel, CURS slides) as
  a third, machine "pass" next to double entry; and the authenticated Save Page
  Now API (job status, guaranteed fresh captures) if anonymous captures prove
  unreliable.

## Log
- **2026-11-27 Inventory design (DATA_MODEL §6.13, schema 1.2).** Columns:
  `publication_url`, `election_id`, `title`, `published_date`,
  `fieldwork_start`, `fieldwork_end`, `found_via`, `discovery_url`, `status`,
  `exclusion_reason`, `document_id`, `poll_id`, then the §5.1 provenance block
  (it describes where the row's descriptive values come from: the index page
  while `found`, the publication once opened). Key
  (`publication_url`, `election_id`, `poll_id`): one publication can cover two
  elections, or quote two surveys for one election. `found_via` values:
  `index`, `pollster_site`, `partner_outlet`, `web_search`, `reference`,
  `other`. `exclusion_reason` values: `out_of_window`, `out_of_scope`,
  `exit_poll`, `duplicate`, `no_topline`, `unavailable`, `other`. A
  `duplicate` row may name the poll it duplicates; a media report of a used
  report is a `duplicate`. `inventory.csv` is now **required** in every
  pollster directory (R-05, error), replacing the "reserved; not validated"
  warning. §9 allowed filling §6.13 without a version bump, but R-05 and §7.5
  changed too, so the schema went to 1.2 (changelog in §9.1). The §10 worked
  example and both fixtures gained an inventory.
- **2026-11-27 New rules (next free numbers in §7.5): R-73…R-78.** R-73 E
  status ↔ link columns; R-74 E `publication_url` = the document's
  `source_url` and `election_id` = the poll's; R-75 E every poll is covered by
  an `extracted`/`verified` row (by `poll_id`, or by `document_id` +
  `election_id`, which covers the non-headline scenarios of a survey); R-76 W
  an archived document missing from the inventory; R-77 W `other` without
  notes; R-78 W fieldwork dates differ from the poll's. R-78 first compared
  `published_date` too; the Sociopol demonstration showed that a later
  publication of a poll legitimately has its own date, so it compares only
  fieldwork dates.
- **2026-11-27 Dependency: pdfplumber 0.11.11 (MIT), justified against
  ADR-0005.** ADR-0005 covers the analysis stack and names no PDF library.
  `pypdf` (already used by T-010) returns a page's text without positions;
  chart pages (the Verifield report) print values and category labels as
  separate text runs, which can only be paired by their coordinates.
  pdfplumber gives word coordinates and table detection, and renders pages to
  PNG through pypdfium2 (Apache-2.0/BSD-3), which double entry from rendered
  pages needs. It brings pdfminer.six, Pillow, and cryptography. HTML is
  parsed with the standard library (`html.parser`); no BeautifulSoup or lxml.
  No OCR: values in images go through double entry.
- **2026-11-27 Archiving.** `sondaje archive` uses anonymous Save Page Now and
  falls back to the Wayback availability API; it then downloads the snapshot
  (`id_` mode) and compares hashes. In practice Save Page Now sometimes
  returned an existing capture (2025-07-22 for `sociopol-doc-001`, 2024-11-24
  for the graphic `sociopol-doc-004`); the tool reports the snapshot date.
  Snapshot bytes were identical for the PDF and the image, and different for
  the three HTML pages (dynamic pages); for those I downloaded each snapshot
  and checked that it carries the article text used, and said so in the
  manifest notes. All sources were reachable; no paywall.
- **2026-11-27 Extraction paths.** `extract-pdf` reads `<label> <value>%` lines
  (works on the CURS Nov 2024 presentation) and pairs chart value labels with
  category labels by position (works on all six chart pages of the Verifield
  report); `extract-html` reads tables, or lists every percentage in the text
  with an entity-anchored label guess. No MVP house publishes HTML tables
  (AtlasIntel poll pages are rendered client-side and carry no data in the
  HTML; curs.ro posts carry slide images; media articles are prose).
  POLL_INGESTION §5 therefore draws the `html` / `manual_double_entry` line
  at "the tool pairs each value with its label" vs "a person must read it".
- **2026-11-27 Demonstration 1, `pdf_text`: Verifield, pres-2025-r2, 6 May 2025**
  (`verifield-pres-2025-r2-20250506`). Report PDF hosted by HotNews (Verifield
  logo on every page), embedded in the HotNews article of 2025-05-07, which
  gives `published_date`. Three bases: total sample (p. 3), expressed votes
  (p. 4), and "% voturi exprimate a celor care se duc la vot – 61.6% din
  esantion" (p. 5), recorded as `other_subset` with notes (owner question 1).
  Crosstabs by round-1 vote (pp. 6–8) are not toplines and were not recorded.
  `sponsor_type = not_disclosed`: the report names no client; HotNews states
  that candidate Nicușor Dan commissioned it (in `notes`; owner question 2).
  Margin of error 3.19 from the report; HotNews says ±3% (pollster's report
  wins, ADR-0012 rule 5). Population not stated beyond "reprezentativ pe
  variabilele socio-demografice", so `population`/`population_geo` are empty
  and `target_scope = domestic` (R-64). Labels as printed ("George-SIMION",
  "Nicușor DAN"), with cedilla letters written with comma below (ş → ș),
  following DATA_MODEL §1.7 (owner question 4). Reviewed against the rendered
  pages 2–5.
- **2026-11-27 Demonstration 2, `html`: Sociopol, pres-2025-r2, 10–12 May 2025**
  (`sociopol-pres-2025-r2-20250512`). Document: România TV article of
  2025-05-14 (`sociopol-doc-001`), which carries the values ("George Simion
  53% – Nicușor Dan 47%", plus the quote "53% la 47% în favoarea lui George
  Simion"), the fieldwork days ("în zilele de 10, 11, 12", after the round-1
  Sunday, so May 2025), n = 1,024, and the client ("comandat de România TV").
  `extract-html` produced 16 draft rows; the 2 option rows were kept and the
  14 others (turnout, earlier polls, other articles) deleted at review.
  `published_date` 2025-05-12 comes from the earlier article that first
  published the values without dates or n (`sociopol-doc-002`, inventory row
  `excluded`/`duplicate`). Two shares summing to 100, no undecided shown:
  `share_base = expressed_option`, `topline_coverage = full` (owner question
  3). "63%, inclusiv Diaspora" is the expected turnout, so `population_geo` is
  empty. Media-only: `verified = false`.
- **2026-11-27 Demonstration 3, `manual_double_entry` from an image: Sociopol,
  parl-2024-cd, 20–22 Nov 2024** (`sociopol-parl-2024-cd-20241122`). Documents:
  the broadcast graphic (`sociopol-doc-004`, the poll's document) and the
  article that embeds it (`sociopol-doc-003`: dates, n = 1,000, CATI,
  ±3.2%). **Independence:** I launched pass B as a sub-agent with only the
  inputs (graphic, article text, a brief without values) and the protocol, and
  forbade it to read pass A, ADR-0012, the T-006 report, and this task file
  (they quote this poll's values); I also removed the USR values from
  POLL_INGESTION.md while the passes ran. Pass B's final reply listed its
  values, so I did **not** do pass A myself: a second, fresh sub-agent did
  pass A under the same rules and was told not to report values. I only ran
  the diff and the review. Result: **0 mismatches** (the two `notes` cells
  differ in wording; they are not compared). Review against the graphic: all
  seven values (sum 100) and labels as printed ("SOS RO" in the logo, "ALȚII",
  the question in capitals) confirmed. The graphic's USR 13% is used; the
  article text says 15% (in the poll row's `notes`, ADR-0012 rule 1).
  `sponsor_type = not_disclosed`: the graphic says "România TV Exclusiv" and
  the article "difuzat de Romania TV"; the article's "realizat la comanda
  postului de televiziune România TV" refers to the 4–8 Nov presidential poll
  it also quotes.
- **2026-11-27 Incident.** An early PowerShell `[IO.File]` call used a
  relative path, which .NET resolved against the main worktree, and added two
  lines to `src/sondaje/validation/__init__.py` there. I reverted it at once
  with `git checkout` in the main worktree (clean since); all later file
  writes used editor tools, Python, or absolute paths.
- **2026-11-27 Demonstration 3 re-run (coordinator).** In the first run,
  both passes ran on the same model. The owner's rule is that the two
  transcription passes use different models, so the coordinator ran both
  passes again: **pass A on Claude Opus 5.5** and **pass B on Claude Sonnet
  5.5**. They ran in parallel in an isolated scratch folder outside the
  repository, with only:
  - the archived graphic (`sociopol-doc-004`) and article (`sociopol-doc-003`);
  - a copy of POLL_INGESTION.md with this poll's values removed (the §0.3
    "known case" and §11);
  - DATA_MODEL.md and the entity, pollster and entity-map registries.

  Neither pass could open the repository, the web, or the other pass.
  `double-entry-diff` found **1 mismatch**: pass A wrote `question_wording` in
  capitals, as the graphic prints it, and pass B in sentence case. Resolved
  against the graphic for pass A (§0.1, §8: verbatim). The re-diff found
  **0 mismatches**. Pass A also matches the committed rows of
  `sociopol-parl-2024-cd-20241122` exactly (0 mismatches), so the data is
  unchanged.

## Outcome
**Delivered**
- **Poll inventory** (DATA_MODEL §6.13, schema 1.2): column table, status and
  exclusion-reason tables, header line (§6.14), R-05 update, rules R-73…R-78
  in `src/sondaje/validation/rules_inventory.py`, the worked example (§10) and
  the fixtures extended, tests for every new rule.
- **`sondaje archive`** (`src/sondaje/ingest/archive.py`): download or
  `--file`, SHA-256, format detection, Save Page Now with lookup fallback,
  `--archive-url` for checked snapshots, snapshot byte check, manifest
  append/update, inventory `found` → `archived`. Writes nothing when no
  snapshot exists. Tests mock the network.
- **Extraction helpers**: `sondaje extract-pdf` (lines, chart pairing,
  tables), `sondaje render-pdf`, `sondaje extract-html` (tables, text, page
  metadata), writing drafts under `build/drafts/` with registry-based
  `entity_id`/`option_type` guesses (`src/sondaje/ingest/drafts.py`,
  `extract_pdf.py`, `extract_html.py`).
- **`sondaje double-entry-diff`** (`src/sondaje/ingest/double_entry.py`):
  reports missing/extra polls, bases, and options and every differing cell;
  exit 1 on any mismatch. `tests/test_double_entry.py` includes the deliberate
  mismatch test.
- **`docs/POLL_INGESTION.md`**: the step-by-step protocol (discovery,
  inventory, archive, extraction or double entry, review, recording,
  validation), with "data that is never guessed" (§0.1), "how gaps are
  recorded" (§0.2), and the ADR-0012 rules (§0.3, §0.4).
- `data/README.md` points to the inventory and the protocol.

**Demonstration polls committed** (T-012…T-015 must not collect them again;
they should list them in their Outcome):

| Pollster | poll_id | Format → method | Source |
|---|---|---|---|
| Verifield | `verifield-pres-2025-r2-20250506` | `pdf_text` → `pdf_text` | https://hotnews.ro/wp-content/uploads/2025/05/Raport-ND13-6-Mai-Val-1.pdf |
| Sociopol | `sociopol-pres-2025-r2-20250512` | `html` → `html` | https://www.romaniatv.net/exclusiv-mirel-palada-director-sociopol-cursa-dintre-nicusor-dan-si-george-simion-e-din-ce-in-ce-mai-stransa_8926885.html |
| Sociopol | `sociopol-parl-2024-cd-20241122` | `image` → `manual_double_entry` | https://www.romaniatv.net/wp-content/uploads/2024/11/sondaj-3.jpg (metadata: https://www.romaniatv.net/sondaj-sociopol-pe-cine-prefera-romanii-la-alegerile-parlamentare-psd-conduce-detasat_8633323.html) |

`data/polls/verifield/` and `data/polls/sociopol/` now exist with all four
files; their inventories list only the publications used by these three
polls, so T-013 and T-015 continue them.

**Key commits:** `412a0ab` inventory schema and rules · `2c80836` archive ·
`bcff885` extraction helpers · `d4ad09e` double-entry diff · `d87d46a`
Verifield demo · `28e7c19` Sociopol html demo · `8789e62` protocol and
double-entry demo.

**Checks (2026-11-27):** `uv run pytest` 352 passed; `uv run ruff check .` and
`uv run ruff format --check .` clean; `uv run sondaje validate` 0 errors
(88 R-33 warnings, entity colours, pre-existing); also with `--against main`.

**Known limitations**
- `extract-pdf` chart mode handles column and horizontal bar charts with one
  value label per bar; stacked or grouped bars and legends need double entry.
  Values inside images are not read (no OCR).
- `extract-html` text mode guesses labels only for registry names next to the
  value; prose drafts need a careful review, or double entry.
- Save Page Now (anonymous) may return an existing capture or fail under rate
  limits; the tool reports both honestly, and HTML snapshot checks need a
  human look.

**Open questions for the owner**
1. Verifield's third base ("expressed votes of those who will vote", 61.6% of
   the sample) is `other_subset` with notes. Keep that, or add a
   `share_base` value for it (INSCOP publishes the same base)?
2. When the pollster's report names no client but the media say a candidate
   commissioned the poll (Verifield, 6 May 2025), the poll is
   `not_disclosed` with the media statement in `notes` (strict reading of
   §6.11: columns describe the source used). Is that the intended reading for
   M-5.1d, given that the affiliation registry already records the relation?
3. Two published shares that sum to 100 with no undecided shown (Sociopol
   round 2): `expressed_option` with `topline_coverage = full`. OK?
4. Labels are verbatim except that cedilla letters are written with a comma
   below (ş → ș), per DATA_MODEL §1.7. OK?
