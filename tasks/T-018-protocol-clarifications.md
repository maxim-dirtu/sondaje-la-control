---
id: T-018
title: Protocol and data-model clarifications from the first collection round
status: in-progress
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
- [ ] Each convention is written in POLL_INGESTION.md, or in DATA_MODEL.md
      where it concerns a column.
- [ ] Every existing row that contradicts a convention is fixed, and each fix
      is logged.
- [ ] `uv run sondaje validate --against main`, pytest and ruff pass.

## Follow-ups

## Log

## Outcome
