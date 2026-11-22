---
id: T-011
title: Poll ingestion toolkit
status: todo
phase: 1
depends_on: [T-001, T-002, T-006]
owner: null
branch: null
methodology: [M-1.1, M-5.3]
created: 2026-11-22
updated: 2026-11-22
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
- [ ] Each supported format is demonstrated end to end on one real report from
      an MVP pollster. The demo data may be committed if it is complete.
- [ ] The double-entry diff detects a deliberately introduced mismatch (test).
- [ ] The protocol states which data is never guessed and how gaps are recorded.
- [ ] Ruff and pytest pass.

## Follow-ups

## Log

## Outcome
