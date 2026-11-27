# Project Plan

**Last updated:** 2026-11-27 · **Current phase:** 2 (Core metrics). Phases 0 and 1 (M1) are complete; T-016…T-018 finish the collection round.

The task files in [tasks/](../tasks/) are the source of truth for status. This
document defines **what** gets built and **in which order**. It does not track
status, so that concurrent agents never conflict on it.

## Goal

An **investigative case study** of Romanian political pollsters: which ones
deviate systematically, toward or against whom, and how much their polls can
be trusted. The findings are **explained simply to the general public**, which
is the top priority ([ADR-0008](decisions/0008-product-positioning.md)). The
methodology is fully published ([METHODOLOGY.md](METHODOLOGY.md)). This is not
a poll aggregator.

## MVP scope ([ADR-0007](decisions/0007-mvp-scope.md))

| Election | ID | Date | Notes |
|---|---|---|---|
| Parliamentary 2024 | `parl-2024-cd` | 2024-12-01 | The Chamber of Deputies list vote is the comparison target |
| Presidential 2025, round 1 | `pres-2025-r1` | 2025-05-04 | |
| Presidential 2025, round 2 | `pres-2025-r2` | 2025-05-18 | |

**Pollsters:** 2–4 popular, transparent houses, chosen by a scorecard (T-006).
**Polls:** full toplines (every option published), with the originals archived.

**Known MVP limitations:** at most 3 (house, election) pairs per house, so
significance results are preliminary. With only 2–4 houses, the market
reference is thin (see I-013). The MVP proves the pipeline, the metrics, and
the visuals; it does not give final verdicts.

## Related work

- **sondajeromania.ro** is a poll **aggregator** (averages, trends, seat
  projections, coalition simulations) with 20+ houses and a simple accuracy
  table (the mean absolute error of each house's last poll, and the candidate
  it "favored"). This project is an **investigation** instead. It measures
  error relative to the market (separating house error from industry-wide
  misses), looks at the whole campaign rather than only the final poll, adds
  significance and uncertainty, herding/convergence detection, a trust score
  with a certainty level, and full provenance. We take **design inspiration
  only** from it (visual design, design system, UX, light mode; ADR-0009), none
  of its mechanisms. It is also a future discovery source (I-017).
- **gov2-ro/prezenta.roaep.ro:** an open-source downloader for AEP results
  data. Reference for T-010.

## Phases & tasks

Legend: tasks without dependencies inside the same phase can run **in parallel**.
Task files exist for Phases 0–2, T-030, and T-031. Later phases are refined
into task files when they start.

### Phase 0: Foundations
| ID | Task | Depends on |
|---|---|---|
| T-001 | Define data model & CSV schemas | none |
| T-002 | Python project skeleton (uv, ruff, pytest) | none |
| T-003 | Data validation tooling | T-001, T-002 |
| T-004 | Election, party & alliance registry (MVP elections) | T-001 |
| T-005 | Pollster registry & transparency metadata | T-001 |
| T-006 | Select MVP pollsters (scorecard; needs owner approval) | T-005 |
| T-007 | Schema amendments from Phase 0 follow-ups (incl. "ran on another party's list") | T-003, T-004, T-005 |
| T-008 | Continuous integration: tests, lint, and validation on every PR | T-003 |

**Milestone M0:** schemas are frozen, validation runs, and the MVP pollsters
are approved.

### Phase 1: Data collection (MVP)
| ID | Task | Depends on |
|---|---|---|
| T-010 | Results ingestion from AEP: all 3 MVP elections | T-002, T-003, T-004 |
| T-011 | Poll ingestion toolkit (archive, extraction, double-entry protocol) | T-001, T-002, T-006 |
| T-012 | Polls: AtlasIntel (all 3 elections) | T-011 |
| T-013 | Polls: Sociopol (all 3 elections; media-only sources) | T-011 |
| T-014 | Polls: CURS (all 3 elections) | T-011 |
| T-015 | Polls: Verifield (all 3 elections; campaign house) | T-011 |
| T-016 | Sponsor source: credit M-5.3 "client disclosed" only when the pollster discloses it | T-012–T-015 |
| T-017 | Poll tooling fixes (archive, extract, double-entry-diff) from the collection round | T-011 |
| T-018 | Protocol and data-model clarifications (owner decisions from the collection round) | T-016 |

The selection and its rules are in [ADR-0012](decisions/0012-mvp-pollsters.md).
T-011 committed three demonstration polls (Verifield round 2; Sociopol
round 2 and parliamentary 20–22 Nov 2024). T-013 and T-015 continue those
files and do not collect them again. The protocol is
[POLL_INGESTION.md](POLL_INGESTION.md).

**Milestone M1:** the 3 elections have validated results, and every selected
pollster has validated full-topline polls with archived originals. The four
pollster tasks run in parallel with each other, after T-011.
**Reached 2026-11-27:** 45 polls (AtlasIntel 11, CURS 10, Sociopol 19,
Verifield 5) across the three elections.

### Phase 2: Core metrics
| ID | Task | Depends on |
|---|---|---|
| T-020 | Data preparation pipeline (M-1) | T-002, T-003 |
| T-021 | Error metrics (M-2.1–M-2.4) | T-020 |
| T-022 | Relative house effect & accuracy (M-2.5, M-2.6) | T-021 |
| T-023 | Market average & campaign house effect (M-3.1, M-3.2) | T-020 |
| T-024 | Significance tests (M-4.1–M-4.3) | T-022 |
| T-025 | First analysis report + parameter sensitivity | T-021–T-024, M1 |

**Milestone M2:** a reproducible report compares the MVP pollsters on the 3
elections.
Development can start on synthetic fixtures before M1 is reached.

### Phase 3: Internal prototype & UX
| ID | Task | Depends on |
|---|---|---|
| T-030 | Prototype dashboard on real data (leaderboard, house × party heatmap, pollster card, timeline), **applying the post-mock-up decisions**: 28-day window, balanced card lead, provisional grades, notices for post-vote and unverified polls, and a source link (original + archived copy) on every number (I-019) | T-025, T-031 |
| T-031 | UX concept & design references (storyboards, wireframes, visual language) in [docs/ux/](ux/); mock-ups at [docs/ux/mockups/index.html](ux/mockups/index.html) | none: **can start now** |

**Milestone M3:** the owner can explore every metric visually, through the UX
concept.

### Phase 4: Advanced models & trust score
| ID | Task | Depends on |
|---|---|---|
| T-040 | Hierarchical Bayesian bias model (M-4.4) | T-022 |
| T-041 | Herding detection (M-3.4) | T-020 |
| T-042 | Convergence flag + calibration (M-3.3) | T-023 |
| T-043 | Trust score v1 (M-5) | T-040, T-041, T-042, T-005 |

**Milestone M4:** every pollster has a grade, a certainty level, and an
explanation.

### Phase 5: Public website
| ID | Task | Depends on |
|---|---|---|
| T-050 | ADR: public web stack & hosting | M3 |
| T-051 | Romanian UX copy guidelines & methodology page | T-043 |
| T-052 | Build the public site | T-050, T-051 |
| T-053 | Right-of-reply process for pollsters | T-043 |
| T-054 | Legal/wording review before launch | T-051, T-053 |

**Milestone M5:** public launch.

### Phase 6: Scale & expansion
This phase is designed after the MVP. It solves the *quantity* problem: more
pollsters, more elections, and less manual work.

| ID | Task | Depends on |
|---|---|---|
| T-060 | Adjusted poll feature (M-6) | T-040, T-052 |
| T-061 | Backfill elections: EP 2024, Presidential 2024 R1, then 2014–2020 | M1 |
| T-062 | Local elections (selected races) | M1 |
| T-063 | Ongoing ingestion of new polls | T-052 |
| T-064 | Extend coverage to all active pollsters | M1 |
| T-065 | Automated discovery & extraction (RSS, LLM-assisted, sondajeromania.ro scraping per I-017, all with verification) | T-011 |

## Open questions (owner)

| # | Question | Blocks |
|---|---|---|
| Q1 | Public project/brand name and domain | T-052 |
| Q2 | License for code (e.g. MIT) and data (e.g. CC BY 4.0) | T-052 |
| Q3 | Confirm proposed ADRs 0003–0006 | none (they are working defaults) |
| Q4 | Publish pollster grades by name from day one, or only after the right-of-reply period? | T-053 |
| Q5 | ~~Approve the MVP pollster selection~~ Answered 2026-11-22: ADR-0012 | none |
