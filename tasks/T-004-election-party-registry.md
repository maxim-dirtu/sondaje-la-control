---
id: T-004
title: Election, party and alliance registry (MVP elections)
status: done
phase: 0
depends_on: [T-001]
owner: agent-t004
branch: task/T-004-registry
methodology: [M-1.2, M-1.5]
created: 2026-11-22
updated: 2026-11-22
---

## Goal
Registry rows for the 3 MVP elections (`parl-2024-cd`, `pres-2025-r1`,
`pres-2025-r2`; see [ADR-0007](../docs/decisions/0007-mvp-scope.md)) and for
every party, candidate, and alliance that appears in their official results.

## Context
The registry gives the Phase 1 tasks a shared vocabulary of IDs. Linking each
presidential candidate to the parties that supported them lets a lean toward a
**party** be tracked across both parliamentary and presidential elections (I-002).

## Scope
**In:**
- The registry files defined by T-001: elections, entities, and the alliance
  mapping
- Per entity: official name, short name, type (party/alliance/candidate/
  independent), and a chart color (hex)
- The alliance mapping (electoral alliances in `parl-2024-cd`), so that poll
  labels map to result entities
- Candidate → supporting party/parties for both presidential rounds, each with
  a source
- **Candidates that polls included but who are not in the official results**
  (withdrawn, excluded, or never registered): an entity row plus an
  `entity_map` row each, so that the pollster tasks don't all append the same
  rows. Use the discovery indexes (Wikipedia, sondajeromania.ro) to find them.

**Out:**
- Results and polls (Phase 1). Pollsters (T-005).

## Acceptance criteria
- [x] All 3 MVP elections are present, with correct dates and round numbers.
- [x] Every party, candidate, and alliance in the official results is present,
      with a source (AEP/BEC).
- [x] Every alliance in these elections has a mapping.
- [x] `sondaje validate` passes. If T-003 is not merged yet, the files match
      DATA_MODEL.md by manual check, recorded in the Log.

## Follow-ups
- **Schema (DATA_MODEL §6.6), proposal:** add an `entity_map.relation` value
  for "ran on another party's list" (e.g. `ran_on_list_of`, with
  `result_entity_id` required). In `parl-2024-cd`, PMP members ran on the
  Forța Dreptei lists, and several polls show PMP separately or as "PMP+FD".
  The enum offers no value for this, so `pmp` is recorded as `not_registered`
  (literally true: it filed no lists). Under M-1.5 its poll share is then
  dropped, not added to `fd`. The same question applies to `pusl` and
  `pro-romania` if a source confirms their candidates ran on the PSD lists
  (not verified here). Coordinator/T-020 to decide.
- **Schema (DATA_MODEL §4.2), proposal:** one person can be a contestant in two
  roles (`independent` in a list election, `candidate` in a presidential one).
  `entity_type` is one value per ID, so John-Ion Banu-Muscel has two IDs:
  `john-banu-muscel` (parl-2024-cd) and `john-banu-muscel-2025`
  (pres-2025-r1). Consider documenting this case in §4.2.
- **DATA_MODEL §4.2, clarification:** state which given name a person ID uses.
  This task used the publicly used given name for presidential candidates
  (`crin-antonescu`, `lavinia-sandru`, `daniel-funeriu`) and the first given
  name on the ballot for list independents.
- **Pollster tasks (T-012+):** names that 2025 presidential polls may include
  but that are not in the Wikipedia index (e.g. Mircea Geoană, Ludovic Orban,
  Marcel Ciolacu in early-2025 polls) have no entity yet. Append an entity row
  and a `pres-2025-r1` `entity_map` row (`not_registered`, source BEC
  PV 479C) when a poll is ingested. The same applies to parl-2024-cd labels
  not anticipated here (e.g. "Alianța AER" PER+PV, BSR, UNPR, "PSD+PNL").
- **T-010:** the AEP JSON (`prezenta.roaep.ro/parlamentare01122024/data/json/sicpv/pv/pv_aggregated.json`)
  has slightly different national votes from the BEC final PVs (e.g. PSD
  2,030,023 vs 2,030,144 in RFCD_1); use the BEC final figures. Entity names
  and IDs for all 101 competitors are in `entities.csv`.
- **Candidate support, not recorded (not verified):** round-2 endorsements of
  Nicușor Dan by FD, PMP and REPER; support for Călin Georgescu by AUR/POT
  before his rejection; other minor-party endorsements listed by Wikipedia.

## Log
- 2026-11-22: Locked the task (branch `task/T-004-registry`, worktree
  `sondaje-wt/T-004`).
- 2026-11-22: **Sources used.**
  - Elections: BEC PVs. `parl-2024-cd`: national totalization PV for the
    Chamber of Deputies, no. 1 RFCD of 4.12.2024
    (https://parlamentare2024.bec.ro/wp-content/uploads/2024/12/RFCD_1.pdf).
    `pres-2025-r1`: PV RFT1; `pres-2025-r2`: PV RFT2 of 20.05.2025
    (https://prezidentiale2025.bec.ro/rezultate-turul1/ and `/rezultate-turul-ii/`).
  - parl-2024-cd competitors: RFCD_1 lists all 101 competitors (29 parties,
    1 political alliance, 19 national-minority organisations, 52 independent
    candidates). The PDF is scanned (no text layer); names were read from the
    rendered pages and cross-checked against the AEP JSON
    (`pv_aggregated.json`, scope CNTRY/CD/RO), which has the same 101 names.
    Threshold PV RF_1 confirmed the party list.
  - Alliance status: the BEC decision list for parl-2024 shows one alliance,
    "Alianța politică România Socialistă" (decision 82/D/28.09.2024). Its
    members (PSR, PSDM, PCR - XXI) come from AGERPRES (29.11.2024). AUR and
    ANC are political parties despite "Alianța" in their names (BEC refers to
    them as "partidul ...").
  - pres-2025: BEC candidates page and PV 479C of 20.03.2025 (final
    candidacies): all 30 filings, proposers, filing dates, rejections
    (Georgescu 18D, Iovanovici-Șoșoacă 34D) and Gavrilă's renunciation
    (19.03.2025). Ballot names from RFT1/RFT2. A.Ro membership and short name
    from Digi24 (22.02.2025, citing the alliance protocol).
  - Endorsements: AGERPRES, Digi24, Mediafax, Adevărul, Jurnalul,
    cursdeguvernare.ro (URL on each row).
  - Discovery indexes (not used as sources): English Wikipedia "2025 Romanian
    presidential election" (opinion polls section; the "Opinion polling for
    the 2025..." page redirects there), "Opinion polling for the 2024 Romanian
    parliamentary election", Romanian Wikipedia. sondajeromania.ro no longer
    shows the 2024/2025 polls on its front page, so it was not useful as an index.
- 2026-11-22: **Polled names not on the ballot** (from the Wikipedia poll
  tables): pres-2025-r1: Călin Georgescu and Diana Iovanovici-Șoșoacă
  (`excluded`), Anamaria Gavrilă (`withdrawn`), George Becali, Ilie Bolojan,
  Ana Birchall (`not_registered`, i.e. absent from the 30 filings in PV 479C).
  parl-2024-cd: ADU, PMP, PUSL, PRO România (`not_registered`, i.e. absent
  from the 101 competitors in RFCD_1). Nicolae Ciucă appears in the 2025 index
  only in the 2024-election comparison row and was not added. `pres-2025-r2`
  needs no `entity_map` rows: its polls can only be fielded after round 1
  (R-84), between the two remaining candidates.
- 2026-11-22: **Naming decisions.** `name` is the name as on the ballot/official
  results, converted from the BEC upper case to normal Romanian
  capitalisation, with comma-below ș/ț (AEP data partly uses cedilla forms).
  For persons, `name` is given names + family name in ballot form (e.g.
  "Nicușor-Daniel Dan"); `short_name` is the commonly used form. Where a name
  differs from the registered party name, the note says so (e.g. `plan`:
  ballot "Liga Acțiunii Naționale", registered "Partidul Liga Acțiunii
  Naționale"; AGERPRES, 29.11.2024, reports the parl-2024 lists of "Partidul
  Liga Acțiunii Naționale (PLAN)", so the two names refer to the same party).
- 2026-11-22: **ID decisions.** Acronyms only where an official document shows
  them: the BEC member lists in RFCD_1 (PSD, PNL, USR, AUR, UDMR, FD, PSDI,
  PNCR, PRA, RS, PSDU, REPER) and in RFT2 (SOS, POT, PUSL, PLAN, PNR), or the
  file names of the BEC supporters-list proofs (SENS, DREPT, PER, ADN, ANC).
  Otherwise the slug of the name (the 19 minority organisations, small
  parties such as `partidul-verde`, `partidul-national-taranesc-crestin-democrat`,
  and `patriotii-poporului-roman`, whose BEC file name says PPPR and Wikipedia
  says PPR). Exception: `roasit`, from "RO.AS.IT." in the organisation's
  official name. For non-ballot entities: `psr`, `psdm`, `pcr-xxi` (AGERPRES),
  `pmp` (cursdeguvernare.ro), `adu` (Digi24), `aro` (A.Ro, Digi24),
  `pro-romania` (slug). For a list independent, the ID uses the first given name
  (`ioan-sarmas`). Non-ASCII letters were transliterated (`janos-szucs` for
  János-Attila Szűcs).
- 2026-11-22: **Entity types.** National-minority organisations are
  `entity_type = party` (the schema has no separate type); noted per row.
  `rs`, `adu`, `aro` are `alliance`.
- 2026-11-22: **Colours.** Not analytical values. Taken from the English
  Wikipedia `Module:Political party` data (cited per row in `notes`), uppercased.
  For candidates: the colour of the nominating party/alliance. For Nicușor Dan
  (#BAE002) and Victor Ponta (#E02043): the inline colours of the Wikipedia
  2025 poll tables. No colour for national-minority organisations (Wikipedia
  only has a generic black), PSDI (Wikipedia reuses the PSD colour), small
  parties without a module entry, independents, and the persons not on a ballot
  without a party colour. 88 of 126 entities have no colour (R-33 warnings).
- 2026-11-22: **candidate_support decisions.** `nominated` = the party that
  proposed the candidacy, as recorded in PV 479C, with the filing date as
  `announced_date`. For Crin Antonescu the alliance `aro` filed; PSD, PNL and
  UDMR are also recorded as `nominated` (formed the alliance to support the
  candidacy, protocol 19.02.2025). Round 2 repeats AUR's nomination of George
  Simion (same candidacy). `announced_date` is empty where the source does not
  state the date of the decision.
- 2026-11-22: **`verified`.** `true` on every row: each row's values were
  checked against the cited source. The colours come from Wikipedia and are
  explained in `notes`; they are not covered by the source.
- 2026-11-22: **Manual validation** (T-003 not merged): a throwaway script (not
  committed) checked every file against DATA_MODEL.md: headers equal to §6.14;
  UTF-8 without BOM, LF, final newline, no whitespace or line breaks in fields;
  slug/date/url/hex patterns; enums (election_type, body, status, entity_type,
  relation, support_type, source_type); unique keys; R-14; R-20/R-21 on the
  election IDs; FKs between elections, entities, entity_map and
  candidate_support; R-40; R-42; R-43 against the known ballots; no cedilla
  diacritics; neutral wording. Result: no errors. All 101 parl-2024-cd
  competitors and all 11 + 2 presidential ballot names have entities, and none
  of them is a `poll_entity_id` in `entity_map` (R-41).
- 2026-11-22: **Left out.** No results/turnout (T-010), no pollsters (T-005),
  no polls. Senate competitors (e.g. Partidul Phralipe al Romilor, which ran
  for the Senate only) are out of scope. The 2024 presidential election
  (annulled) is not in the MVP.

## Outcome
Registry for the three MVP elections, on branch `task/T-004-registry`.

| File | Rows |
|---|---|
| `data/registry/elections.csv` | 3 |
| `data/registry/entities.csv` | 126: 54 party (29 parl-2024-cd parties, 19 minority organisations, 6 non-contestant parties), 3 alliance (`rs`, `adu`, `aro`), 52 independent, 17 candidate (11 on the 2025 ballot, 6 polled but not on it) |
| `data/elections/parl-2024-cd/entity_map.csv` | 7 (3 `alliance_member` → `rs`; 4 `not_registered`: `pmp`, `adu`, `pusl`, `pro-romania`) |
| `data/elections/pres-2025-r1/entity_map.csv` | 6 (2 `excluded`, 1 `withdrawn`, 3 `not_registered`) |
| `data/elections/pres-2025-r2/entity_map.csv` | 0 (header only; not needed) |
| `data/elections/pres-2025-r1/candidate_support.csv` | 16 (12 `nominated`, 4 `endorsed`) |
| `data/elections/pres-2025-r2/candidate_support.csv` | 5 (1 `nominated`, 4 `endorsed`) |

Key commits: `6aedae2` (elections), `b4a442d` (entities), `017a123`
(entity_map), `cd908dc` (candidate_support).

Known limitations: see Follow-ups. In short, the `pmp` (and possibly `pusl`/
`pro-romania`) relation needs a schema decision. Endorsements are limited to
verified ones. 88 entities have no colour. Validated by manual check only
(T-003 pending).
