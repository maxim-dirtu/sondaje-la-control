# ADR-0007: MVP scope: 3 elections, 2–4 pollsters, full toplines

- **Status:** Accepted
- **Date:** 2026-11-22
- **Related:** T-006, T-010, T-011; supersedes the initial 5-election backlog
  (the bootstrap commit "T-000: bootstrap plan, methodology spec, ADRs and task
  backlog", restructured before any work started)

## Context
The initial plan covered 5 elections and every pollster. That is too much
collection work before we can see whether the pipeline, the metrics, and the
visuals are useful. Collecting data by hand is the main cost. In particular,
polls are often published only partially (top parties only), in PDFs, images,
or media articles.

## Decision
- **Elections (MVP):** Parliamentary 2024 (Chamber of Deputies,
  `parl-2024-cd`), Presidential 2025 round 1 (`pres-2025-r1`), and round 2
  (`pres-2025-r2`).
- **Pollsters (MVP):** 2–4 houses, chosen for popularity and transparency
  through a documented scorecard (T-006) and approved by the owner.
- **Full toplines:** every option that a poll publishes is captured (all
  parties/candidates, "other", undecided, non-response), not just the leading
  parties. The original report is archived, with a hash and a Web Archive link,
  so that crosstabs can be extracted later.
- **Scale** (more elections, more pollsters, automated discovery) is deferred to
  Phase 6. That phase is designed after the MVP is complete.

## Consequences
- The data work splits **per pollster** (each house publishes in its own format)
  rather than per election.
- **Limited statistical power:** each house has at most 3 (house, election)
  pairs. MVP outputs are descriptive and demonstrate the method. Significance
  results must be presented as preliminary.
- With only 2–4 houses, the "market" reference used in M-2.5 and M-3.1 is
  thin. See I-013 for a mitigation.
- EP 2024, Presidential 2024 R1, and 2014–2020 move to the backfill (T-061).

## Alternatives considered
- All pollsters, few elections: too much collection work across many formats.
- One pollster only: no market comparison, so house effects can't be computed.
