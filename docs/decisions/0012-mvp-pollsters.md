# ADR-0012: MVP pollsters: AtlasIntel, Sociopol, CURS and Verifield, with MKOR as reserve

- **Status:** Accepted
- **Date:** 2026-11-22 (owner decisions given in chat with the coordinator)
- **Related:** ADR-0003, ADR-0007, ADR-0010, T-005, T-006, T-011, T-012…T-015,
  T-025, M-1.3, M-1.4, M-1.7, M-3.2, M-5.3; evidence in
  [docs/reports/pollster-selection.md](../reports/pollster-selection.md)

## Context
[ADR-0007](0007-mvp-scope.md) limits the MVP to 2–4 pollsters for
`parl-2024-cd`, `pres-2025-r1` and `pres-2025-r2`, chosen through a documented
scorecard. The required criterion (T-006) is at least one poll in the **final
accuracy window** (M-1.3) for **each** of the three elections.
[ADR-0010](0010-grades-and-card-framing.md) gives a (provisional) grade only
to houses with at least 3 elections that have a final poll.

The T-006 scorecard covers all 15 registered houses. With the original
21-day window only AtlasIntel and Sociopol had a final-window poll in all
three elections; CURS's latest parliamentary and round-1 polls ended 26 and 24
days before the vote, Verifield's 53 and 37 days. Several sources are
media-only (Sociopol), one AtlasIntel poll was published after election day,
and some polls include the diaspora. The owner was asked five questions
(Q-A to Q-E) and decided them on 2026-11-22.

The selection criteria are data availability and transparency. Accuracy,
house effects and affiliation records were not considered (affiliations are an
input to M-5.1d).

## Decision

### Owner decisions (2026-11-22)

| # | Question | Decision |
|---|---|---|
| Q-A | CURS is outside the 21-day window for two elections | **Wider window for all houses:** M-1.3 `window_days` default 21 → **28**. T-025 tests 21 and 35 days as sensitivity. |
| Q-B | Media-only sources (Sociopol) | **Accepted**, with `verified = false`. For Sociopol the **TV broadcast graphic is the primary value**; a differing article-text value goes in `notes`. The UI shows a lower verification level for such polls. |
| Q-C | Polls published on or after election day (AtlasIntel 1–3 May 2025, published 5 May) | **Shown** to users with an explicit notice that they were published after the vote, but **excluded from all calculations** (errors, house effects, market average, significance, trust score). A house's final poll is its latest poll published before election day. New METHODOLOGY section **M-1.7**. |
| Q-D | Polls that include the diaspora | Apply **M-1.4 as written**: a poll that explicitly includes the diaspora is compared to the `total` result; otherwise `domestic`. |
| Q-E | A 4th house | **Yes: Verifield** joins as the 4th house. |

### Selected houses (4) and reserve (1)

Final windows with `window_days` = 28 (`fieldwork_end` from 2024-11-03,
2025-04-06, 2025-04-20; round 2 also needs `fieldwork_start` after
2025-05-04, R-84). Gap = election day − `fieldwork_end` of the latest eligible
poll (published before election day, M-1.7).

| House | parl-2024-cd | pres-2025-r1 | pres-2025-r2 | Coverage (all 3) | Why |
|---|---|---|---|---|---|
| **AtlasIntel** (`atlasintel`) | ✓ 26–28 Nov (3 d) | ✓ 28 Apr–1 May (3 d) | ✓ 13–15 May (3 d) | **Yes** | Full toplines incl. "don't know" and null/blank on two bases; own-site reports with n, dates, mode, MoE, client; high media reach. Its 1–3 May poll is excluded (M-1.7); the 28 Apr–1 May poll, published 1–2 May, is its round-1 final poll. |
| **Sociopol** (`sociopol`) | ✓ 20–22 Nov (9 d) | ✓ 28–30 Apr (4 d) | ✓ 10–12 May (6 d) | **Yes** | Most frequent house in round 1 (12 polls); CATI; TV-station client. Media-only sources, expressed toplines (Q-B). |
| **CURS** (`curs`) | ✓ 30 Oct–5 Nov (26 d) | ✓ 3–10 Apr (24 d) | ✓ 8–11 May (7 d) | **Yes** (with 28 days) | Own-site text PDFs with 6 of 7 M-5.3 items, incl. weighting; face-to-face and CATI. Its round-2 poll is known through TVR Info only. |
| **Verifield** (`verifield`) | ✗ 7–9 Oct (53 d) | ✗ 24–28 Mar (37 d) | ✓ 6 May (12 d) | **No — round 2 only** | Owner decision Q-E. Polls in all three 120-day campaign windows; round-2 report is a text PDF with a full topline. |
| *Reserve:* **MKOR** (`mkor`) | ✗ no 2024 parliamentary poll | ✓ 24–27 Apr (7 d) | ✓ 8–14 May (4 d) | No | Highest transparency (7/7) and full toplines on an own-site HTML report. |

**Verifield does not meet the coverage requirement**, even with the 28-day
window (and also not with 35 days): it has no parliamentary or round-1 poll
ending within 28 days of the vote. It is selected by owner decision as a
**campaign house**: its polls enter the market average and the campaign house
effect (M-3) in all three elections, and the final-poll metrics (M-2) only
for round 2. Under ADR-0010 its card shows "no grade yet" in the MVP.
AtlasIntel, Sociopol and CURS can receive provisional grades.

The set spans three collection modes (online after random digital
recruitment, CATI, face-to-face/CATI) and four client situations (an online
news outlet, a TV station, no client stated, and a party and candidates'
teams). The reserve adds a self-funded online panel.

### Rules for the data tasks (T-012 onward)
1. **Media-only sources** (Q-B): record them with `verified = false` and archive
   the article and any broadcast graphic. When a broadcast graphic and the
   article text disagree, use the graphic and record the text value in `notes`
   (known case: Sociopol 20–22 Nov 2024, USR 13% on the graphic vs 15% in the
   text).
2. **Publication timing** (Q-C, M-1.7): record every poll, including those
   first published on or after election day, with its true `published_date`;
   the pipeline excludes them from all metrics.
3. **Diaspora** (Q-D, M-1.4): set `population_geo` / `target_scope` from the
   report. `residents_and_diaspora` → `total` (e.g. Noi, Cetățenii; AtlasIntel
   where its report or partner states that the figures include the diaspora).
4. **Search beyond the discovery indexes**: own sites and partner outlets.
   Polls missing from all indexes included Sociopol 20–22 Nov 2024 and BCS
   26–29 Sep / 7–10 Nov 2024.
5. When sources disagree on a methodology item (e.g. AtlasIntel parliamentary
   MoE ±2 pp in the report vs ±3% in HotNews), use the pollster's report
   (DATA_MODEL §6.11).

## Consequences
- The coordinator creates one data task per house (T-012 onward) from
  [the template](../../tasks/_TEMPLATE-pollster-data.md). Expected volume in
  the 120-day windows: AtlasIntel ~9 polls (1 excluded by M-1.7),
  Sociopol ~14, CURS ~7, Verifield ~4–5 (approximate).
- METHODOLOGY changed: M-1.3 default `window_days` = 28, and new M-1.7.
  Recency weighting (τ = 7) is unchanged, so polls 22–28 days out get a small
  weight.
- **T-011** must support `pdf_text`, `html`, and manual double entry from
  images and rendered PDF pages (AtlasIntel charts, Sociopol broadcast
  graphics, CURS slide PNGs).
- The UI must show (a) a lower verification level for `verified = false`
  polls and (b) a "published after the vote" notice for M-1.7 polls.
- Verifield has fewer than 3 elections with a final poll and gets no grade in
  the MVP; with 4 houses the market reference (M-2.5, M-3.1) is still thin
  (I-013).
- Other documents still say "21 days" (T-025 sensitivity list, UX docs and
  mock-ups); they are updated through follow-up tasks.

## Alternatives considered
- **Keep 21 days and select only AtlasIntel and Sociopol:** the smallest
  collection effort, but a two-house market reference. Rejected by the owner (Q-A).
- **Treat CURS as a campaign-only house at 21 days:** rejected in favour of a
  single, wider window for all houses (Q-A).
- **Reject media-only sources:** would remove Sociopol, one of the two houses
  with complete coverage. Rejected (Q-B).
- **Count polls published after the vote:** they could not have informed
  voters and would mix pre- and post-election information. Rejected (Q-C).
- **INSCOP, BCS or CIRA:** transparent parliamentary sources, but no 2025
  pre-election polls. **IRSOP, Noi, Cetățenii:** both presidential rounds but
  no 2024 parliamentary poll. MKOR is kept as the reserve.