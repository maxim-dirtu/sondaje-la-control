---
id: T-005
title: Pollster registry and transparency metadata
status: review
phase: 0
depends_on: [T-001]
owner: agent-t005
branch: task/T-005-pollster-registry
methodology: [M-5.3]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
A registry of every polling firm that published polls for the MVP elections,
with name aliases and sourced background information.

## Context
Pollster names appear in many variants across media. The aliases let the Phase 1
tasks map them consistently. The sponsor and affiliation information feeds
M-5.1d and M-5.3. [ADR-0003](../docs/decisions/0003-neutral-language.md)
applies to every description.

## Scope
**In:**
- The pollster registry file defined by T-001: ID, official name, aliases,
  website, typical survey modes, and known affiliations or regular clients
  (each with a source)
- A list of every house that published at least one poll in the 3 MVP
  elections, built from two discovery indexes: the "Opinion polling" Wikipedia
  pages and sondajeromania.ro. T-006 picks the MVP houses from this list.

**Out:**
- Per-poll transparency fields, which the poll tasks capture.

## Acceptance criteria
- [x] Every pollster with at least one poll in the indexed sources is listed.
- [x] Every affiliation or client claim has a `source_url`. Unsourced claims
      are left out.
- [x] The wording is factual and neutral.
- [x] Validation passes (or is checked manually, as in T-004).

## Follow-ups
- **Link `counterpart_entity_id` after T-004 merges.** Left empty because T-004
  runs in parallel. Rows to link: `verifield`→USR, Crin Antonescu, Nicușor Dan;
  `cira`→PNL (2 rows); `atlasintel`→Nicușor Dan. This needs a correction by
  the primary writer (T-005) or by a coordinator-assigned task (append-only rule).
- **DATA_MODEL `mode` enum gaps (proposal).** Two cases have no clean value:
  (a) face-to-face reported without saying CAPI or PAPI (CURS 2024); (b) "random
  digital recruitment" reports that don't name the interview channel (DataEcho,
  Noi, Cetățenii). Proposal: document a convention in §6.11 (e.g. `other` + notes),
  or add a `f2f` value.
- **DATA_MODEL §5.1 `verified` for registry rows (proposal).** Clarify how
  `verified` applies to aliases and affiliations. The rule this task used is
  in the Log (2026-11-22, "verified flag").
- **sondajeromania.ro has no round-2 polls.** Its presidential data stops at
  round 1. T-006 has to use Wikipedia and media for `pres-2025-r2`.
- **Exit polls are out of this registry's scope.** ARA, Avangarde, CURS, INSCOP
  and Sociopol published 2025 exit polls (all are registered anyway). If exit
  polls ever come into scope, this needs a decision first.
- **Leads not recorded (need a stronger source first):** see the Log entry
  "affiliation leads not recorded".

## Log
- **2026-11-22: setup incident.** My first front-matter edit used a relative
  path with `[IO.File]`. That resolves against the process directory, so the
  write landed in the main checkout (`E:\Projects\sondaje-la-control`). I
  reverted it at once with `git checkout -- tasks/T-005-pollster-registry.md`.
  The main checkout is clean. After that, every write used absolute worktree
  paths.
- **2026-11-22: discovery indexes used** (all retrieved 2026-11-22; wikitext was
  parsed with a scratch script):
  - EN "Opinion polling for the 2024 Romanian parliamentary election" (§2024,
    plus the end of §2023);
  - EN "Opinion polling for the 2025 Romanian presidential election". This title
    redirects to "2025 Romanian presidential election#Opinion polls", so the
    tables of that article were used (second round, first round after/before
    the BEC deadline, hypothetical second rounds);
  - RO "Sondaje de opinie pentru alegerile parlamentare din România, 2024"
    (table 15 iunie 2023–1 decembrie 2024);
  - RO "Sondaje de opinie pentru alegerile prezidențiale din România, 2025"
    (Turul II, Turul I, Ipotetice);
  - sondajeromania.ro `/institute` and the 31 `/institute/<slug>` pages. Each
    page embeds its poll list as structured data (pollster, commissioner,
    fieldwork, scope). It was used **only as a discovery index** (ADR-0009, I-017).
    No logic or metric was taken from it.
- **2026-11-22: inclusion rule** ("published at least one voting-intention poll"):
  - `parl-2024-cd`: national party vote intention with fieldwork end from
    2023-12-02 to 2024-12-01. This is 365 days, matching `max_poll_age_days`
    in DATA_MODEL §7.
  - `pres-2025-r1`: first-round vote intention after the annulment (fieldwork
    end from 2024-12-07 to 2025-05-04), including the hypothetical
    first-round scenarios.
  - `pres-2025-r2`: Dan–Simion polls after round 1 (2025-05-05 to 05-18).
    Earlier hypothetical head-to-heads are noted separately.
  - Exit polls and election-day polls are not voting-intention polls, so they
    were not counted. No house appears *only* through exit polls: INSCOP's 2025
    presidential rows are exit or election-day rows, but INSCOP qualifies
    through `parl-2024-cd`.
- **2026-11-22: index entries resolved or excluded** (not registered):
  - The Wikipedia labels "Newsweek" (EN/RO parliamentary, 24–28 Oct and 9–13
    Nov 2024) are the client, not the pollster. The pollsters are BCS (Oct, per
    Newsweek's own article and bcs.com.ro) and CIRA (Nov, per Newsweek).
  - "PNL" (RO parliamentary, Dec 2023) is a CIRA poll commissioned by PNL,
    per G4Media. Its question was European Parliament vote intention.
  - "The Center for International Research and Analyses" (EN, 24–30 Aug 2024)
    is CIRA.
  - "Verified for USR" (EN) is Verifield.
  - "USR" (EN) / "necunoscut" (RO), 24–29 Mar and 2–7 Apr 2025: party-commissioned
    polls whose pollster is not named (Euronews). Excluded: there is no
    pollster to register.
  - "Cozmin Gușă" (RO hypothetical round 1, 21–23 Jan 2025): a commentator
    presenting an unnamed "Franco-German" telephone poll (Știri pe surse).
    Excluded: no pollster named.
  - "Media Info Surveys" (RO, 13–23 Jan 2025): the only source is a Facebook
    post, and a web search found no firm by that name. Excluded: identity not
    verifiable.
  - "Europe Elects" (RO, 14–18 Feb 2025): the link is a TikTok video. Europe
    Elects is a poll aggregator, not a polling firm. The fieldwork dates and
    n=1,000 match the Verifield poll of 14–18 Feb. Excluded: pollster identity
    not verifiable.
  - Outside the window (listed in the parliamentary pages but fieldwork before
    2023-12-02): Mercury Research (Oct–Nov 2023), LARICS (Sep 2023), Geeks for
    Democracy (May–Jun 2023), and Snap Market Research's Nov 2023 poll (the
    house qualifies through its Jan 2024 poll).
  - Houses with only European Parliament polls in 2024 per sondajeromania.ro:
    INSOMAR, Ipsos, CSPS. Not registered; they are not MVP elections.
- **2026-11-22: pollster IDs** follow DATA_MODEL §4.3: the slug of the public
  short name, without the legal form. The IDs are `atlasintel`, `inscop`,
  `curs`, `avangarde`, `sociopol`, `verifield`, `cira`, `bcs`, `ara`,
  `snap-market-research`, `flashdata`, `dataecho`, `irsop`, `mkor`, and
  `noi-cetatenii`.
- **2026-11-22: `typical_modes`** are taken from the pollster's own methodology
  statements where they exist; otherwise from media reports of their MVP-period
  polls, with the basis in `notes`. Special cases:
  - AtlasIntel = `cawi`. Its "random digital recruitment" leads to online
    questionnaires (CNN Brasil).
  - CURS = `capi;cati`. Its site describes face-to-face as PAPI/CAPI with CAPI
    since 2016; the Nov 2024 report says only "face-to-face". The Oct 2024
    report states CATI.
  - DataEcho and Noi, Cetățenii are left empty. They report "digital
    recruitment" without naming the interview channel.
- **2026-11-22: verified flag.**
  - `pollsters.csv`: `verified=true` only when name, website, and modes were
    all confirmed on the pollster's own pages or reports (INSCOP, CURS,
    Avangarde, MKOR). The other rows are `false`, and `notes` says which value
    rests on media or an index.
  - `pollster_aliases.csv`: `true` when I saw the variant myself at a
    pollster or media source. Wikipedia and aggregator rows are always `false`
    (R-14).
  - `pollster_affiliations.csv`: `true` only when the source is the pollster's
    own publication, or the counterpart's own publication of the commissioned
    poll (INSCOP reports, bcs.com.ro, HotNews, România TV, Antena 3 CNN,
    Newsweek România). Third-party media reports are `false`.
- **2026-11-22: aliases.** Every variant seen in the indexes, media, or own sites,
  except variants that differ **only by letter case** (Atlasintel, Flashdata,
  SOCIOPOL, Inscop). R-31 compares aliases case-insensitively, so those match
  the existing rows anyway. Client labels ("Newsweek", "USR", "PNL") are not
  aliases, because they would be ambiguous.
- **2026-11-22: affiliation leads not recorded** (unsourced, or the source is too weak):
  - The Avangarde website shows a report image whose *file name* contains
    "LA-COMANDA-PSD". The image itself shows only "Barometrul Opiniei Publice,
    Național, Octombrie 2021", with no client, and the linked Google Drive file
    is gone.
  - Cuget Liber commissioned the 21–25 Apr 2025 poll (its article and PDF),
    but neither names the pollster. Wikipedia attributes it to ARA.
  - Client links that appear only in sondajeromania.ro: AtlasIntel–Digi24
    (Apr 2024, EP poll), CIRA–Evenimentul Zilei (2024 presidential).
  - Verifield–Nicușor Dan for the 6 May 2025 poll: RO Wikipedia only. The
    HotNews-hosted PDF names no sponsor in its text layer. Recorded only in
    `notes` of the Mar 2025 row.
  - ARA's "American consulting company" partner is not named on arapo.ro.
  - No ownership or personnel record was found for most houses. No
    rumour-level or unsourced claim was added.
- **2026-11-22: gaps (fields left empty / not verified).**
  - Sociopol: no official website (sociopol.ro is dead; Web Archive snapshots
    end in 2015); legal name unknown.
  - Snap Market Research Plc: website and country of registration unknown.
  - DataEcho: results.dataecho.ro is unreachable (the Web Archive copy of the
    22–24 Apr PDF was used); website and legal name unknown.
  - Noi, Cetățenii: no website; the organisation is unidentified beyond its
    published Google Sheets.
  - Verifield: the live site shows only a title page; the legal form
    (Verifield SRL) comes from a 2023 Web Archive snapshot.
  - Legal forms and registration numbers were not verified for any house
    (not required by §6.3).
- **2026-11-22: manual validation** (T-003 not merged). A scratch script
  checked the three files against DATA_MODEL:
  - R-01: UTF-8 without BOM, LF, final newline, no line breaks in fields;
  - R-02: headers exactly as in §6.14;
  - R-03: slug/url/date/partial_date/bool types and the enums (`mode` list
    items, `source_type`, `relation`);
  - R-04: no duplicate keys;
  - R-06: alias/affiliation `pollster_id` FK → `pollsters.csv`;
    `counterpart_entity_id` is empty everywhere;
  - R-10, R-11 (`retrieved_at` ≤ 2026-11-22), R-14, R-30, R-31
    (case-insensitive alias uniqueness), and R-32;
  - no leading/trailing whitespace;
  - a scan of `notes`/`description` for the banned wording of ADR-0003.

  Result: OK. All Romanian diacritics use comma-below ș/ț (no cedilla
  characters). The header lines were not changed (append-only).
- **2026-11-22: notes for T-006** (rough counts of distinct polls in the
  indexes, merging EN/RO Wikipedia and sondajeromania.ro; "win" = inside the
  120-day window; not a scorecard):

  | pollster | parl-2024-cd (win) | pres-2025-r1 | pres-2025-r2 after r1 (+ pre-r1 Dan–Simion) | where originals are published |
  |---|---|---|---|---|
  | atlasintel | 1 (1) | 5 | 2 (+5) | PDFs on cdn.atlasintel.org (slide images exported from Google Slides; little or no text layer) + HotNews articles |
  | inscop | 5 (3) | 0 (exit/election-day only) | 0 | own site posts + text PDFs (wp-content), very regular |
  | curs | 3 (3) | 3 | 1 (+1) | own site posts with slide PNGs + text PDF presentations |
  | avangarde | 2 (0) | 2 | 0 (exit polls only) | media (Libertatea embeds PDF, HotNews, Antena 3); own site lists old reports on Google Drive |
  | sociopol | 0 | 12 | 1 (+2) | media only (România TV articles/broadcast, slide images); no own website |
  | verifield | 2 (1–2) | 2 | 1 | media (Digi24, Libertatea), client Facebook posts; one text PDF hosted by HotNews (6 May) |
  | cira | 2 (2) | 0 | 0 | media (Newsweek, B1TV with Google Drive report) |
  | bcs | 1 (1) | 0 | 0 | own site posts (bcs.com.ro, "Barometru politic național") + Newsweek; own site also lists 26–29 Sep and 7–10 Nov 2024 barometers not in the indexes |
  | ara | 1 (0) | 5 | 0 (+1; exit poll on 18 May) | media (Antena 3 CNN); one text PDF published by Cuget Liber (pollster not named in it) |
  | snap-market-research | 1 (0) | 0 | 0 | press release via Oficiul de Știri only |
  | flashdata | 0 | 4 | 0 (+2) | media (Agerpres, Spotmedia, ProTV-hosted PDF) |
  | dataecho | 0 | 2 | 0 | text PDFs on results.dataecho.ro (offline now; Web Archive copies) |
  | irsop | 0 | 1 | 1 | press releases via media (HotNews, images) |
  | mkor | 0 | 3 | 1 (+2) | own site HTML reports (mkor.ro/studii), methodology section |
  | noi-cetatenii | 0 | 3 | 1 (+3) | published Google Sheets (HTML/CSV export) |

  Houses with polls in all three MVP elections (pre-election, per the indexes):
  AtlasIntel, CURS, Verifield. Sociopol, MKOR, IRSOP and Noi, Cetățenii cover
  both presidential rounds but not `parl-2024-cd`. INSCOP covers only
  `parl-2024-cd` (plus 2025 exit polls). Parliamentary coverage is thin in all
  indexes. The Verifield August 2024 poll has no exact dates ("Aug 2024").
  Counts are approximate: the indexes disagree in places (e.g. ARA 15–19 Apr
  2025 appears only in EN Wikipedia; DataEcho's sample is 2,607 in EN and
  1,200 in RO/sondajeromania).

## Outcome
`data/registry/` now holds the pollster registry for the three MVP elections
(commit ff2e4bf):
- `pollsters.csv`: **15** pollsters (`atlasintel`, `inscop`, `curs`,
  `avangarde`, `sociopol`, `verifield`, `cira`, `bcs`, `ara`,
  `snap-market-research`, `flashdata`, `dataecho`, `irsop`, `mkor`,
  `noi-cetatenii`)
- `pollster_aliases.csv`: **38** name variants
- `pollster_affiliations.csv`: **19** sourced rows: 14 `client`, 3 `other`
  (2 INSCOP partnerships; Nicușor Dan publishing an AtlasIntel poll),
  1 `owner`, 1 `personnel`

Every row has a `source_url`. Manual validation passed (see Log).

Known limitations:
- `counterpart_entity_id` is empty pending T-004.
- Several websites and legal names are unverified (see Log, "gaps").
- Poll counts per house are approximate index counts, for T-006 only.
