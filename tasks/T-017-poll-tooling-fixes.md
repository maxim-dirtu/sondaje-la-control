---
id: T-017
title: Poll tooling fixes (archive, extract, double-entry-diff)
status: in-progress
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
- [ ] Each item above is fixed with a test, or declined with a reason in the
      Log.
- [ ] Tests never touch the network.
- [ ] `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`
      and `uv run sondaje validate` pass.

## Follow-ups

## Log

## Outcome
