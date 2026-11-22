# ADR-XXXX: MVP pollsters: AtlasIntel, Sociopol and CURS, with Verifield and MKOR as reserves

- **Status:** Proposed (awaiting owner approval; open questions below)
- **Date:** 2026-11-22
- **Related:** ADR-0003, ADR-0007, ADR-0010, T-005, T-006, T-011, T-012…T-015,
  M-1.3, M-1.4, M-3.2, M-5.3; evidence in
  [docs/reports/pollster-selection.md](../reports/pollster-selection.md)

## Context
[ADR-0007](0007-mvp-scope.md) limits the MVP to 2–4 pollsters for
`parl-2024-cd`, `pres-2025-r1` and `pres-2025-r2`, chosen through a documented
scorecard. T-006 made the required criterion explicit: at least one poll in the
**final window** (M-1.3: fieldwork ending ≤ 21 days before election day) for
**each** of the three elections. [ADR-0010](0010-grades-and-card-framing.md)
adds weight to this: a house gets a (provisional) grade only with at least
3 elections that have a final poll.

The scorecard covers all 15 registered houses. Its main findings:

- **Only two houses meet the required coverage:** AtlasIntel and Sociopol.
  Sociopol qualifies through a parliamentary poll (20–22 Nov 2024) that is in
  none of the discovery indexes.
- **CURS** and **Verifield** poll in all three elections, but only their
  round-2 polls are inside the 21-day window. CURS's latest parliamentary and
  round-1 polls end 26 and 24 days before the vote; Verifield's end 53 and
  37 days before.
- **MKOR, IRSOP and Noi, Cetățenii** cover both presidential rounds, and did
  not poll the 2024 parliamentary election. INSCOP, BCS and CIRA cover only
  the parliamentary election; ARA, FlashData and DataEcho only round 1.
- **Formats:** AtlasIntel publishes own-site PDFs whose values sit in chart
  images; Sociopol has no website, and its results are known from România TV
  articles and broadcast graphics, with expressed-vote toplines (no undecided
  share); CURS publishes text PDFs on its own site (its round-2 poll only via
  TVR Info).

The selection criteria are data availability and transparency. Accuracy,
house effects and affiliation records were not considered (affiliations are an
input to M-5.1d).

## Decision
Proposed for owner approval:

**MVP houses (3):**

| House | Why |
|---|---|
| **AtlasIntel** (`atlasintel`) | Meets the coverage requirement; full toplines incl. "don't know" and null/blank on two bases; own-site reports with n, dates, mode, MoE, client; high media reach. |
| **Sociopol** (`sociopol`) | Meets the coverage requirement; the most frequent house in round 1 (12 polls), which helps the campaign metrics (M-3); CATI. Its sources are media-only, and toplines show no undecided share (see trade-offs). |
| **CURS** (`curs`) | Polls in all three campaigns (7 polls) with own-site text PDFs and 6 of 7 M-5.3 items, incl. a weighting description; face-to-face and CATI. Inside the 21-day window **only for round 2**, so it needs one of the owner options below. |

**Reserves (2), in order:**

1. **Verifield** (`verifield`): polls in all three campaigns; its round-2 report
   is a text PDF with a full topline. Final-window coverage only for round 2;
   most originals are media articles.
2. **MKOR** (`mkor`): highest transparency (7/7: weighting, self-funding and
   method published) and full toplines on an own-site HTML report; final-window
   polls in both presidential rounds, no 2024 parliamentary poll.

A reserve replaces a selected house if its data task finds collection
infeasible, or is added as a 4th house if the owner wants a larger market
reference (I-013).

The set spans three collection modes (online after random digital
recruitment, CATI, face-to-face/CATI) and three client situations (an online
news outlet, a TV station, no client stated). The reserves add a
party/candidate-client profile and a self-funded online panel.

### Trade-offs and questions for the owner

**Q-A. CURS and the coverage requirement.** Only two houses meet it. Options:

| Option | Effect |
|---|---|
| **A1 (proposed):** keep CURS as a "campaign house" | CURS enters the market average and the campaign house effect (M-3) in all three elections, and the final-poll metrics (M-2) only for round 2. Under ADR-0010 its card shows "no grade yet". No methodology change. |
| A2: evaluate CURS with a wider final window | A `window_days` of 28 would cover CURS's 5 Nov and 10 Apr polls. This changes M-1.3 for **all** houses (a methodology task); T-025 already plans a `window_days` sensitivity analysis. |
| A3: only the two qualifying houses | AtlasIntel + Sociopol. Smallest collection effort, but the market reference rests on two houses, both of which publish their final-window values only in images or media text. |

**Q-B. Media-only sources and expressed toplines (Sociopol).** Accepting
Sociopol means accepting România TV articles and broadcast screenshots as the
archived originals, a round-2 poll known only from the director's on-air
statement (n, dates and client stated; no mode, MoE, or question), and
toplines without undecided / non-response. One source disagreement exists
(parliamentary USR: 15% in the text, 13% on the graphic). Alternatives: accept
as is (recommended, with `topline_coverage` decided per poll), or replace
Sociopol with Verifield and relax the requirement for two elections.

**Q-C. Polls published after election day.** AtlasIntel's 1–3 May 2025 poll
(fieldwork ending one day before round 1) was published on 5 May. R-81 allows
it; R-83 only warns. Should a poll published on or after election day be
eligible as a house's final poll in M-1.3? This affects only AtlasIntel in the
proposed set.

**Q-D. Diaspora (M-1.4).** AtlasIntel's round-2 figures are reported as
including the diaspora. The data task should decide `target_scope` per poll
from the report; the owner may want a default rule for "electorate" universes.

**Q-E. Fourth house.** Add Verifield now (more houses for the market
reference; about 5 more polls, mostly media articles) or keep it in reserve?

## Consequences
- The coordinator creates one data task per approved house (T-012 onward)
  from [the template](../../tasks/_TEMPLATE-pollster-data.md). Expected volume
  in the 120-day windows: AtlasIntel ~9 polls, Sociopol ~14, CURS ~7
  (approximate).
- **T-011** must support `pdf_text`, `html`, and **manual double entry from
  images and rendered PDF pages** (AtlasIntel charts, Sociopol broadcast
  graphics, CURS slide PNGs). Google Sheets charts and video are needed only
  if Noi, Cetățenii or ARA are added later.
- Data tasks must search beyond the discovery indexes: the Sociopol
  parliamentary poll and two BCS barometers were missing from all of them.
- With A1, CURS has fewer than 3 elections with a final poll and gets no grade
  in the MVP (ADR-0010); AtlasIntel and Sociopol can get provisional grades.
- The market reference (M-2.5, M-3.1) remains thin with 3 houses (I-013).
- If the owner chooses A2, a methodology task must change M-1.3 before T-020.

## Alternatives considered
- **AtlasIntel, CURS, Verifield** (the T-005 working assumption): rejected as
  the default because CURS and Verifield have no final-window poll for two of
  the three elections; it remains available through Q-A/Q-E.
- **INSCOP or BCS**: the most transparent parliamentary sources (own-site text
  PDFs), but no 2025 pre-election polls, so at most one election per house.
- **MKOR, IRSOP or Noi, Cetățenii as main houses**: good transparency and both
  presidential rounds, but no 2024 parliamentary poll. MKOR is kept as a
  reserve.
- **Four houses now** (adding Verifield): possible (Q-E); not proposed by
  default because most of Verifield's originals are media articles and it adds
  no final-window coverage beyond round 2.
