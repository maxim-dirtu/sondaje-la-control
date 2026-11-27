---
id: T-017
title: Poll tooling fixes (archive, extract, double-entry-diff)
status: review
phase: 1
depends_on: [T-011]
owner: Copilot agent (contributor)
branch: task/T-017-poll-tooling-fixes
methodology: []
created: 2026-11-27
updated: 2026-11-28
---

## Goal
The T-011 tools handle the cases the pollster tasks hit by hand, so the next
collection round (T-061, T-064) needs fewer manual steps.

## Context
Collected from the *Follow-ups* of T-012…T-015. Each item names the task that
found it.

## Scope
**In:** `src/sondaje/ingest/` and its tests; the tool sections of
`docs/POLL_INGESTION.md` (§4, §6, §7) where the behaviour changes.

1. `sondaje archive`:
   - Compare gzip-encoded snapshots after decompressing them; today they are
     reported `DIFFERENT` although identical (T-012).
   - Clearer handling of Save Page Now HTTP 429 and refused connections: a
     retry, or an explicit "fallback snapshot, not checked" message (T-012).
   - Accept Google Drive `view` URLs by resolving them to the direct download
     (T-012).
   - Do not leave an orphan raw file when the snapshot step fails (T-015).
   - Repeat the snapshot check when the command is run again on the same
     bytes after a failed snapshot download (T-014).
2. `sondaje extract-html`: read "Name - N%" lines (T-013).
3. `sondaje extract-pdf`: report clearly when a PDF's text layer is
   unreadable (Sociopol PDFs), and point to `render-pdf` and double entry
   (T-013).
4. `sondaje double-entry-diff`: tests for duplicate option labels (e.g. two
   "Altul" rows, Verifield Oct 2024); match by position when labels repeat
   (T-015).

**Out:** data changes; OCR (a separate idea).

## Acceptance criteria
- [x] Each item above is fixed with a test, or declined with a reason in the
      Log.
- [x] Tests never touch the network.
- [x] `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`
      and `uv run sondaje validate` pass.

## Follow-ups
- `archive`: Drive files too large for the virus-scan confirmation page are
  detected (HTML instead of the file) and refused with a `--file` hint, but
  the confirmation-token download is not automated.
- `archive`: the snapshot check outcome is not stored in the manifest, so a
  re-run repeats the check (one extra download) instead of skipping it; a
  `--check-only` flag was not added (the re-run does the job).
- `extract-html`: a dash after a long sentence ("...PSD a obținut - 30%") is
  not taken as a label (more than 8 words); the row keeps an empty label for
  the reviewer.
- POLL_INGESTION §5 got a one-sentence note on unreadable text layers (outside
  the §4/§6/§7 scope named in the task, directly tied to item 3); drop or
  keep it at review.

## Log
- 2026-11-28 Locked: branch `task/T-017-poll-tooling-fixes` from `main`
  (26baf3a), worktree `..\sondaje-wt\T-017`.
- 2026-11-28 **1a gzip.** `check_snapshot` compares the SHA-256 of the raw bytes
  and, if they are gzip data (magic `1f 8b`), of the decompressed bytes; a
  gzip-decoded match is reported as `identical` with a note. Decompression
  errors fall back to `DIFFERENT`. Chose the magic bytes over the
  `Content-Encoding` header because the fetcher returns raw bytes and the
  header may be missing.
- 2026-11-28 **1b retries / explicit message.** `retrying()` wraps the fetcher
  (download, Save Page Now, lookup, snapshot download): up to `--retries`
  (default 2) retries with waits of 10 s, 20 s. Retriable: HTTP 429 and 5xx,
  refused connections, timeouts, dropped connections; not retriable: other
  4xx and bad URLs. A failed snapshot download now reads `NOT CHECKED: ...
  unverified ... run the same command again`. Tests inject `sleep`, so they
  never wait; the test request helper defaults to `retries=0`.
- 2026-11-28 **1c Drive.** `direct_download_url` maps `/file/d/<id>/view` (and
  `/file/d/<id>`, `/open?id=<id>`) to `uc?export=download&id=<id>`. Download,
  Save Page Now and lookup use the direct URL; the manifest `source_url`
  and the inventory keep the listed link. If the response is an HTML page
  (quota, private, too large) and no `--file`/`--format` was given, the run
  fails with a `--file` hint instead of archiving the viewer page.
- 2026-11-28 **1d orphan raw file.** The raw file is written after the snapshot
  is secured (and before the manifest). A failed run writes nothing under
  `data/raw/`, and no longer overwrites the raw file of a document that was
  archived earlier. The error message no longer says the download is kept.
  Declined: naming raw files after the document only after the row is
  written (T-015's other option); deferring the write covers it.
- 2026-11-28 **1e re-run check.** The snapshot check now also runs when the
  bytes are unchanged and the snapshot is kept from the manifest, unless
  `--no-check` or `--archive-url` is given. Chose this over `--check-only`
  (T-014's alternative): one extra download per re-run, no new flag.
- 2026-11-28 **2 extract-html.** In `text` mode, a dash (`-`, en or em dash)
  directly before a value makes the text before it (back to the previous value
  or comma/semicolon/colon/bracket, at most 8 words) the label; the entity is
  found inside the label (else `guess_type`). The sentence splitter no longer
  splits a decimal point between digits (`3.5%`).
- 2026-11-28 **3 extract-pdf.** `text_layer_problem()` reports a page range with
  fewer than 50 letters ("no text layer") or where at least 40% of the words
  are single characters ("unreadable"). `extract-pdf` prints it to stderr
  after every run: "no rows found: ..." or "the rows above are probably
  wrong: ...", with the `render-pdf` / double-entry advice. Spaced letters can
  still produce a bogus `lines` row, hence the warning also when rows exist.
  The Sociopol PDFs themselves are not in the repository, so the test PDF
  imitates their text layer (every character a separate text run).
- 2026-11-28 **4 double-entry-diff.** Duplicate labels were already matched by
  occurrence (`Altul`, `Altul (#2)`) but untested. Repeats of a label in a base
  are now paired by equal `option_order` first, then by file position; extra
  repeats are reported once (`Altul (#3)`). Tests cover agreement, a value
  mismatch, reordered rows, one missing, one extra, and a differing order.
- 2026-11-28 Docs: POLL_INGESTION §4, §6, §7 updated (plus the sentence in §5).

## Outcome
All four items are done, with tests; nothing was declined. `uv run pytest`
(381 passed), `uv run ruff check .`, `uv run ruff format --check .` and
`uv run sondaje validate` (0 errors, 91 warnings, all pre-existing) pass.
No data under `data/` and no dependency changed (`uv.lock` untouched).

Commits (all `T-017: ...`): gzip, retries, Drive, orphan raw file, re-run
check, extract-html dash lines, extract-pdf text layer, double-entry
duplicates, docs. Known limitations: see Follow-ups.
