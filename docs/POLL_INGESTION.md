# Poll ingestion protocol

**Owner:** T-011 · **Last updated:** 2026-11-27 · **Applies to:** the pollster data
tasks (T-012 AtlasIntel, T-013 Sociopol, T-014 CURS, T-015 Verifield, and later
ones).

This is the step-by-step procedure for turning a pollster's publications into
rows of `data/polls/<pollster_id>/`. Follow the steps in order for every
publication. The contract for the files is [DATA_MODEL.md](DATA_MODEL.md) (§5
provenance, §6.10–§6.13 poll files, §7 rules); the rules for the MVP houses are
in [ADR-0012](decisions/0012-mvp-pollsters.md), and the formats each house
publishes in are in [pollster-selection.md §5](reports/pollster-selection.md).

Contents:
0. [Ground rules](#0-ground-rules)
1. [Set up the pollster directory](#1-set-up-the-pollster-directory)
2. [Discover publications](#2-discover-publications)
3. [List them in the inventory](#3-list-them-in-the-inventory)
4. [Archive each publication](#4-archive-each-publication)
5. [Choose the extraction path](#5-choose-the-extraction-path)
6. [Extract (text PDF, HTML)](#6-extract-text-pdf-html)
7. [Double entry (images, rendered pages, prose)](#7-double-entry-images-rendered-pages-prose)
8. [Review against the original](#8-review-against-the-original)
9. [Record the data](#9-record-the-data)
10. [Validate and report](#10-validate-and-report)
11. [Worked examples (T-011 demonstrations)](#11-worked-examples-t-011-demonstrations)

---

## 0. Ground rules

### 0.1 Data that is never guessed

A value is recorded only if the publication states it. **Never** fill in,
estimate, infer, compute, or "fix" any of the following:

- **Shares** (`share_raw`): no rounding, re-basing, normalizing, or completing
  a topline so that it sums to 100; no reading a value off a bar's length when
  no number is printed; no value for an option the source does not show.
- **Options**: no option that the source does not list (e.g. an "undecided"
  share that is only implied by 100 minus the rest).
- **Dates**: `fieldwork_start`, `fieldwork_end`, `published_date`. Do not
  derive the fieldwork from the publication date, or the reverse. A date given
  without a year ("10, 11, 12") may be completed only when the publication
  itself fixes the year and month (e.g. "after Sunday's round 1"); say so in
  `notes`.
- **Sample**: `sample_size`, `sample_size_expressed`, `population`,
  `population_geo` (a poll covers the diaspora only when the publication says
  so for the sample, not for turnout).
- **Method**: `mode` (follow the conventions of DATA_MODEL §6.11; a pollster's
  usual mode is not enough), `question_type`, `question_wording` (verbatim or
  empty), `weighting_published`, `margin_of_error`.
- **Sponsor**: `sponsor` and `sponsor_type` describe the client as stated by
  the pollster's publication or, when it names none, by a media outlet
  (owner decision, 2026-11-27). A client stated only by the media is recorded
  only when the outlet states it explicitly (e.g. "realizat la comanda ...")
  or the client presents the poll itself. Archive that publication too, cite
  it in `notes` with its `document_id`, and give its inventory row the poll's
  `poll_id`. If the pollster's publication names a different client, the
  pollster wins (§0.3) and the media claim goes in `notes`. A client that is
  only rumoured or inferred (e.g. from the pollster's usual clients) is never
  recorded.
- **Entities**: an `entity_id` is set only when the label clearly names that
  registry entity; a person or party missing from the registry is added
  (append-only, with its own source), never mapped to a "close" entity.
- **Archive URLs**: an `archive_url` is a snapshot you (or `sondaje archive`)
  obtained and checked; never a URL built by hand.

### 0.2 How gaps are recorded

- **An unknown value is an empty cell.** Never write `NA`, `-`, `?`, `0`, or a
  placeholder (DATA_MODEL §1.3).
- **Say why in `notes`** when the gap matters for a reader, e.g.
  "Mode, question wording, margin of error and weighting were not stated."
- **Publication-level gaps go in the inventory.** A publication that cannot be
  used is `excluded` with an `exclusion_reason` and a sentence in `notes`
  (e.g. `unavailable`: "404 on 2026-11-27; no Web Archive snapshot"). A
  publication that cannot be archived yet stays `found` with the reason in
  `notes`.
- **Partial toplines** are recorded as published with
  `topline_coverage = partial`; they are not excluded and not completed.
- **The task Log** lists every gap found, with the date and what was tried
  (AGENTS.md §6), and the task Outcome sums them up (§10).

### 0.3 Which source wins

1. **The pollster's own report** wins over any media report of it (ADR-0012
   rule 5; DATA_MODEL §6.11). The media value goes in `notes`.
2. **Media-only polls** (e.g. Sociopol) are recorded with `verified = false`
   (ADR-0012 Q-B). Archive the article **and** every broadcast graphic.
3. **A broadcast graphic wins over the article text** when they disagree; the
   text value goes in `notes` (ADR-0012 rule 1; known case: Sociopol
   20–22 Nov 2024, USR 13% on the graphic, 15% in the text).
4. **Wikipedia and aggregators** (sondajeromania.ro) are indexes: use them to
   find publications, never as the source of a value (`verified` can never be
   `true` for them, R-14).

### 0.4 Other rules

- **Publication timing** (ADR-0012 rule 2, M-1.7): record every poll, including
  one first published on or after election day, with its true
  `published_date`. Do not drop it; the pipeline excludes it from metrics
  (validation warns with R-83, which is expected).
- **Diaspora** (ADR-0012 rule 3, M-1.4): set `population_geo` from the report
  (or its partner, when the report is silent) and `target_scope` to match:
  `residents_and_diaspora` → `total`; `residents` or empty → `domestic`.
- **Round 2** (`pres-2025-r2`): only polls with fieldwork after round 1
  (R-84). A head-to-head asked before 2025-05-04 is not a round-2 poll.
- **Labels** are copied verbatim, but Romanian letters with a cedilla are
  written with a comma below (ş → ș, ţ → ț; DATA_MODEL §1.7), in every pass.
- **Neutral wording** in every `notes` cell
  ([ADR-0003](decisions/0003-neutral-language.md)).
- **Encoding**: on Windows, PowerShell 5 corrupts UTF-8. Edit CSV files with
  an editor tool, or write them from Python (`sondaje.ingest.csvio`), never
  with `Set-Content` or `Out-File`.
- **Drafts and passes are not data.** They live under `build/` (git-ignored).
  Raw downloads live under `data/raw/` (git-ignored). Only reviewed rows are
  committed.

## 1. Set up the pollster directory

Every `data/polls/<pollster_id>/` has four files (R-05): `polls.csv`,
`poll_results.csv`, `archive_manifest.csv`, and `inventory.csv`. Create them
with their header lines (DATA_MODEL §6.14):

```powershell
uv run python -c "from pathlib import Path; from sondaje.schema import ARCHIVE_MANIFEST, INVENTORY, POLLS, POLL_RESULTS; from sondaje.ingest.csvio import write_rows; [write_rows(Path('data/polls/<pollster_id>') / t.filename, t, []) for t in (POLLS, POLL_RESULTS, ARCHIVE_MANIFEST, INVENTORY)]"
```

The pollster must already be in `data/registry/pollsters.csv` (T-005).

## 2. Discover publications

Goal: every publication of the pollster's voting-intention polls for the
task's elections inside the collection windows (the task file gives them:
120 days before election day for `parl-2024-cd` and `pres-2025-r1`; fieldwork
after round 1 for `pres-2025-r2`).

1. **Indexes, for finding only**: the EN and RO Wikipedia "Opinion polling
   for ..." pages of each election and sondajeromania.ro
   (`/institute/<slug>` and `/sondaje/<year>`). Note every poll they list.
2. **The pollster's own site**: poll pages, reports, press releases (e.g.
   `atlasintel.org/poll/...`, `curs.ro` posts and `wp-content/uploads` PDFs).
3. **Partner outlets** (ADR-0012 rule 4): the clients and media partners of
   the house (e.g. HotNews for AtlasIntel; România TV for Sociopol; TVR Info
   and ProTV for CURS; HotNews, Digi24, Libertatea, G4Media, B1TV and the
   clients' Facebook posts for Verifield). Search their poll tags and the
   pollster's name.
4. **Web searches** for each month of the window ("sondaj <pollster> <month>
   <year>"), to catch polls missing from every index (in the MVP: Sociopol
   20–22 Nov 2024, BCS 26–29 Sep and 7–10 Nov 2024).
5. **Follow the chain to the original**: from an index entry to the article,
   and from the article to the pollster's report, image, or video it quotes.

Record what you searched, and when, in the task Log; the Outcome reports the
polls found outside the indexes.

## 3. List them in the inventory

Add one row per publication to `inventory.csv` (DATA_MODEL §6.13) with
`status = found`, before downloading anything:

- `publication_url`: the publication itself (the report PDF, the poll page,
  the article, the graphic image), never the index page.
- `election_id`; `title`, `published_date`, and fieldwork dates as far as
  known (they decide the window).
- `found_via` and `discovery_url`: how and where it was found (`index`,
  `pollster_site`, `partner_outlet`, `web_search`, `reference`, `other`).
- The provenance block describes where the row's values come from (the index
  page while the row is `found`; the publication once you have opened it).

List **every** publication you looked at, also the ones you will not use:
a media report of a poll whose own report you use is `excluded` /
`duplicate` (with `poll_id` once the poll exists); an exit poll is
`exit_poll`; a poll outside the window is `out_of_window`; an attitudes
survey or a pre-round-1 head-to-head is `out_of_scope`. The status column
rules are R-73 (validation enforces them).

## 4. Archive each publication

Every publication that a poll's values or metadata come from is archived
(ADR-0007; DATA_MODEL §5.2). For media-only polls, archive the article **and**
each broadcast graphic (two rows in the inventory, two documents).

```powershell
uv run sondaje archive <publication_url> --pollster <pollster_id> --source-type pollster --title "<title as published>" --published-date YYYY-MM-DD
```

The command:
1. refuses URLs that are not in the inventory (step 3 first);
2. downloads the file and computes its SHA-256. A Google Drive `view` link
   (`drive.google.com/file/d/<id>/view`) is resolved to its direct download
   (`drive.google.com/uc?export=download&id=<id>`), which is also what gets
   snapshotted; the manifest `source_url` stays the link as listed. A request
   that fails with HTTP 429, a server error, a refused connection, or a
   timeout is retried (`--retries`, default 2, waits of 10 s and 20 s);
3. detects the `format` (`pdf_text` when the PDF has a text layer, `pdf_image`
   otherwise, `html`, `image`, ...; override with `--format`);
4. requests a Web Archive snapshot (Save Page Now); if that fails, looks up
   the closest existing snapshot;
5. saves the file to `data/raw/polls/<pollster_id>/<document_id>.<ext>`. This
   happens only once a snapshot is secured, so a failed run leaves no raw file;
6. downloads the snapshot and compares its bytes with the download (a
   gzip-encoded capture is decompressed first);
7. appends (or updates) the `archive_manifest.csv` row and sets the
   inventory rows of the URL to `archived` with the new `document_id`.

Read its report:
- **`snapshot check: identical`**: done.
- **`snapshot check: DIFFERENT`**: normal for HTML pages (ads, scripts). Open
  the snapshot and check that it shows the same values and metadata; write
  what you checked in the manifest `notes` (e.g. "Snapshot HTML differs in
  bytes (dynamic page); article text checked 2026-11-27"). For a PDF or an
  image, a difference means the file changed: find out why before using it.
- **`snapshot check: NOT CHECKED`**: the snapshot could not be downloaded
  (connection refused, HTTP 429), even after the retries. The snapshot URL is
  recorded but unverified (typical after a fallback to an existing capture).
  Run the same command again later: on unchanged bytes it repeats the check
  and keeps the manifest row. Or open the snapshot and compare by hand, and
  say so in `notes`. For a manual comparison with `curl`, use `--compressed`
  (the Web Archive may serve gzip bytes).
- **A snapshot date long before today** means Save Page Now returned an
  existing capture. Keep it if the check passes; say so in `notes`.
- **Error "no Web Archive snapshot could be created or found"**: nothing was
  written, not even the raw file. Retry later. If it keeps failing, make a
  snapshot by other means (e.g. archive.today), open it, check it, and pass it
  with `--archive-url <url>`. Until then the inventory row stays `found`, with
  the reason in `notes`. Never invent an archive URL.
- **Download refused** (some sites block scripts), or **"Google Drive returned
  a web page, not the file"** (a private file, a quota limit, or a file too
  large for Drive's virus-scan check): save the file with a browser and pass
  it with `--file <path>`; say so in the manifest `notes`.

Re-running `archive` on the same URL updates the same `document_id`: same
bytes keep the old `retrieved_at` and snapshot (and the snapshot check is
repeated); new bytes get today's date and a new snapshot (and you must
re-check the values extracted from it).

## 5. Choose the extraction path

`polls.extraction_method` says how the values were read; R-67 checks it
against the document `format`.

| Where the values are | Path | `extraction_method` |
|---|---|---|
| Text layer of a PDF, as text (tables, label + value lines, chart value labels): CURS presentations, the Verifield report | `sondaje extract-pdf` (§6) | `pdf_text` |
| An HTML table, or HTML text where each value sits next to its label ("George Simion 53% – Nicușor Dan 47%") | `sondaje extract-html` (§6) | `html` |
| Inside images: chart images in a PDF (AtlasIntel), broadcast graphics (Sociopol), slide PNGs (CURS), scanned PDFs | `sondaje render-pdf` for PDF pages, then double entry (§7) | `manual_double_entry` |
| Prose where the tool cannot pair labels and values ("53% la 47% în favoarea lui ...") | double entry (§7) | `manual_double_entry` |

If `extract-pdf` finds no values on a page of a `pdf_text` document, the
values are in images, or the text layer is unreadable (e.g. letters printed as
separate text runs, as in the Sociopol PDFs): render the page and use double
entry. `extract-pdf` says which case it found and points to `render-pdf`.
When in doubt, use double entry; it fits every format.

## 6. Extract (text PDF, HTML)

Extraction writes a **draft** `poll_results.csv` under `build/drafts/`. The
draft has the label and value of each option exactly as printed (the only
change is the decimal comma → point), and **guesses** for `option_type` and
`entity_id`. Run it once per share base (the option order restarts at 1):

```powershell
uv run sondaje extract-pdf --pollster verifield --document verifield-doc-001 --election pres-2025-r2 --poll-id verifield-pres-2025-r2-20250506 --pages 3 --share-base all_respondents --out build\drafts\verifield-doc-001.csv
uv run sondaje extract-pdf --pollster verifield --document verifield-doc-001 --election pres-2025-r2 --poll-id verifield-pres-2025-r2-20250506 --pages 4 --share-base expressed_option --out build\drafts\verifield-doc-001.csv --append
```

- `extract-pdf --mode`: `auto` (default) reads `<label> <value>%` lines and
  falls back to `chart` (value labels paired with category labels by
  position); `tables` reads ruled tables. Each draft row's `notes` say where
  it was found (page, line, or chart; `CHECK` when the counts of values and
  labels differ). When it finds no rows, or its text layer looks unreadable
  (most words single characters, or no text at all), it prints why and points
  to `render-pdf` and double entry (§7); do not trust rows from such a page.
- `extract-html` prints the page title, the declared publication time (use it
  for `published_date`), and the images on the page (find broadcast graphics
  here). In `text` mode every percentage on the page becomes a draft row with
  its sentence: delete the rows that are not options of this poll, and check
  that no option is missing. A `Name - 50%` line (a dash directly before the
  value, a short label before it) takes the text before the dash as its
  label.
- `--election` limits the entity guesses to contestants of that election
  (candidates for a presidential round).
- `render-pdf` writes PNG images of PDF pages (for the review in §8 and for
  double entry).

Then complete the draft: keep only the options of this poll and base, fix the
labels (comma-below diacritics), confirm every `option_type` and `entity_id`,
fill `verified` and `notes`, and write the `polls.csv` row (§9). Move on to the
review (§8).

## 7. Double entry (images, rendered pages, prose)

Two **independent** transcriptions of the same archived publication, compared
by a tool.

1. **Prepare** `build/double-entry/<poll_id>/` with the inputs: the archived
   files (the image, the rendered pages, the saved HTML) and a short brief
   (the poll's election, the publication URLs and their `document_id`s, the
   inventory notes). Give both passes the same inputs.
2. **Pass A and pass B** each write, into their own directory
   (`pass-a/`, `pass-b/`), a `polls.csv` and a `poll_results.csv` in the final
   format (DATA_MODEL §6.11, §6.12; header lines in §6.14), following this
   protocol and the ground rules (§0). Each pass decides every cell on its own:
   the values, the labels, the option order, the bases, `option_type`,
   `entity_id`, the dates, `sample_size`, `mode`, `population_geo`,
   `target_scope`, the sponsor, and the provenance.
3. **Independence**: the two passes are done by different people or agents
   (e.g. a sub-agent started with only the inputs and this protocol). Neither
   sees the other's files or notes before the comparison. Do not copy one pass
   into the other to "save time". If only one person is available, do the
   second pass on another day without looking at the first, and say so in the
   Log.
4. **Compare**:
   ```powershell
   uv run sondaje double-entry-diff build\double-entry\<poll_id>\pass-a build\double-entry\<poll_id>\pass-b
   ```
   It lists every missing or extra poll, base, or option (options are matched
   by their exact label; when a label repeats in a base, such as two "Altul"
   rows, the repeats are matched by `option_order`, then by position), and
   every differing cell (`retrieved_at` and
   `notes` are ignored). Exit code 0 = the passes agree, 1 = mismatches.
5. **Resolve every mismatch against the archived original**, never by
   choosing a pass or splitting the difference. Correct the pass that is
   wrong (or both), re-run the diff until it reports 0 mismatches, and log
   each mismatch and its resolution in the task Log (what each pass had, what
   the original shows).
6. The agreed rows are the data: copy pass A's rows into the pollster's files
   (§9). The inventory row of the document moves to `extracted`, and to
   `verified` after the review (§8).

## 8. Review against the original

Before any row is committed, check it against the archived original (the
raw file or the snapshot), value by value:

- [ ] every option the publication shows is a row, in the published order;
      nothing is added (no implied "undecided", no computed "others");
- [ ] every `share_raw` is exactly as printed (decimals kept: `30.0` stays
      `30.0`); `<1%` is `share_raw = 1`, `share_qualifier = lt`;
- [ ] each base the publication shows has its own rows and the right
      `share_base` (`all_respondents`, `expressed_option`, `likely_voters`, or
      `other_subset` with `notes` quoting the base description);
- [ ] labels are verbatim (comma-below diacritics); `entity_id` and
      `option_type` are right, and the same label maps to the same entity in
      every poll of this pollster and election (R-62);
- [ ] the dates, `sample_size`, `mode`, population, question, sponsor, MoE,
      and weighting are as stated, and empty where not stated (§0.1);
- [ ] crosstabs (subgroups) and hypothetical scenarios are not mixed into the
      topline (a second scenario of the same survey is a separate poll with
      `headline = false`, DATA_MODEL §6.11);
- [ ] source disagreements are resolved by §0.3 and the other value is in
      `notes`.

Then set the inventory row of each document that fed the poll to `verified`
(with the `poll_id`).

## 9. Record the data

- **`polls.csv`**: one row per poll (DATA_MODEL §6.11). `poll_id` is
  `<pollster_id>-<election_id>-<fieldwork_end as YYYYMMDD>` (R-70).
  `published_date` is the **first** publication of the results (an earlier
  article may be the first; record it in the inventory too). `document_id`,
  `source_url` (= the document's, R-68), and `extraction_method` name the
  document the values came from; metadata taken from another archived
  document is explained in `notes`. Fill the M-5.3 transparency columns from
  what was published (§0.1).
- **`poll_results.csv`**: the reviewed rows (DATA_MODEL §6.12), provenance
  equal to the poll's.
- **`verified`**: `true` only when every value was checked against the
  pollster's own publication; `false` for media-only polls (§0.3).
- **Registries**: a party or candidate that is polled but not registered is
  appended to `data/registry/entities.csv` (with its own source), and, if it
  is not on the ballot, to the election's `entity_map.csv` (DATA_MODEL §6.6).
  Both are append-only (§2.2).
- **Inventory**: every row ends as `verified` (or `extracted` if the review is
  pending) with its `document_id` and `poll_id`, or `excluded` with a reason.

## 10. Validate and report

```powershell
uv run sondaje validate
uv sync; uv run pytest; uv run ruff check .; uv run ruff format --check .
```

`validate` must report 0 errors. Warnings to expect: R-33 (entity colours),
R-83 for polls published after election day (M-1.7). The inventory rules are
R-73 (status ↔ links), R-74 (links agree), R-75 (every poll is covered by an
`extracted`/`verified` row), R-76 (every archived document is in the
inventory), R-77 and R-78 (notes, fieldwork dates).

The task Outcome reports, per election: the number of polls, the share taken
from the pollster's own publications (vs media), the polls found outside the
indexes, the polls excluded and why, and the gaps (§0.2).

## 11. Worked examples (T-011 demonstrations)

T-011 ran this protocol on three real MVP publications. The data is committed;
the pollster tasks do not need to collect these polls again (but they list
them in their Outcome).

| Format | Poll | Documents | Path |
|---|---|---|---|
| Text PDF | `verifield-pres-2025-r2-20250506` (Verifield, fieldwork 6 May 2025, n = 944) | `verifield-doc-001`: the Verifield report hosted by HotNews | `extract-pdf --mode auto` (chart pairing) on pages 3–5 → three bases; reviewed against the rendered pages. The HotNews article (`verifield-doc-002`) is archived as the source of the client, which the report does not name (`sponsor_type = candidate`, §0.1); its ±3% margin of error lost to the report's ±3.19% (§0.3). |
| HTML | `sociopol-pres-2025-r2-20250512` (Sociopol, 10–12 May 2025, n = 1,024) | `sociopol-doc-001`: România TV article of 14 May 2025; `sociopol-doc-002`: the article of 12 May 2025 that first published the values | `extract-html` text mode; 2 of 16 draft rows kept ("George Simion 53% – Nicușor Dan 47%"). Media-only, `verified = false`. The 12 May article gives `published_date` and is a `duplicate` row. |
| Image (double entry) | `sociopol-parl-2024-cd-20241122` (Sociopol, 20–22 Nov 2024, n = 1,000) | `sociopol-doc-004`: the România TV broadcast graphic; `sociopol-doc-003`: the article that embeds it (dates, n, mode, margin of error) | Two independent passes (two sub-agents on different models, given only the inputs and this protocol) over the graphic and the article, compared with `double-entry-diff`. It found 1 mismatch: the question wording was in capitals as printed in one pass and in sentence case in the other. It was resolved against the graphic (verbatim, §0.1), and the re-diff found 0 mismatches. The rows were then reviewed against the graphic. The graphic's USR 13% is used; the article text's 15% is in `notes`. |
