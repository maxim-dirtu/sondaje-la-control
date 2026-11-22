# Project Plan

**Last updated:** 2026-11-22 · **Current phase:** 0 (Foundations)

The task files in [tasks/](../tasks/) are the source of truth for status. This
document defines **what** gets built and **in which order**. It does not track
status, so that concurrent agents never conflict on it.

## Goal

A public, explainable rating of Romanian political pollsters covering:
accuracy, systematic party lean, campaign behaviour, and a trust score with a
certainty level. The methodology is fully published
([METHODOLOGY.md](METHODOLOGY.md)).

## Initial data scope (MVP)

| Election | Date | Notes |
|---|---|---|
| European Parliament 2024 | 2024-06-09 | Held together with local elections |
| Presidential 2024, round 1 | 2024-11-24 | Annulled by the Constitutional Court; polls still evaluable |
| Parliamentary 2024 | 2024-12-01 | Chamber of Deputies list vote as the target |
| Presidential 2025, round 1 | 2025-05-04 | |
| Presidential 2025, round 2 | 2025-05-18 | |

Backfill (Phase 6): 2014 and 2019 presidential; 2016 and 2020 parliamentary;
2019 European Parliament; selected local races (e.g. Bucharest mayor).

## Phases & tasks

Legend: tasks without dependencies inside the same phase can run **in parallel**.
Task files exist for Phases 0–2. Later phases are refined into task files when
they start.

### Phase 0: Foundations
| ID | Task | Depends on |
|---|---|---|
| T-001 | Define data model & CSV schemas | none |
| T-002 | Python project skeleton (uv, ruff, pytest) | none |
| T-003 | Data validation tooling | T-001, T-002 |
| T-004 | Election, party & alliance registry (2024–2025) | T-001 |
| T-005 | Pollster registry & transparency metadata | T-001 |

**Milestone M0:** schemas are frozen and validation runs on empty and sample data.

### Phase 1: Data collection 2024–2025
| ID | Task | Depends on |
|---|---|---|
| T-010 | Results: EP 2024 | T-003, T-004 |
| T-011 | Results: Presidential 2024 R1 | T-003, T-004 |
| T-012 | Results: Parliamentary 2024 | T-003, T-004 |
| T-013 | Results: Presidential 2025 R1 & R2 | T-003, T-004 |
| T-014 | Polls: EP 2024 | T-003, T-004, T-005 |
| T-015 | Polls: Presidential 2024 R1 | T-003, T-004, T-005 |
| T-016 | Polls: Parliamentary 2024 | T-003, T-004, T-005 |
| T-017 | Polls: Presidential 2025 R1 & R2 | T-003, T-004, T-005 |

**Milestone M1:** all 5 elections have validated results and polls, with full
provenance. All 8 tasks can run in parallel.

### Phase 2: Core metrics
| ID | Task | Depends on |
|---|---|---|
| T-020 | Data preparation pipeline (M-1) | T-002, T-003 |
| T-021 | Error metrics (M-2.1–M-2.4) | T-020 |
| T-022 | Relative house effect & accuracy (M-2.5, M-2.6) | T-021 |
| T-023 | Market average & campaign house effect (M-3.1, M-3.2) | T-020 |
| T-024 | Significance tests (M-4.1–M-4.3) | T-022 |
| T-025 | First analysis report + parameter sensitivity | T-021–T-024, M1 |

**Milestone M2:** a reproducible report ranks pollsters on 2024–2025 data.
Development can start on synthetic fixtures before M1 is reached.

### Phase 3: Internal prototype
| ID | Task | Depends on |
|---|---|---|
| T-030 | Prototype dashboard (leaderboard, house × party heatmap, pollster card, timeline) | T-025 |

**Milestone M3:** the owner can explore every metric visually.

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

### Phase 6: Expansion
| ID | Task | Depends on |
|---|---|---|
| T-060 | Adjusted poll feature (M-6) | T-040, T-052 |
| T-061 | Backfill 2014–2020 elections | M1 |
| T-062 | Local elections (selected races) | M1 |
| T-063 | Ongoing ingestion of new polls | T-052 |

## Open questions (owner)

| # | Question | Blocks |
|---|---|---|
| Q1 | Public project/brand name and domain | T-052 |
| Q2 | License for code (e.g. MIT) and data (e.g. CC BY 4.0) | T-052 |
| Q3 | Confirm proposed ADRs 0003–0006 | none (they are working defaults) |
| Q4 | Publish pollster grades by name from day one, or only after the right-of-reply period? | T-053 |
