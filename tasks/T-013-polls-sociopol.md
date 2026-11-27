---
id: T-013
title: "Polls: Sociopol (MVP elections)"
status: done
phase: 1
depends_on: [T-011]
owner: copilot-agent (Opus)
branch: task/T-013-polls-sociopol
methodology: [M-1.1, M-1.3, M-1.4, M-1.5, M-1.7, M-5.3]
created: 2026-11-22
updated: 2026-11-27
---

## Goal
Every published voting-intention poll by **Sociopol** (`sociopol`) for the 3
MVP elections, captured as a **full topline**, with transparency metadata and
provenance.

Collection windows (fieldwork end date):
- `parl-2024-cd`: 120 days before 2024-12-01
- `pres-2025-r1`: 120 days before 2025-05-04
- `pres-2025-r2`: head-to-head polls with fieldwork between 2025-05-05 and
  2025-05-17. Pre-R1 hypothetical pairings are not R2 polls (R-84).

## Context
- Follow `docs/POLL_INGESTION.md` (from T-011) step by step.
- [ADR-0012](../docs/decisions/0012-mvp-pollsters.md) and its report
  [pollster-selection.md](../docs/reports/pollster-selection.md) give the
  rules, evidence and publication formats for this house. Read its §5.
- Expected volume: about 14 polls (12 in round 1). The house has no website
  of its own; its polls are published only through the România TV
  broadcasts and articles.
- **Media-only sources** (ADR-0012 rule 1): record each poll with
  `verified = false`, and archive the article and any broadcast graphic. When
  the TV graphic and the article text disagree, use the graphic as the
  primary value and put the text value in `notes`. Known case: the 20–22 Nov
  2024 parliamentary poll shows USR at 13% on the graphic and 15% in the text.
- That 20–22 Nov 2024 parliamentary poll is missing from all discovery
  indexes. Search beyond them (rule 4).
- Toplines are published without an undecided share. If a topline sums to 100
  with no undecided option, record exactly what was published and note it. A
  DATA_MODEL clarification may follow.
- The round-2 poll is known only from an on-air statement by the director. Do
  not invent fields, and mark gaps in `notes`.
- Every option is recorded exactly as published. Never normalize, round, or
  guess.
- Wording follows [ADR-0003](../docs/decisions/0003-neutral-language.md).
  Affiliation records are factual and sourced (T-005).

## Scope
**In:**
- `data/polls/sociopol/` (polls, poll results, archive manifest, inventory)
- Append-only additions to the entity registry (only entities that T-004
  missed)

**Out:**
- Other pollsters, and analysis.

## Acceptance criteria
- [x] The inventory lists every publication found, including polls missing
      from the discovery indexes. Each one is either extracted or excluded
      with a reason.
- [x] Every extracted poll has an archived original (hash + Web Archive URL).
      For broadcast graphics, the archived item is the best available
      capture; say which in `notes`.
- [x] Every poll transcribed by hand passed the double-entry diff.
- [x] `uv run sondaje validate` reports 0 errors.
- [x] The Outcome reports polls per election, the % from the original source,
      and the gaps.

## Follow-ups
Proposals for the coordinator (no new task IDs created):

1. **Capital's Sociopol PDF** (`https://media.capital.ro/wp-content/uploads/2025/04/Sociopol-2025-04-Romania-TV.pdf`,
   embedded in Capital's article on the 7 - 11 Apr 2025 poll) could not be
   downloaded: `media.capital.ro` refused connections on 2026-11-27 (also
   through a remote fetch) and the Web Archive has no capture. Its inventory
   row stays `found`. Retry; if it is the 7 - 11 Apr report, it should become
   that poll's document (then `source_type = pollster`, `verified = true`).
2. **Undated party ranking** (T-011 follow-up): `PSD 33%, PNL 19%, AUR 18%,
   USR 12%, SOS 6%, UDMR 5%` was first published by România TV on 10 Nov 2024
   (article `..._8605681`), next to the presidential results that the 24 Nov
   article dates to 4 - 8 Nov 2024; the only technical paragraph of the 10 Nov
   article (28 Oct - 1 Nov 2024) belongs to the earlier survey it quotes. Tying
   the ranking to the 4 - 8 Nov survey needs a cross-article inference, so it
   is excluded (`other`). Owner decision: accept the inference (then a partial
   parl poll ending 2024-11-08 could be added) or keep it excluded.
3. **6 May 2025 "first round-2 poll"** (Simion 49%, Dan 30% of the total
   population), posted by the Sociopol director on Facebook and reported by
   România TV and Puterea: no fieldwork dates or sample, so R-84 cannot be
   checked; excluded (`other`). The Facebook page of the director is a Sociopol
   publication channel (slides are also posted there) that scripts cannot
   read; a manual capture could recover dates.
4. **DATA_MODEL clarification (share base).** Sociopol's own slides and
   reports print `% din răspunsurile valide ale celor care estimăm că ar merge
   la vot (VOTANȚI HOTĂRÂȚI, X% din tot. pop.)` as the only base. It is
   recorded as `expressed_option` with the base quoted in `notes` (it is the
   pollster's headline and only base, METHODOLOGY OI-1), whereas T-011 used
   `other_subset` for Verifield's third base "expressed votes of those who will
   vote". §6.12 could say which to use when such a base is the only one.
5. **POLL_INGESTION addition (photo-only graphics).** Most România TV graphics
   show candidates as photos without names. The rule applied here (label =
   the name as written in the archived article of the same poll that lists the
   candidates with the same shares; say so in `notes`) could be added to §7/§8.
6. **ADR-0012 / pollster-selection §4 wording.** Sociopol is not purely
   media-only: two polls (14 - 17 and 28 - 30 Apr 2025) are recorded from
   Sociopol's own PDF reports (hosted by România TV and DCNews) with
   `verified = true`, and two from Sociopol slides republished by media
   (`source_type = pollster`, `verified = false`). The coordinator may want to
   confirm this reading and update the "media only" description.
7. **Tools.** `extract-html` text mode found the values of `Name - 50%` lines
   but left the labels empty; `extract-pdf` cannot read the Sociopol PDFs (text
   layer with spaced letters and split numbers), so they went through double
   entry. Possible improvements for a toolkit task.
8. **Mode convention.** "interviuri telefonice" without the word CATI was
   recorded as `cati` (31 Mar - 4 Apr 2025, from the CNA decision; 3 - 7 Mar
   2025 first article). DATA_MODEL §6.11 could state this explicitly.
9. **2024 presidential polls** (election annulled, not in the registry) are
   listed as `out_of_scope`; they would be ready if `pres-2024-*` is ever
   registered.

## Log
- **2026-11-27 Setup.** Worktree `E:\Projects\sondaje-wt\T-013`, branch
  `task/T-013-polls-sociopol` from `main`; rebased on `main` (175aa60) before
  hand-off.
- **2026-11-27 Discovery (indexes).** EN Wikipedia "2025 Romanian presidential
  election" and "Opinion polling for the 2024 Romanian parliamentary
  election", RO Wikipedia "Sondaje de opinie pentru alegerile prezidențiale din
  România, 2025" and "... din 2024", sondajeromania.ro `/institute/sociopol`
  (parliamentary series only; no Sociopol poll in the parl window). The
  indexes list the 12 round-1 surveys (10 - 15 Jan to 28 - 30 Apr 2025), the
  10 - 12 May round-2 poll and exit polls; no Sociopol parliamentary poll in
  the 120-day window.
- **2026-11-27 Discovery (partner outlet).** România TV tag pages
  (`/tag/sociopol`, `/tag/sondaj-sociopol`); the WordPress REST search
  (`/wp-json/wp/v2/posts?search=sociopol`) returned its first page (posts from
  21 Apr 2025 on) and then HTTP 403; a full scan of the post sitemaps 318 - 349
  (IDs 7.8 M - 9.0 M, Aug 2024 - Jun 2025) for slugs with "sociopol" or
  "palada" gave 42 articles, all reviewed. Probes of
  `wp-content/uploads/2025/0X/Sociopol-2025-0X[-a..f]-Romania-TV.pdf` and Web
  Archive CDX prefix queries found one Sociopol PDF on România TV (`-c-`), one
  on DCNews (`-e-`) and none on Capital/Gândul in the archive.
- **2026-11-27 Discovery (web search).** Monthly searches (Aug 2024 - May
  2025) for "sondaj Sociopol" with party/candidate names and dates, and chains
  from the articles to their sources. Found outside the indexes: the
  **14 - 18 Oct 2024 parliamentary poll** (PS News / DCNews, 24 Oct 2024), the
  full 10 - 15 Jan 2025 toplines (Realitatea, via Accentul Zilei / Reflexul
  Zilei), the 17 - 21 Mar Sociopol slide (Gândul), the CNA decision with the
  31 Mar - 4 Apr technical data (cited by RO Wikipedia), the Flux de Știri
  labels for 31 Mar - 4 Apr, and both Sociopol PDF reports.
- **2026-11-27 Inventory.** 70 rows added (74 in total): every publication
  opened, including duplicates, exit polls, 2024 presidential polls
  (`out_of_scope`) and the undated / statement-only items (`other`,
  `no_topline`). Rows only seen through an index or a search snippet carry
  `verified = false`.
- **2026-11-27 Archive.** 32 documents archived (`sociopol-doc-005` ...
  `-036`) with `sondaje archive`; one Save Page Now call hit HTTP 429 and
  fell back to an existing capture. All images and PDFs matched their
  snapshots except `sociopol-doc-019` (Gândul PNG), which the Web Archive
  serves gzip-encoded: decompressed, it is identical. HTML snapshots differ in
  bytes as usual; for each one the article's poll passages were found in the
  snapshot text (scripted check, one passage differing only in spacing on
  `sociopol-doc-020`). The CNA decision (`sociopol-doc-022`) returns 404 at its
  original URL and was archived from its 2025-05-05 Web Archive capture
  (`--file` + `--archive-url`).
- **2026-11-27 Extraction paths.** `extract-html` text mode for the 10 - 15 Jan
  (Realitatea), 27 - 30 Jan (Știripesurse) and 7 - 11 Apr (România TV) polls:
  the drafts had the values but empty labels for `Name - N%` lines; the labels
  were taken from the same lines, the non-option rows deleted, and every row
  reviewed against the archived page. The 10 - 14 Feb tables print numbers
  without `%` (the draft missed them) and the two Sociopol PDFs have an
  unreadable text layer (`extract-pdf` auto/chart/lines found no usable
  pairs), so these went to double entry with the other images and prose.
- **2026-11-27 Double entry.** 10 folders (12 polls) under
  `build/double-entry/`, each with only the archived inputs (plus article-text
  extractions and rendered PDF pages), the protocol, DATA_MODEL, ADR-0012,
  ADR-0003, the entity registry and a brief without values. Pass A:
  `claude-opus-5.5`; pass B: `claude-sonnet-5.5`; separate sub-agents, neither
  saw the other's files. `double-entry-diff` results and resolutions (against
  the archived originals):
  - 20241018 (parl), 20250318, 20250404, 20250426, 20250417, 20250430:
    0 mismatches.
  - 20250214 and 20250307: `scenario` text (A described the headline scenario,
    B left it empty; different wording for scenario B). Free-text description;
    A's wording kept as the closer paraphrase of the printed questions.
  - 20250321 and 20250423: `source_type` (A `pollster`, B `media`) →
    `pollster`: the image is Sociopol's own slide (logo, base line) hosted by a
    media outlet, as for `verifield-doc-001`. `share_base` (A
    `expressed_option`, B `likely_voters`) → `expressed_option`: valid answers
    are the base and it is the only one published (see Follow-up 4).
  - 20250423, then: `share_qualifier` of "Alți candidați (sub 1%)" (A empty,
    B `lt`) → empty: the slide prints the exact value 1; "(sub 1%)" describes
    each other candidate.
  After the corrections every diff reports 0 mismatches; pass A's rows were
  copied into the data and reviewed against the originals (values, labels,
  dates, n, method, client, wording).
- **2026-11-27 Post-diff change.** R-63 needs one document per survey: the two
  3 - 7 Mar scenarios (one graphic each) now both use the 1 Apr 2025 article
  that embeds both graphics (`sociopol-doc-015`); the scenario-B graphic shown
  there was archived too (`sociopol-doc-036`). Values unchanged.
- **2026-11-27 Decisions.**
  - `verified = true` only for the two polls whose values and methodology come
    from Sociopol's own PDF reports (14 - 17 Apr, 28 - 30 Apr); slides
    republished by media keep `verified = false` (metadata from media); all
    other polls are media-only (`verified = false`).
  - Photo-only graphics: labels from the archived article listing the same
    candidates with the same shares (noted per row).
  - "Alți candidați (sub 1%)" / "ALȚII" are recorded with the printed value and
    no qualifier; "sub 1%" in an article is kept in `notes` when a graphic or
    slide prints a number (graphic / pollster wins).
  - 10 - 15 Jan and 27 - 30 Jan: the only full lists come from secondary media
    and show no "others" option (sums 97 - 99), so `topline_coverage =
    partial`.
  - 3 - 7 Mar client: România TV, from the 1 Apr article's sentence that
    introduces this survey's first-scenario results (noted); 17 - 18 Mar and
    14 - 18 Oct 2024: no client named, `not_disclosed`.
- **2026-11-27 Gaps.** See the Outcome. No entity had to be added to the
  registry.
- **2026-11-27 Checks.** `uv sync`; `uv run pytest` (352 passed);
  `uv run ruff check .` (passed); `uv run ruff format --check .` (passed);
  `uv run sondaje validate --against main` (0 errors; no Sociopol warnings).

## Outcome
**Recorded:** 19 Sociopol polls in `data/polls/sociopol/` (17 new, 2 from
T-011), 120 result rows, 36 archived documents, 74 inventory rows.

| Election | Surveys found | Polls recorded | Own-source (pollster report) | Pollster slide via media | Media only | Outside the indexes |
|---|---|---|---|---|---|---|
| `parl-2024-cd` | 2 dated surveys (+ 1 undated ranking, 1 statement) | 2: 14 - 18 Oct 2024 (new), 20 - 22 Nov 2024 (T-011) | 0 | 0 | 2 | both |
| `pres-2025-r1` | 12 | 16 (12 headline + 4 scenario-B polls of the Jan, Feb and Mar surveys) | 2 surveys (14 - 17 Apr, 28 - 30 Apr) = 17% | 2 (17 - 21 Mar, 21 - 23 Apr) | 8 | none (all 12 were indexed; several of their sources were not) |
| `pres-2025-r2` | 1 | 1: 10 - 12 May 2025 (T-011) | 0 | 0 | 1 | no |

Share from the pollster's own publications: 2 of 15 surveys (13%) are fully
from Sociopol reports (`verified = true`); with the two slides, Sociopol's own
material supplies the shares of 4 of 15 surveys (27%). All other polls are
media-only (`verified = false`): România TV broadcast graphics and articles,
and for January Realitatea and Știripesurse.

T-011 polls (listed, not re-collected): `sociopol-parl-2024-cd-20241122`,
`sociopol-pres-2025-r2-20250512`.

**Excluded (with reasons in the inventory):** parl: the undated ranking (twice,
`other`), the director's on-air ranges of 15 Nov 2024 (`no_topline`), the
1 Dec 2024 exit poll; r1: the 4 May exit poll; r2: the 6 May Facebook poll
without fieldwork (`other`, twice), the 8 May forecast and the 16 May estimate
(`other`), two exit polls; 8 România TV articles on 2024 presidential polls
(`out_of_scope`); 19 duplicate media reports. One row stays `found` (Capital's
PDF, unreachable).

**Gaps:**
- Toplines: 10 - 15 Jan and 27 - 30 Jan (both scenarios) are partial lists
  from secondary media; the original broadcast graphics were not found (the
  client's articles give only the leading candidates).
- No undecided / non-response shares are published for any poll; Sociopol's
  slides and reports state the base (valid answers of likely voters, 50 - 55%
  of the population), the TV graphics do not.
- M-5.3 items: question wording missing for 17 - 18 Mar, both scenario-B
  questions of January, and the 14 - 18 Oct 2024 poll; weighting published only
  for 10 - 14 Feb, 7 - 11 Apr, 14 - 17 Apr and 28 - 30 Apr; population missing
  for the TV-graphic polls; client not stated for 17 - 18 Mar 2025 and
  14 - 18 Oct 2024.
- 27 - 30 Jan margin of error: ±3% (Știripesurse, used) vs ±3.2% (a later
  DailyBusiness report).
- 7 - 11 Apr: Capital's Sociopol PDF could not be archived (Follow-up 1).

**Key commits:** `8997673` start, `968e779` inventory and archive,
`e472d83` polls; final commit with the Log/Outcome.
