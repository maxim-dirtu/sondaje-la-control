# Data Model and CSV Schemas

**Schema version:** 1.1 · **Owner:** T-001 (amended by T-007) · **Last updated:** 2026-11-22

This document is the contract for everything under `data/`. Collection tasks
(T-004, T-005, T-010, the pollster tasks T-012+) write files that follow it,
validation (T-003) enforces it mechanically, and the analysis (T-020+) reads
it. Storage format and rationale: [ADR-0004](decisions/0004-data-storage-csv-in-git.md).
MVP scope: [ADR-0007](decisions/0007-mvp-scope.md).

Contents:
1. [Principles](#1-principles)
2. [Directory layout and file ownership](#2-directory-layout-and-file-ownership)
3. [CSV format and column types](#3-csv-format-and-column-types)
4. [ID conventions](#4-id-conventions)
5. [Provenance and archive fields](#5-provenance-and-archive-fields)
6. [Tables](#6-tables)
7. [Integrity rules (for T-003)](#7-integrity-rules-for-t-003)
8. [Coverage of METHODOLOGY inputs](#8-coverage-of-methodology-inputs)
9. [Changing the schema](#9-changing-the-schema)
10. [Worked example (fictitious)](#10-worked-example-fictitious)

---

## 1. Principles

1. **Raw values, exactly as published.** Poll shares are stored as the
   publication prints them: the same options, the same number of decimals, the
   same base, even when they do not sum to 100. Data files are **never
   normalized, rounded, re-based, or corrected**. Normalization to valid votes
   (METHODOLOGY M-1.1), alliance mapping and withdrawals (M-1.5), and the
   comparison set (M-1.2) happen **in code** (T-020), never in data.
   The only allowed format change is mechanical: a decimal comma becomes a
   decimal point, and the `%` sign is dropped (`"31,5%"` → `31.5`).
2. **Full toplines.** Every option a poll publishes is a row: every party or
   candidate, "other", undecided, non-response, "would not vote", and so on,
   each tagged with an `option_type` (§6.12). Subtotal and total lines are not
   options and are not recorded.
3. **Empty means "not published / not known".** An empty cell is the only way
   to say that a value is unknown. Sentinels such as `NA`, `null`, `-`, `?`,
   or `0` for "unknown" are forbidden. **Never invent or estimate a value**
   (AGENTS.md §6); record the gap in the task Log instead.
4. **Provenance on every row.** Every data file carries the provenance block
   (§5.1). Wikipedia and aggregators are indexes, not sources: a row that was
   only taken from them is `verified = false`.
5. **One writer per file.** Files are split per pollster (polls) and per
   election (results, mappings) so that tasks run in parallel. The only files
   shared between tasks are the **append-only** files listed in §2.2.
6. **Neutral wording** ([ADR-0003](decisions/0003-neutral-language.md)) in
   every free-text field (`notes`, `description`) and in every identifier.
7. **Language.** Column names, enum values, IDs, and `notes` are English.
   Values copied from a source (`name`, `option_label`, `question_wording`,
   `title`, `alias`, `sponsor`) stay in the original language, with Romanian
   diacritics (ș, ț with comma below).

## 2. Directory layout and file ownership

### 2.1 Layout

```
data/
├── README.md                          short guide; points here
├── registry/                          shared registries (append-only)
│   ├── elections.csv                  §6.1  one row per election (round)
│   ├── entities.csv                   §6.2  parties, alliances, candidates, independents
│   ├── pollsters.csv                  §6.3  one row per polling firm
│   ├── pollster_aliases.csv           §6.4  name variants seen in media
│   └── pollster_affiliations.csv      §6.5  sourced clients/ownership/personnel links
├── elections/
│   └── <election_id>/                 e.g. parl-2024-cd/
│       ├── entity_map.csv             §6.6  poll entity → ballot contestant (alliances, withdrawals)
│       ├── candidate_support.csv      §6.7  presidential only: candidate → supporting parties
│       ├── results.csv                §6.8  votes per contestant × scope
│       ├── results_totals.csv         §6.9  valid/invalid votes, voters, per scope
│       └── archive_manifest.csv       §6.10 official source files (URLs + SHA-256)
├── polls/
│   └── <pollster_id>/                 one directory per pollster
│       ├── polls.csv                  §6.11 one row per poll (metadata)
│       ├── poll_results.csv           §6.12 one row per poll × option × base (full topline)
│       ├── archive_manifest.csv       §6.10 archived original reports
│       └── inventory.csv              §6.13 RESERVED: defined by T-011
└── raw/                               git-ignored local copies of source files
    ├── elections/<election_id>/...
    └── polls/<pollster_id>/<document_id>.<ext>
```

`data/raw/` is git-ignored. Files there can be re-downloaded from the URLs in
the committed `archive_manifest.csv` files and checked against their SHA-256.

The directories for the three MVP elections exist with header-only CSV files.
Pollster directories are created by the pollster tasks (after T-006), with the
header lines copied from §6.14. `data/polls/.gitkeep` keeps the empty
`polls/` directory in git until then.

A header-only file (header line, no rows) is valid and means "no data yet".
A file that a directory does not need may be absent, except that every
`data/polls/<pollster_id>/` directory has all of `polls.csv`,
`poll_results.csv`, and `archive_manifest.csv` (R-05).

### 2.2 Who writes what

| File | Primary writer | Others | Mode |
|---|---|---|---|
| `registry/elections.csv` | T-004 (MVP), T-061 (backfill) | none | append-only |
| `registry/entities.csv` | T-004 | T-010, pollster tasks | append-only |
| `registry/pollsters.csv` | T-005 | pollster tasks | append-only |
| `registry/pollster_aliases.csv` | T-005 | pollster tasks | append-only |
| `registry/pollster_affiliations.csv` | T-005 | pollster tasks | append-only |
| `elections/<id>/entity_map.csv` | T-004 | pollster tasks (e.g. a polled candidate who never registered) | append-only |
| `elections/<id>/candidate_support.csv` | T-004 | none | owned |
| `elections/<id>/results.csv`, `results_totals.csv`, `archive_manifest.csv` | T-010 (generated by `sondaje ingest-results`) | none | owned, regenerated |
| `polls/<pollster_id>/*` | the task for that pollster | none | owned |

**Append-only** means:
- New rows are added **at the end** of the file.
- Existing rows are never deleted or reordered, and an ID is never changed or
  reused.
- A non-ID field of an existing row may be corrected only by the file's
  primary writer or by a correction task assigned by the coordinator. The
  correction is logged in that task's Log.
- Before appending, rebase on `main` and check that the ID does not exist yet.
  When two branches append to the same file, git reports a conflict at the end
  of the file. The coordinator resolves it by keeping both blocks (and fixing
  a duplicate ID if one appears).

**Owned** files have exactly one writer task at a time, so no other task
touches them.

With this split, the Phase 1 tasks run in parallel: T-010 writes only result
files, each pollster task writes only its own `polls/<pollster_id>/`
directory, and both only append to the registries (pollster tasks also to
`entity_map.csv`).

## 3. CSV format and column types

### 3.1 File format

- Encoding **UTF-8 without BOM**; line endings **LF** (`.gitattributes`
  enforces LF for `*.csv`). The file ends with a newline.
- Delimiter `,`; quote character `"`; a field is quoted only when it contains
  a comma or a quote, and an inner quote is doubled (RFC 4180).
- **No line breaks inside a field.** Multi-line text is joined with a single
  space.
- The first line is the header. It lists **exactly** the columns of §6, **in
  the order given there**. Extra, missing, or reordered columns are errors.
- No leading or trailing whitespace in any field.
- Recommended row order (keeps diffs small; not validated): registries in
  append order; `polls.csv` by `fieldwork_end`, then `poll_id`;
  `poll_results.csv` by `poll_id`, `share_base`, `option_order`;
  `results.csv` by `scope`, then `votes` descending.

### 3.2 Column types

| Type | Format | Validation pattern / rule |
|---|---|---|
| `slug` | lowercase ASCII letters and digits, groups joined by single hyphens, ≤ 64 characters | `^[a-z0-9]+(-[a-z0-9]+)*$` |
| `date` | ISO 8601 calendar date | `^\d{4}-\d{2}-\d{2}$` and a real calendar date |
| `partial_date` | year, year-month, or full date, when only part is known | `^\d{4}(-\d{2}(-\d{2})?)?$`, valid parts |
| `int` | non-negative integer, no thousands separators | `^(0\|[1-9][0-9]*)$` |
| `decimal` | non-negative decimal number, `.` as separator; trailing zeros kept as published (`30.0` ≠ `30` in precision) | `^(0\|[1-9][0-9]*)(\.[0-9]+)?$` |
| `bool` | lowercase | `true` or `false` |
| `enum` | one of the values listed for the column, exact case | listed per column |
| `url` | absolute URL | `^https?://\S+$` |
| `sha256` | lowercase hex digest | `^[0-9a-f]{64}$` |
| `hex_color` | uppercase RGB hex | `^#[0-9A-F]{6}$` |
| `path` | repository-relative path with `/` separators | must start with `data/raw/` |
| `text` | any UTF-8 text without line breaks | no leading/trailing whitespace |
| `list<enum>` | enum values separated by `;`, no spaces, no duplicates | each item valid |

### 3.3 Required flags

In the column tables, **Req** is:
- `yes`: never empty;
- `no`: may be empty (empty = not published / not known);
- `cond`: required or forbidden depending on another column; the rule is
  given in the description and in §7.

## 4. ID conventions

IDs are `slug`s. They are **stable**: once a row with an ID is on `main`, the
ID never changes and is never reused, even if the name of the thing changes.
Romanian diacritics are transliterated: ă→a, â→a, î→i, ș/ş→s, ț/ţ→t.

### 4.1 Elections: `election_id`

Grammar: `<type>-<year>[-<body>][-<tag>][-r<round>]`

| Part | Values | Meaning |
|---|---|---|
| `type` | `parl` parliamentary · `pres` presidential · `ep` European Parliament · `local` local | `election_type` |
| `year` | 4 digits | year of `election_date` |
| `body` | `cd` Chamber of Deputies · `sen` Senate (parliamentary only; omitted where the type has one body) | `body` |
| `tag` | a slug, only to disambiguate two elections that would otherwise get the same ID; agreed with the coordinator | none (free) |
| `round` | `r1`, `r2`, … only for elections that can have several rounds | `round` |

Examples: `parl-2024-cd`, `pres-2025-r1`, `pres-2025-r2` (MVP); `ep-2024`,
`pres-2024-r1`, `parl-2024-sen` (future). Each round is a separate election
(M-1.5). If two elections would get the same ID (e.g. a repeated election in
the same year), the later one gets a `tag` (e.g. `pres-2030-rerun-r1`). Local elections (T-062) extend the
grammar with a locality part through a schema change (§9).

### 4.2 Entities: `entity_id`

One entity is one contestant identity: a party, an alliance, a presidential
candidate, or an independent candidate in a list election.

- **Party or alliance:** the lowercase acronym as used on the ballot
  (e.g. fictitious `pex` for "Partidul Exemplu"). If there is no acronym, the
  slug of the short name.
- **Person (candidate, independent):** `<given-name>-<family-name>`,
  transliterated, e.g. fictitious `ion-exemplu`.
  - `<given-name>` is **one** given name: the one the person is publicly known
    by (the everyday name, as in `short_name`), e.g. `crin-antonescu` for the
    ballot name "George-Crin-Laurențiu Antonescu". If no everyday form can be
    established from sources (typical for list independents), it is the
    **first** given name on the ballot (`ioan-sarmas` for "Ioan-Sabin Sărmaș").
  - `<family-name>` is the **full** family name as on the ballot, every part
    kept and joined by hyphens (`diana-iovanovici-sosoaca`,
    `erich-mocanu-gollent`), even if the person is publicly known by one part.
  - Further given names only if needed to disambiguate.
- **Collision:** if the slug already exists for a different contestant (e.g. an
  acronym reused by a different legal party), append the year in which the new
  one first appears: `pex-2028`.
- **One person, two roles.** `entity_type` is one value per ID, so a person
  who is a contestant in two roles (e.g. an `independent` in a list election
  and a `candidate` in a presidential one) has **two** IDs. The role registered
  first keeps the plain slug; the second is a collision and gets the year of
  the election in which that role first appears, e.g. `john-banu-muscel`
  (independent, `parl-2024-cd`) and `john-banu-muscel-2025` (candidate,
  `pres-2025-r1`). The same ID is reused for the same role in later elections.
  The `notes` of the second row name the other ID. The registry has no
  machine-readable link between the two IDs.
- A renamed party keeps its ID; the rename goes in `notes`.

### 4.3 Pollsters: `pollster_id`

The slug of the short name the firm uses publicly, without the legal form
(SRL, SA), e.g. fictitious `exemplar` for "Institutul Exemplar de Sondare
SRL". The poll directory is `data/polls/<pollster_id>/`.

### 4.4 Polls: `poll_id`

`<pollster_id>-<election_id>-<YYYYMMDD>[-<suffix>]`

- `YYYYMMDD` is `fieldwork_end`; if the fieldwork end was not published, it is
  `published_date`.
- `<suffix>` (a slug) is added only when the ID would otherwise collide: a
  second scenario from the same survey (e.g. `-scenario-b`), or a second
  survey with the same date (`-2`).

Example: `exemplar-parl-2024-cd-20241124`, `exemplar-pres-2025-r1-20250427-scenario-b`.

### 4.5 Source documents: `document_id`

`<directory_id>-doc-<NNN>`: `<directory_id>` is the `pollster_id` or the
`election_id` of the directory that holds the `archive_manifest.csv`; `NNN`
is a zero-padded sequence number (3 digits or more), assigned in append order.
Example: `exemplar-doc-001`, `parl-2024-cd-doc-001`.

## 5. Provenance and archive fields

### 5.1 Provenance block

Every data file ends with these columns, in this order (the archive manifest
omits `verified`, see §6.10):

| Column | Type | Req | Allowed values / format | Example | Description |
|---|---|---|---|---|---|
| `source_url` | url | yes | absolute http(s) URL | `https://example.org/sondaj.pdf` | Where the values in this row were taken from (the page or file, not a home page). |
| `source_type` | enum | yes | `official` · `pollster` · `media` · `wikipedia` · `aggregator` · `other` | `pollster` | Kind of source: `official` = electoral authority (AEP, BEC, Official Gazette); `pollster` = the pollster's own publication; `media` = a media outlet; `wikipedia` = Wikipedia; `aggregator` = a poll aggregator such as sondajeromania.ro; `other` = anything else (e.g. a party website), explained in `notes`. |
| `retrieved_at` | date | yes | `YYYY-MM-DD` | `2026-11-22` | Date the source was accessed. |
| `verified` | bool | yes | `true` · `false` | `true` | `true` if every value in the row was checked against the **original** publication (the pollster's own report, or the official results). Never `true` when `source_type` is `wikipedia` or `aggregator` (R-14). Readings per registry table: §5.3. |
| `notes` | text | no | English free text | `Fieldwork dates from the PDF footnote.` | Anything a reader needs to interpret the row. |

### 5.2 Archive fields

The original of every poll report (and of every official results file) is
listed in an `archive_manifest.csv` (§6.10) with:

- `archive_url`: a public snapshot of the original (Web Archive, or another
  archive service), so the source stays checkable if the original disappears;
- `sha256`: the SHA-256 of the exact bytes downloaded to `data/raw/`;
- `format`: the document format (text PDF, scanned PDF, HTML, …).

Each poll records **how** its values were extracted, in
`polls.extraction_method`: `pdf_text` (from the text layer of a PDF),
`html` (from an HTML table or text), or `manual_double_entry` (two
independent manual transcriptions, compared by the T-011 diff tool; used for
images, scans, and articles).

### 5.3 What `verified` means in the pollster registries

For the pollster registries, "the original publication" of §5.1 reads as
follows. In every case, a row whose only source is Wikipedia or an aggregator
is `false` (R-14).

| File | `verified = true` when |
|---|---|
| `pollsters.csv` | `name`, `website`, and `typical_modes` were all confirmed on the pollster's own pages or reports. If any of them rests on media or an index, the row is `false` and `notes` says which value. |
| `pollster_aliases.csv` | The contributor saw the variant, exactly as written in `alias`, in the cited source (the pollster's own publication or a media publication), and that source clearly refers to this pollster. |
| `pollster_affiliations.csv` | The cited source is a **party to the relation**: the pollster's own publication, or the counterpart's own publication (e.g. the commissioning outlet's article on its own poll, a party's or candidate's own post), or an official record (e.g. the trade register, the Official Gazette). A third-party report (media describing a relation between two other parties) is `false`, even when `description` matches it exactly. |

## 6. Tables

### 6.1 `registry/elections.csv`

One row per election; each round is a separate election.
Key: `election_id`.

| Column | Type | Req | Allowed values / format | Example | Description |
|---|---|---|---|---|---|
| `election_id` | slug | yes | §4.1 grammar | `pres-2025-r1` | Stable election ID. |
| `election_type` | enum | yes | `parliamentary` · `presidential` · `european` · `local` | `presidential` | Must match the ID prefix (R-20). |
| `body` | enum | yes | `chamber_of_deputies` · `senate` · `president` · `european_parliament` | `president` | The body elected. Must match the ID (R-20). |
| `round` | int | yes | ≥ 1 | `1` | Round number; `1` for single-round elections. |
| `election_date` | date | yes | `YYYY-MM-DD` | `2025-05-04` | Election day. |
| `name` | text | yes | English | `Presidential election 2025, round 1` | Human-readable name. |
| `status` | enum | yes | `held` · `annulled` · `scheduled` | `held` | `annulled`: the result was annulled by a competent authority; details in `notes`. |
| provenance block | | | §5.1 | | Source of the date and status (`official` preferred). |

### 6.2 `registry/entities.csv`

Parties, alliances, presidential candidates, and independent candidates.
Key: `entity_id`.

| Column | Type | Req | Allowed values / format | Example | Description |
|---|---|---|---|---|---|
| `entity_id` | slug | yes | §4.2 | `pex` | Stable entity ID. |
| `entity_type` | enum | yes | `party` · `alliance` · `candidate` · `independent` | `party` | `candidate` = a person running in a single-winner election (presidential); `independent` = an independent candidate in a list election (parliamentary, European). |
| `name` | text | yes | original language | `Partidul Exemplu` | Official full name (for persons: full name as on the ballot). |
| `short_name` | text | yes | original language | `PEX` | Name used in charts and tables. |
| `color` | hex_color | no | `#RRGGBB` | `#1F77B4` | Chart color. Empty = the UI uses a neutral default. |
| provenance block | | | §5.1 | | Source for the name (`official` preferred). |

Alliance membership is election-specific, so it lives in `entity_map.csv`
(§6.6), not here.

### 6.3 `registry/pollsters.csv`

One row per polling firm. Key: `pollster_id`.

| Column | Type | Req | Allowed values / format | Example | Description |
|---|---|---|---|---|---|
| `pollster_id` | slug | yes | §4.3 | `exemplar` | Stable pollster ID. |
| `name` | text | yes | original language | `Institutul Exemplar de Sondare` | Official name (legal form may be omitted). |
| `short_name` | text | yes | original language | `Exemplar` | Name used in charts and tables. |
| `website` | url | no | absolute http(s) URL | `https://example.org` | Official website. |
| `typical_modes` | list<enum> | no | items from the `mode` enum (§6.11) | `cati;cawi` | Survey modes the firm usually reports. |
| provenance block | | | §5.1 | | Source for the name and website. |

### 6.4 `registry/pollster_aliases.csv`

Name variants seen in media and indexes, so that every task maps them to the
same `pollster_id`. Key: (`pollster_id`, `alias`).

| Column | Type | Req | Allowed values / format | Example | Description |
|---|---|---|---|---|---|
| `pollster_id` | slug | yes | FK → `pollsters.pollster_id` | `exemplar` | |
| `alias` | text | yes | exactly as seen | `Institutul Exemplar` | A name variant. Unique across all pollsters (R-31). |
| provenance block | | | §5.1 | | Where the variant was seen. |

### 6.5 `registry/pollster_affiliations.csv`

Sourced, factual links between a pollster and another organisation or person:
clients, ownership, personnel. Feeds M-5.1d. Unsourced claims are not recorded.
Wording is factual and neutral (ADR-0003). Key: (`pollster_id`, `relation`,
`counterpart_name`, `period_start`).

| Column | Type | Req | Allowed values / format | Example | Description |
|---|---|---|---|---|---|
| `pollster_id` | slug | yes | FK → `pollsters.pollster_id` | `exemplar` | |
| `relation` | enum | yes | `client` · `owner` · `personnel` · `other` | `client` | `client`: commissioned polls from the firm; `owner`: holds an ownership stake; `personnel`: a person in the firm's management or staff holds or held a role with the counterpart; `other`: explained in `description`. |
| `counterpart_name` | text | yes | original language | `Partidul Exemplu` | The organisation or person on the other side. |
| `counterpart_entity_id` | slug | no | FK → `entities.entity_id` | `pex` | Set whenever the counterpart is a registered entity (R-35 warns when a matching entity exists but the cell is empty). When the counterpart becomes an entity later, the cell is filled in as a correction (§2.2). |
| `period_start` | partial_date | no | `YYYY[-MM[-DD]]` | `2024-03` | Start of the relation, if known. |
| `period_end` | partial_date | no | `YYYY[-MM[-DD]]` | `2025-12` | End of the relation; empty = ongoing or unknown. |
| `description` | text | yes | English, factual | `Commissioned 2 polls published in March 2024.` | What the source states, nothing more. |
| provenance block | | | §5.1 | | `source_url` is mandatory, as everywhere. |

### 6.6 `elections/<election_id>/entity_map.csv`

Maps an entity that appears in polls to the contestant that appears in the
official results of this election (M-1.5). An entity needs a row here only if
it is polled but is **not itself a contestant** in `results.csv` (R-41).
Key: (`election_id`, `poll_entity_id`).

| Column | Type | Req | Allowed values / format | Example | Description |
|---|---|---|---|---|---|
| `election_id` | slug | yes | FK → `elections`; equals the directory name | `parl-2024-cd` | |
| `poll_entity_id` | slug | yes | FK → `entities.entity_id` | `pex` | The entity as polled. |
| `relation` | enum | yes | `alliance_member` · `merged_into` · `ran_on_list_of` · `withdrawn` · `excluded` · `not_registered` | `alliance_member` | `alliance_member`: the polled party ran as part of the alliance `result_entity_id`; its poll share is added to the alliance. `merged_into`: the polled entity was absorbed into `result_entity_id` before the vote. `ran_on_list_of`: the polled party filed no lists of its own, and its candidates ran on the lists of the party or alliance `result_entity_id` (the *host*) under a party-level arrangement; its poll share is added to the host's share (see below). `withdrawn`: the contestant withdrew. `excluded`: the candidacy was rejected or annulled by the electoral authorities. `not_registered`: polled but never filed a candidacy/list. For the last three, the poll share is dropped and the rest renormalized (M-1.5). |
| `result_entity_id` | slug | cond | FK → `entities.entity_id` | `ax` | Required for `alliance_member`, `merged_into`, and `ran_on_list_of`; must be empty otherwise (R-40). For `alliance_member` it must be an entity of type `alliance`; for `ran_on_list_of`, of type `party` or `alliance` (R-45). It is always a ballot contestant, never itself a `poll_entity_id` of the same file (R-41, R-46). |
| `effective_date` | date | no | `YYYY-MM-DD` | `2024-10-20` | When the alliance, merger, withdrawal, or exclusion took effect, or (for `ran_on_list_of`) when the arrangement was announced, if known. |
| provenance block | | | §5.1 | | Source of the relation (`official` or `media`). |

**`ran_on_list_of` in detail.** The relation covers a *guest* party
(`poll_entity_id`) that is not on the ballot because it placed its candidates
on the lists of a *host* contestant (`result_entity_id`), for example when
there was no time to register an electoral alliance. It differs from
`alliance_member` in that the host is a single party (or alliance) that keeps
its own name on the ballot, and from `merged_into` in that the guest party
continues to exist.
- **Evidence.** A source must show a **party-level** arrangement: the guest
  party (its leadership or a statutory body) states that its candidates run
  on the host's lists, or the host and guest file the lists together. A few
  members of a party who join another party, or run on its lists as
  individuals, do not make the party a guest; it stays `not_registered`, and
  the source goes in `notes`.
- **Semantics (M-1.5).** In a poll for this election, the guest's share is
  added to the host's share, exactly as for `alliance_member`; it is not
  dropped. Validation: the host has type `party` or `alliance`, the guest has
  type `party` or `alliance`, the election is a list election
  (`parliamentary` or `european`) (R-45); the host is a contestant in
  `results.csv` (R-41) and is not itself mapped in the same file (R-46).
- **Combined poll labels.** A poll option that names the host and the guest
  together (e.g. "Partidul Delta + Partidul Eta") keeps its published
  `option_label` and gets the **host's** `entity_id`: the option is the host's
  list. A note on the `poll_results` row is recommended.

Poll **labels** are resolved per row in `poll_results.csv`: `option_label`
keeps the published text and `entity_id` holds the registry entity it refers
to. The same label must resolve to the same entity within one
(pollster, election) (R-62).

### 6.7 `elections/<election_id>/candidate_support.csv`

Presidential elections only. Links each candidate to the parties or alliances
that nominated or endorsed them (I-016), so that a lean toward a party can be
followed across election types. With several supporting parties, M-1.5
attributes the error to the candidate only. Key: (`election_id`,
`candidate_entity_id`, `party_entity_id`, `support_type`).

| Column | Type | Req | Allowed values / format | Example | Description |
|---|---|---|---|---|---|
| `election_id` | slug | yes | FK → `elections` with `election_type = presidential`; equals the directory name | `pres-2025-r1` | |
| `candidate_entity_id` | slug | yes | FK → `entities`, type `candidate` | `ion-exemplu` | |
| `party_entity_id` | slug | yes | FK → `entities`, type `party` or `alliance` | `pex` | |
| `support_type` | enum | yes | `nominated` · `endorsed` | `nominated` | `nominated`: the party formally proposed the candidate (candidacy filing); `endorsed`: the party publicly declared support without nominating. |
| `announced_date` | date | no | `YYYY-MM-DD` | `2025-02-15` | Date of the nomination or endorsement, if known. |
| provenance block | | | §5.1 | | |

### 6.8 `elections/<election_id>/results.csv`

Official votes per contestant and scope. Shares are **not stored**; they are
derived as `votes / valid_votes` of the same scope (§6.9). For
`parl-2024-cd` this is the Chamber of Deputies list vote.
Key: (`election_id`, `scope`, `entity_id`).

| Column | Type | Req | Allowed values / format | Example | Description |
|---|---|---|---|---|---|
| `election_id` | slug | yes | FK → `elections`; equals the directory name | `parl-2024-cd` | |
| `scope` | enum | yes | `domestic` · `diaspora` · `total` | `domestic` | `domestic`: polling stations in Romania; `diaspora`: polling stations abroad (and postal votes); `total` = domestic + diaspora (M-1.4). |
| `entity_id` | slug | yes | FK → `entities` | `pex` | A contestant on the ballot. Entity type must fit the election type (R-52). |
| `votes` | int | yes | ≥ 0 | `1234567` | Valid votes for the contestant in this scope. |
| provenance block | | | §5.1 | | `source_type = official` expected. |

### 6.9 `elections/<election_id>/results_totals.csv`

Totals per scope. Key: (`election_id`, `scope`).

| Column | Type | Req | Allowed values / format | Example | Description |
|---|---|---|---|---|---|
| `election_id` | slug | yes | FK → `elections`; equals the directory name | `parl-2024-cd` | |
| `scope` | enum | yes | `domestic` · `diaspora` · `total` | `total` | As in §6.8. |
| `registered_voters` | int | no | ≥ 0 | `18000000` | Voters on the permanent lists, if published for this scope. |
| `voters` | int | no | ≥ 0 | `9000000` | Voters who turned up (signed the lists). |
| `valid_votes` | int | yes | ≥ 0 | `8700000` | Valid votes; the denominator for result shares. |
| `invalid_votes` | int | no | ≥ 0 | `250000` | Invalid (null) votes. |
| provenance block | | | §5.1 | | |

### 6.10 `archive_manifest.csv` (polls and elections)

One row per downloaded source document. The same schema is used in
`data/polls/<pollster_id>/` (poll reports) and in
`data/elections/<election_id>/` (official result files). The provenance block
here has **no `verified` column**, because the row describes the source
itself. Key: `document_id`.

| Column | Type | Req | Allowed values / format | Example | Description |
|---|---|---|---|---|---|
| `document_id` | slug | yes | §4.5 | `exemplar-doc-001` | |
| `title` | text | no | original language | `Barometru politic, noiembrie 2024` | Title as published. |
| `published_date` | date | no | `YYYY-MM-DD` | `2024-11-26` | Publication date of the document, if known. |
| `format` | enum | yes | `pdf_text` · `pdf_image` · `html` · `image` · `csv` · `xlsx` · `json` · `zip` · `other` | `pdf_text` | `pdf_text`: PDF with a text layer; `pdf_image`: scanned or image-only PDF. |
| `archive_url` | url | cond | absolute http(s) URL of an archive snapshot | `https://web.archive.org/web/20241126000000/https://example.org/r.pdf` | Snapshot of the original. **Required** in poll manifests (`data/polls/`); optional in election manifests (R-71). |
| `sha256` | sha256 | yes | 64 lowercase hex | `e3b0c442…b855` | SHA-256 of the downloaded bytes. |
| `raw_path` | path | no | `data/raw/...` | `data/raw/polls/exemplar/exemplar-doc-001.pdf` | Local (git-ignored) copy. |
| `source_url` | url | yes | absolute http(s) URL | `https://example.org/r.pdf` | The original URL that was downloaded. |
| `source_type` | enum | yes | §5.1 | `pollster` | |
| `retrieved_at` | date | yes | `YYYY-MM-DD` | `2026-11-22` | Download date (the hash refers to this download). |
| `notes` | text | no | English free text | `Second copy of the report, hosted by a media partner.` | As in §5.1. |

### 6.11 `polls/<pollster_id>/polls.csv`

One row per **poll**: one voting-intention question (one scenario) for one
election, from one survey. A survey that asks two questions for the same
election (e.g. two candidate lists) produces two polls, exactly one of which
is the `headline` poll. Questions for elections that are not in the registry
are not recorded. Exit polls (fieldwork on election day) are out of scope.
Key: `poll_id`.

| Column | Type | Req | Allowed values / format | Example | Description |
|---|---|---|---|---|---|
| `poll_id` | slug | yes | §4.4 | `exemplar-parl-2024-cd-20241124` | |
| `pollster_id` | slug | yes | FK → `pollsters`; equals the directory name | `exemplar` | The firm that conducted the fieldwork. |
| `election_id` | slug | yes | FK → `elections` | `parl-2024-cd` | The election the question is about. |
| `headline` | bool | yes | `true` · `false` | `true` | `true` for the poll the pollster presents as its main result; exactly one per survey (R-63). |
| `scenario` | text | cond | English | `Candidate list without X` | Describes the question variant. Required when `headline = false`. |
| `fieldwork_start` | date | no | `YYYY-MM-DD` | `2024-11-18` | First day of fieldwork, as published. |
| `fieldwork_end` | date | no | `YYYY-MM-DD` | `2024-11-24` | Last day of fieldwork, as published. Used for M-1.3 windows. |
| `published_date` | date | yes | `YYYY-MM-DD` | `2024-11-26` | First publication date of the results. |
| `sample_size` | int | no | ≥ 1 | `1100` | Total respondents (`n`), as published. |
| `sample_size_expressed` | int | no | ≥ 1, ≤ `sample_size` | `792` | Respondents in the `expressed_option` base, if published. |
| `mode` | enum | no | `cati` · `cawi` · `capi` · `papi` · `face_to_face` · `mixed` · `other` | `cati` | Data collection mode (the interview channel), as published. `face_to_face`: in-person interviews when the publication does not say whether CAPI or PAPI was used. `mixed`/`other`: details in `notes`. Conventions below the table. |
| `population` | enum | no | `adults` · `likely_voters` · `other` | `adults` | Sampled population: all adults with the right to vote, or respondents filtered as likely to vote. |
| `population_geo` | enum | no | `residents` · `residents_and_diaspora` · `diaspora` | `residents` | Geographic coverage, as published. Empty if not stated. |
| `target_scope` | enum | yes | `domestic` · `total` · `diaspora` | `domestic` | Result scope the poll is compared to (M-1.4): `domestic` unless the poll explicitly covers the diaspora. Must agree with `population_geo` (R-64). |
| `question_type` | enum | no | `prompted_list` · `open` · `other` | `prompted_list` | Whether options were read/shown (`prompted_list`) or not (`open`). |
| `question_wording` | text | no | original language, verbatim | `Dacă duminica viitoare …` | Exact wording, if published. |
| `sponsor` | text | cond | original language | `Televiziunea Exemplu` | Client/sponsor as published. Required unless `sponsor_type` is `self` or `not_disclosed`; must be empty for `not_disclosed` (R-65). |
| `sponsor_type` | enum | yes | `self` · `media` · `party` · `candidate` · `public_institution` · `civil_society` · `business` · `other` · `not_disclosed` | `media` | `self`: the publication states the pollster funded it; `not_disclosed`: no client/sponsor information published. |
| `weighting_published` | bool | yes | `true` · `false` | `true` | The publication describes the weighting. |
| `moe_published` | bool | yes | `true` · `false` | `true` | The publication states a margin of error. |
| `margin_of_error` | decimal | no | pp, as published | `3` | Margin of error in percentage points (e.g. `±3%` → `3`). Allowed only if `moe_published = true` (R-66). |
| `topline_coverage` | enum | yes | `full` · `partial` | `full` | `full`: every option the publication shows was captured **and** the publication shows a complete topline (all options, incl. undecided/non-response where asked). `partial`: the source shows only some options (e.g. an article listing the leading parties). |
| `document_id` | slug | yes | FK → `archive_manifest.document_id` in the same directory | `exemplar-doc-001` | The archived document the values were extracted from. |
| `extraction_method` | enum | yes | `pdf_text` · `html` · `manual_double_entry` | `pdf_text` | §5.2. Must fit the document format (R-67). |
| provenance block | | | §5.1 | | `source_url` equals the document's `source_url` (R-68). |

M-5.3 transparency items are read from these columns: sample size
(`sample_size` not empty), fieldwork dates (`fieldwork_start` and
`fieldwork_end` not empty), mode (`mode` not empty), exact question wording
(`question_wording` not empty), weighting (`weighting_published`), margin of
error (`moe_published`), client/sponsor (`sponsor_type ≠ not_disclosed`).
They describe what the **source used** published. If the media article lacks
an item that the pollster's own report has, use the pollster's report.

`mode` conventions:
- `mode` records how the **answers were collected** (the interview channel),
  not how respondents were recruited.
- Face-to-face without CAPI/PAPI detail ("față în față", "la domiciliul
  respondentului"): `face_to_face`. Use `capi` or `papi` only when that
  publication (or the pollster's report for that poll) says so; the pollster's
  usual practice is not enough.
- Recruitment-only descriptions, such as "random digital recruitment" (RDR):
  if the publication also says the questionnaire was completed online, the
  mode is `cawi`; if it names no interview channel, the mode is `other`, and
  `notes` quotes the published description. Either way the mode counts as
  published for M-5.3, because the publication describes the collection.
- Several channels in one poll (e.g. CATI plus CAWI): `mixed`, with the
  channels and, if published, their shares in `notes`.
- The same conventions apply to the items of `pollsters.typical_modes`.

### 6.12 `polls/<pollster_id>/poll_results.csv`

The full topline: one row per poll × published option × base.
Key: (`poll_id`, `share_base`, `option_order`).

| Column | Type | Req | Allowed values / format | Example | Description |
|---|---|---|---|---|---|
| `poll_id` | slug | yes | FK → `polls.poll_id` in the same directory | `exemplar-parl-2024-cd-20241124` | |
| `share_base` | enum | yes | `all_respondents` · `expressed_option` · `likely_voters` · `other_subset` | `all_respondents` | Who the percentage is computed over: all respondents; only those who named a party/candidate; only respondents who say they will vote; or another subset (explained in `notes`, R-69). Many reports publish two bases; each gets its own rows. |
| `option_order` | int | yes | 1, 2, … within (`poll_id`, `share_base`) | `1` | Position in the published table. Contiguous from 1 (R-60). |
| `option_label` | text | yes | original language, verbatim | `Partidul Exemplu` | The label as published. |
| `option_type` | enum | yes | see below | `party` | Kind of option. |
| `entity_id` | slug | cond | FK → `entities` | `pex` | Required for `party`, `alliance`, `candidate`, `independent`; must be empty for every other type. Its `entity_type` must equal `option_type` (R-61). |
| `share_raw` | decimal | yes | 0–100, as published | `31.5` | The published percentage, never recomputed. |
| `share_qualifier` | enum | no | `lt` | `lt` | `lt`: published as "below `share_raw`" (e.g. `<1%` → `share_raw = 1`, `share_qualifier = lt`). Empty = exact value. |
| provenance block | | | §5.1 | | Usually identical to the poll's. |

`option_type` values:

| Value | Meaning | Romanian examples | Counts as a vote option in M-1.1 |
|---|---|---|---|
| `party` | a party | the party name or acronym as printed | yes |
| `alliance` | an alliance | the alliance name as printed | yes |
| `candidate` | a presidential candidate | the candidate name as printed | yes |
| `independent` | one named independent candidate in a list election | the candidate name as printed (a generic "Independenți" bucket is `other`) | yes |
| `other` | a catch-all for other parties/candidates | "Alt partid", "Alt candidat", "Altele" | yes, as "others" (M-1.1) |
| `undecided` | does not know yet | "Nu știu", "Nehotărât" | no |
| `non_response` | refuses to answer | "Nu răspund" | no |
| `undecided_or_non_response` | the two above published as one bucket | "NS/NR" | no |
| `would_not_vote` | will not vote | "Nu voi vota", "Nu merg la vot" | no |
| `none` | explicitly none of the options | "Niciunul" | no |
| `blank_or_invalid` | would cast a blank or invalid ballot | "Vot alb", "Vot anulat" | no |
| `other_non_vote` | any other non-vote answer, explained in `notes` | "Depinde" | no |

### 6.13 `polls/<pollster_id>/inventory.csv` (reserved for T-011)

> **RESERVED.** T-011 defines this file and adds its column table to this
> section (T-011's scope allows editing `docs/DATA_MODEL.md` for this). Until
> then the file is not created and T-003 does not validate it.

Expected content, from T-011's scope: one row per discovered publication of
this pollster: URL, election, how it was found (discovery source), and status
`found | archived | extracted | verified | excluded` with a reason. To keep
the model linked, the inventory should reference the existing IDs
(`election_id`, `document_id` once archived, `poll_id` once extracted) and
reuse the provenance block (§5.1) and the types of §3.2.

### 6.14 Header lines (copy-paste reference)

The exact first line of each file, in order (generated from the tables above;
the tables win if they ever disagree):

```text
registry/elections.csv
election_id,election_type,body,round,election_date,name,status,source_url,source_type,retrieved_at,verified,notes

registry/entities.csv
entity_id,entity_type,name,short_name,color,source_url,source_type,retrieved_at,verified,notes

registry/pollsters.csv
pollster_id,name,short_name,website,typical_modes,source_url,source_type,retrieved_at,verified,notes

registry/pollster_aliases.csv
pollster_id,alias,source_url,source_type,retrieved_at,verified,notes

registry/pollster_affiliations.csv
pollster_id,relation,counterpart_name,counterpart_entity_id,period_start,period_end,description,source_url,source_type,retrieved_at,verified,notes

elections/<election_id>/entity_map.csv
election_id,poll_entity_id,relation,result_entity_id,effective_date,source_url,source_type,retrieved_at,verified,notes

elections/<election_id>/candidate_support.csv
election_id,candidate_entity_id,party_entity_id,support_type,announced_date,source_url,source_type,retrieved_at,verified,notes

elections/<election_id>/results.csv
election_id,scope,entity_id,votes,source_url,source_type,retrieved_at,verified,notes

elections/<election_id>/results_totals.csv
election_id,scope,registered_voters,voters,valid_votes,invalid_votes,source_url,source_type,retrieved_at,verified,notes

elections/<election_id>/archive_manifest.csv  and  polls/<pollster_id>/archive_manifest.csv
document_id,title,published_date,format,archive_url,sha256,raw_path,source_url,source_type,retrieved_at,notes

polls/<pollster_id>/polls.csv
poll_id,pollster_id,election_id,headline,scenario,fieldwork_start,fieldwork_end,published_date,sample_size,sample_size_expressed,mode,population,population_geo,target_scope,question_type,question_wording,sponsor,sponsor_type,weighting_published,moe_published,margin_of_error,topline_coverage,document_id,extraction_method,source_url,source_type,retrieved_at,verified,notes

polls/<pollster_id>/poll_results.csv
poll_id,share_base,option_order,option_label,option_type,entity_id,share_raw,share_qualifier,source_url,source_type,retrieved_at,verified,notes
```

## 7. Integrity rules (for T-003)

Severity: **E** = error (validation fails), **W** = warning (reported, does
not fail). Rules apply only to rows that exist; a header-only file passes all
row rules.

**Running and output.** `uv run sondaje validate` checks `data/` (options:
`--data-dir DIR`, `--reference-date YYYY-MM-DD`, `--against REF`, `--strict`,
`--quiet`). Each finding is one line:

```text
<path>:<row>: [R-xx] error|warning: <message>
```

`<path>` is relative to the working directory with `/` separators, and
`<row>` is the line number in the file (header = 1). File-level findings
(e.g. R-05, a missing file, an R-34 removal) have no `:<row>` part. The output
ends with a summary line `N error(s), M warning(s)`. The exit code is 1 if
there is an error (or, with `--strict`, a warning), else 0. `--quiet` hides
warnings. `--against REF` (e.g. `--against main`) adds the append-only check
R-34 against the git reference `REF`; without it, R-34 is not run.

**One finding per problem.** Where two rules describe the same problem, only
the more specific one is reported: a duplicate key in `elections`, `entities`,
or `pollsters` is R-30 (not R-04); a duplicate alias is R-31 only; an empty
required provenance cell is R-10 (not R-03); a `poll_results` row whose poll
does not exist is R-06 (not R-60); a full topline whose exact shares exceed
100 + `tol` is R-91 (not also R-90); the `raw_path` prefix of R-71 is reported
by the `path` type (R-03). Other overlaps are reported under each rule (e.g.
R-05 for an unregistered directory with rows, plus R-06 for each row).

Parameters (T-003 exposes them as constants):
- `share_sum_tolerance_pp = 2.0`
- `max_poll_age_days = 365`
- `reference_date` = the date validation runs; overridable so that fixtures
  (e.g. the fictitious example of §10, dated 2099) can be validated.

### 7.1 Files and types

| ID | Sev | Rule |
|---|---|---|
| R-01 | E | File is UTF-8 without BOM, uses LF line endings, ends with a newline, parses as CSV (balanced quotes), and has no line breaks inside fields. A file that is not valid UTF-8 is not checked further; a row with a line break inside a field is skipped. The "quote only when needed" style of §3.1 is not validated (the parsed values are the same either way). |
| R-02 | E | The header equals the column list of §6 for that file, in order. |
| R-03 | E | Every cell matches its column type (§3.2) and enum; `yes` columns are not empty; no cell has leading or trailing whitespace (any column). A row with the wrong number of fields (including an empty line) is reported here and skipped. |
| R-04 | E | No duplicate key within a file (keys given per table in §6). |
| R-05 | E | Only the files of §2.1 exist under `data/` (ignoring `data/raw/`, `data/README.md`, and `.gitkeep` files). `candidate_support.csv` exists only for presidential elections (the election type comes from the registry, or from the `pres-` prefix if the election is not registered yet). Each `data/polls/<pollster_id>/` has `polls.csv`, `poll_results.csv`, and `archive_manifest.csv`. Each directory name is a valid ID; once any file in the directory has rows, the ID must exist in the matching registry (header-only directories, such as the MVP election directories before T-004, pass). A reserved `inventory.csv` (§6.13) is a **warning** ("reserved; not validated") until T-011 defines it. |
| R-06 | E | Every column holding an `election_id`, `entity_id`, `pollster_id`, `poll_id`, or `document_id` from another table references an existing row (FK). |
| R-07 | E | The `election_id` / `pollster_id` column of a per-directory file equals its directory name. |

### 7.2 Provenance

| ID | Sev | Rule |
|---|---|---|
| R-10 | E | `source_url`, `source_type`, and `retrieved_at` are not empty in every row of every file; `verified` is not empty where the column exists. |
| R-11 | E | `retrieved_at ≤ reference_date`. |
| R-12 | E | In `polls.csv`, `retrieved_at ≥ published_date`. |
| R-13 | W | `source_type = other` without `notes`. |
| R-14 | E | `verified = true` is not allowed when `source_type` is `wikipedia` or `aggregator`. |
| R-15 | W | A `results.csv` / `results_totals.csv` row whose `source_type ≠ official`. |

### 7.3 Registries

| ID | Sev | Rule |
|---|---|---|
| R-20 | E | `election_id` agrees with its row: prefix ↔ `election_type` (`parl`↔`parliamentary`, `pres`↔`presidential`, `ep`↔`european`, `local`↔`local`); year = year of `election_date`; `-cd`↔`chamber_of_deputies`, `-sen`↔`senate`; `presidential`↔`president`, `european`↔`european_parliament`; `-rN` ↔ `round = N`, and no `-rN` ↔ `round = 1`; parliamentary IDs always have `-cd` or `-sen`; presidential IDs always have `-rN`; parliamentary and European IDs never have `-rN` (single-round types, §4.1). A `-<tag>` part (§4.1) is ignored by this check. Type `local` is reserved: any `local` row or `local-` ID is an error until T-062 adds its bodies and ID parts (§9). |
| R-21 | E | For an election with `round = N ≥ 2`, the election with the same ID ending in `-r(N−1)` exists and has an earlier `election_date`. |
| R-30 | E | `entity_id`, `pollster_id`, `election_id` values are unique across their registry (no reuse). |
| R-31 | E | `pollster_aliases.alias` is unique across all pollsters (compared case-insensitively). |
| R-32 | E | `pollster_affiliations.period_start ≤ period_end` when both are set (compared at the shared precision). |
| R-33 | W | An entity without `color`. |
| R-34 | E | Append-only files: compared with `main`, no row was removed or reordered, and no ID changed. Run with `sondaje validate --against REF` (e.g. `--against main`; needs git). Every row of an append-only file at `REF` must still be at the same position with the same key; non-key cells may change (corrections, §2.2). One error per file, at the first difference; a deleted file that had rows at `REF`, or an unknown `REF`, is also an error. |
| R-35 | W | `pollster_affiliations`: `counterpart_entity_id` is empty, but `counterpart_name` equals the `name` or `short_name` of a registered entity (ignoring case). |

### 7.4 Election files

| ID | Sev | Rule |
|---|---|---|
| R-40 | E | `entity_map`: `result_entity_id` is required for `alliance_member`, `merged_into`, and `ran_on_list_of`, and must be empty for `withdrawn`, `excluded`, `not_registered`. For `alliance_member`, the target's `entity_type` is `alliance`. |
| R-41 | E | `entity_map`: a `poll_entity_id` is not itself a contestant in `results.csv` of the same election, and a `result_entity_id` is a contestant there (checked only when `results.csv` has rows). |
| R-42 | E | `candidate_support`: the election is presidential; the candidate has type `candidate`; the party has type `party` or `alliance`. |
| R-43 | W | `candidate_support`: the candidate is neither a contestant in `results.csv` nor in `entity_map.csv` of the election (checked only when `results.csv` has rows). |
| R-44 | E | Every `entity_id` used in `poll_results` of a poll for election E is either a contestant in `results.csv` of E or a `poll_entity_id` in `entity_map.csv` of E (checked only when `results.csv` of E has rows). This is what makes M-1.5 mechanical. |
| R-45 | E | `entity_map`, relation `ran_on_list_of`: the election is a list election (`election_type` `parliamentary` or `european`); the `poll_entity_id` (guest) and the `result_entity_id` (host) both have `entity_type` `party` or `alliance`. |
| R-46 | E | `entity_map`: a `result_entity_id` is not a `poll_entity_id` in the same file (mappings are one step, so the target must be a ballot contestant; checked even when `results.csv` has no rows). |
| R-50 | E | `results`: every contestant has a row in each of the three scopes (`0` is written explicitly). |
| R-51 | E | `results`: for every contestant, `votes(domestic) + votes(diaspora) = votes(total)` exactly. Same for every numeric column of `results_totals` whose three cells (domestic, diaspora, total) are all set. |
| R-52 | E | `results`: contestants of a presidential election have type `candidate`; of a parliamentary or European election, type `party`, `alliance`, or `independent`. |
| R-53 | E | `results` vs `results_totals`: for every scope, the sum of `votes` equals `valid_votes` exactly. If `results.csv` has rows but `results_totals.csv` (or its row for a scope) is missing, that is also an R-53 error. |
| R-54 | W | `results_totals`: `valid_votes + invalid_votes > voters` when all three are set. |
| R-55 | W | `results_totals`: `voters > registered_voters` in the `domestic` scope when both are set. |

### 7.5 Poll files

| ID | Sev | Rule |
|---|---|---|
| R-60 | E | `poll_results`: within each (`poll_id`, `share_base`), `option_order` is 1, 2, …, N without gaps. Every poll has at least one `poll_results` row, and every `poll_results` row has a poll. |
| R-61 | E | `poll_results`: `entity_id` is set iff `option_type` ∈ {`party`, `alliance`, `candidate`, `independent`}, and then `entities.entity_type = option_type`. Entity types fit the election type as in R-52. |
| R-62 | E | Within one (`pollster_id`, `election_id`), the same `option_label` always maps to the same `entity_id` (including an empty one: a label left without entity in one poll and mapped in another is an error). Within one (`poll_id`, `share_base`), an `entity_id` appears at most once. |
| R-63 | E | Polls sharing (`document_id`, `election_id`, `fieldwork_start`, `fieldwork_end`) form one survey: exactly one of them has `headline = true`. `headline = false` requires a non-empty `scenario`. The cells are compared as written, so polls with empty fieldwork dates from the same document form one survey. |
| R-64 | E | `population_geo` ↔ `target_scope`: `residents` → `domestic`; `residents_and_diaspora` → `total`; `diaspora` → `diaspora`. Empty `population_geo` → `target_scope = domestic`, unless `notes` explains otherwise (then W). |
| R-65 | E | `sponsor` is not empty unless `sponsor_type` ∈ {`self`, `not_disclosed`}; `sponsor` is empty when `sponsor_type = not_disclosed`. |
| R-66 | E | `margin_of_error` is set only if `moe_published = true`. `sample_size_expressed ≤ sample_size` when both are set. |
| R-67 | E | `extraction_method` fits the document `format`: `pdf_text` needs `pdf_text`; `html` needs `html`; `manual_double_entry` fits any format. |
| R-68 | E | `polls.source_url` equals `source_url` of its `document_id` in the same directory. |
| R-69 | W | `share_base = other_subset` or `option_type = other_non_vote` without `notes`. |
| R-70 | E | `poll_id` matches `<pollster_id>-<election_id>-<YYYYMMDD>[-<suffix>]` with its own row's values, where `YYYYMMDD` = `fieldwork_end`, or `published_date` if `fieldwork_end` is empty. |
| R-71 | E | Every `archive_manifest.csv` row under `data/polls/` has an `archive_url`. `raw_path`, when set, starts with `data/raw/`. `document_id` starts with the directory ID (§4.5). |
| R-72 | W | Two manifest rows in one file with the same `sha256` (same file archived twice). |

### 7.6 Dates

| ID | Sev | Rule |
|---|---|---|
| R-80 | E | `fieldwork_start ≤ fieldwork_end` when both are set. |
| R-81 | E | `fieldwork_end < election_date` (fieldwork on election day is an exit poll, out of scope). If `fieldwork_end` is empty, `fieldwork_start` is used; if both are empty, R-81 is skipped (R-86 warns). |
| R-82 | E | `published_date ≥ fieldwork_end` when both are set. |
| R-83 | W | `published_date ≥ election_date` (published on or after election day). |
| R-84 | E | For an election with `round = N ≥ 2`: `fieldwork_start` (or `fieldwork_end` if the start is empty, or `published_date` if both are empty) is **after** the `election_date` of round N−1. Hypothetical pairings asked before the earlier round are not polls for this election. |
| R-85 | W | `fieldwork_end` (or `published_date`) is more than `max_poll_age_days` before `election_date`. |
| R-86 | W | Neither `fieldwork_start` nor `fieldwork_end` is set (the poll cannot enter M-1.3 windows). |

### 7.7 Sums and duplicates

| ID | Sev | Rule |
|---|---|---|
| R-90 | E | For every poll with `topline_coverage = full` and every `share_base` it has: let `low` = Σ `share_raw` over rows with an empty `share_qualifier`, and `high` = `low` + Σ `share_raw` over rows with `share_qualifier = lt`. Then `low − tol ≤ 100 ≤ high + tol`, with `tol = share_sum_tolerance_pp`. |
| R-91 | E | For every poll and base: `low` (as in R-90) ≤ 100 + `tol` (applies to `partial` toplines too). |
| R-92 | W | A `share_base = expressed_option` row with a non-vote `option_type` (undecided, non-response, would-not-vote, …). |
| R-93 | E | **Duplicate poll:** two `headline = true` polls with the same `pollster_id`, `election_id`, and non-empty `fieldwork_start` and `fieldwork_end`. |
| R-94 | W | **Possible duplicate:** two `headline = true` polls of the same pollster and election without fieldwork dates, with the same `published_date`. |

## 8. Coverage of METHODOLOGY inputs

| Section | Input | Where |
|---|---|---|
| M-1.1 | raw shares; which options are named, "others", or non-vote | `poll_results.share_raw`, `option_type`, `share_base` |
| M-1.2 | entities present in poll and result; result shares for the 1% threshold | `poll_results.entity_id`, `results.votes / results_totals.valid_votes` |
| M-1.3 | fieldwork end; election day; final poll per house | `polls.fieldwork_end`, `elections.election_date`, `polls.pollster_id` |
| M-1.4 | domestic/diaspora/total results; target per poll | `results.scope`, `results_totals`, `polls.target_scope`, `polls.population_geo` |
| M-1.5 | alliance mapping; parties on another party's lists; withdrawals/exclusions; rounds as separate elections; candidate → party | `entity_map.csv` (`alliance_member`, `merged_into`, `ran_on_list_of`, …), `elections.round`, `candidate_support.csv` |
| M-1.6 | the (house, election) unit | `polls.pollster_id`, `polls.election_id` |
| M-2.1–M-2.6 | `s_j`, `r_j`, `k`, houses, recency | derived from the above |
| M-3.1–M-3.3 | `t`, all campaign polls | `polls.fieldwork_start/end`, `published_date`, `headline` (avoids counting two scenarios of one survey) |
| M-3.4 | `n` per poll | `polls.sample_size` (and `sample_size_expressed`) |
| M-4.1 | `n`, `r_j` | `polls.sample_size`, results |
| M-5.1d | party-commissioned polls; affiliations | `polls.sponsor_type ∈ {party, candidate}`, `pollster_affiliations.csv` |
| M-5.1e | elections covered | distinct `polls.election_id` per pollster |
| M-5.3 | sample size, fieldwork dates, mode, wording, weighting, MoE, sponsor | §6.11 (mapping listed under the table) |

## 9. Changing the schema

- The schema is frozen at Milestone M0. Any change (new column, new enum
  value, new file) goes through a task that edits this document, bumps the
  **schema version** (minor: additive; major: breaking), updates the T-003
  schema in code, and migrates existing files in the same branch.
- A new data column is inserted just before the provenance block, so the
  provenance block always stays last.
- Exception: T-011 fills in §6.13 without a version bump (reserved).

### 9.1 Schema history

| Version | Task | Kind | Changes |
|---|---|---|---|
| 1.0 | T-001 | initial | Frozen at Milestone M0. |
| 1.1 | T-007 | minor (additive) | New `entity_map.relation` value `ran_on_list_of` (§6.6) with rules R-45 and R-46, and R-40 extended to it. New `mode` value `face_to_face` and `mode` conventions (§6.11). New warning R-35 (affiliation counterpart not linked to its entity). Person-ID rules: which given name, full family name, one person in two roles (§4.2). Meaning of `verified` in the pollster registries (§5.3). §7: output format, `--against REF`, one finding per problem, and the readings T-003 implemented (R-01, R-03, R-05, R-20, R-34, R-43, R-53, R-62, R-63, R-81). Migration: no header changed; `parl-2024-cd/entity_map.csv` row `pmp` set to `ran_on_list_of` → `fd`; `counterpart_entity_id` filled in six `pollster_affiliations.csv` rows. |

## 10. Worked example (fictitious)

> **FICTITIOUS.** Everything in this section is invented to illustrate the
> schema: the election `parl-2099-cd`, the parties, the pollster, the URLs
> (on the reserved `example.org` domain), the figures, and the hash (it is
> the SHA-256 of an empty file). None of it is real data, and none of it is
> stored under `data/`.

**Story.** The fictitious pollster *Institutul Exemplar de Sondare* polls the
fictitious Chamber of Deputies election of 2099-06-07 for a TV channel.
Partidul Delta and Partidul Epsilon run together on the list of *Alianța
Gama*, but the poll still lists them separately. Partidul Zeta withdraws its
list after the poll. The report publishes two bases: all respondents, and
respondents who named a party (whose figures sum to 101 because of rounding;
they are stored as published).

`data/registry/elections.csv`
```csv
election_id,election_type,body,round,election_date,name,status,source_url,source_type,retrieved_at,verified,notes
parl-2099-cd,parliamentary,chamber_of_deputies,1,2099-06-07,"Parliamentary election 2099, Chamber of Deputies",held,https://example.org/bec/parl-2099,official,2099-06-20,true,Fictitious example.
```

`data/registry/entities.csv`
```csv
entity_id,entity_type,name,short_name,color,source_url,source_type,retrieved_at,verified,notes
alfa,party,Partidul Alfa,PA,#1F77B4,https://example.org/bec/parl-2099/liste,official,2099-06-20,true,
beta,party,Partidul Beta,PB,#D62728,https://example.org/bec/parl-2099/liste,official,2099-06-20,true,
gama,alliance,Alianța Gama,AG,#2CA02C,https://example.org/bec/parl-2099/liste,official,2099-06-20,true,
delta,party,Partidul Delta,PD,,https://example.org/bec/parl-2099/liste,official,2099-06-20,true,Member of gama in parl-2099-cd.
epsilon,party,Partidul Epsilon,PE,,https://example.org/bec/parl-2099/liste,official,2099-06-20,true,Member of gama in parl-2099-cd.
zeta,party,Partidul Zeta,PZ,#9467BD,https://example.org/stiri/zeta-retragere,media,2099-06-20,true,Withdrew its list before parl-2099-cd.
omega,party,Partidul Omega,PO,#8C564B,https://example.org/bec/parl-2099/liste,official,2099-06-20,true,
```

`data/registry/pollsters.csv`
```csv
pollster_id,name,short_name,website,typical_modes,source_url,source_type,retrieved_at,verified,notes
exemplar,Institutul Exemplar de Sondare,Exemplar,https://example.org/exemplar,cati;cawi,https://example.org/exemplar/despre,pollster,2099-06-20,true,
```

`data/registry/pollster_aliases.csv`
```csv
pollster_id,alias,source_url,source_type,retrieved_at,verified,notes
exemplar,Institutul Exemplar,https://example.org/stiri/sondaj-exemplar,media,2099-06-20,false,Variant used by a news site.
```

`data/registry/pollster_affiliations.csv`
```csv
pollster_id,relation,counterpart_name,counterpart_entity_id,period_start,period_end,description,source_url,source_type,retrieved_at,verified,notes
exemplar,client,Televiziunea Exemplu,,2099,,Commissioned the polls published in the 2099 campaign.,https://example.org/exemplar/raport-2099-05.pdf,pollster,2099-06-20,true,
```

`data/elections/parl-2099-cd/entity_map.csv`
```csv
election_id,poll_entity_id,relation,result_entity_id,effective_date,source_url,source_type,retrieved_at,verified,notes
parl-2099-cd,delta,alliance_member,gama,2099-04-10,https://example.org/bec/parl-2099/aliante,official,2099-06-20,true,
parl-2099-cd,epsilon,alliance_member,gama,2099-04-10,https://example.org/bec/parl-2099/aliante,official,2099-06-20,true,
parl-2099-cd,zeta,withdrawn,,2099-05-28,https://example.org/bec/parl-2099/retrageri,official,2099-06-20,true,
```

`candidate_support.csv` is not used: this is not a presidential election.
(For a presidential round it would contain rows such as
`pres-2099-r1,ion-exemplu,alfa,nominated,2099-02-15,<source…>`.)

`data/elections/parl-2099-cd/results.csv`
```csv
election_id,scope,entity_id,votes,source_url,source_type,retrieved_at,verified,notes
parl-2099-cd,domestic,alfa,2000000,https://example.org/aep/parl-2099/rezultate.csv,official,2099-06-20,true,
parl-2099-cd,domestic,beta,1500000,https://example.org/aep/parl-2099/rezultate.csv,official,2099-06-20,true,
parl-2099-cd,domestic,gama,1200000,https://example.org/aep/parl-2099/rezultate.csv,official,2099-06-20,true,
parl-2099-cd,domestic,omega,45000,https://example.org/aep/parl-2099/rezultate.csv,official,2099-06-20,true,
parl-2099-cd,diaspora,alfa,100000,https://example.org/aep/parl-2099/rezultate.csv,official,2099-06-20,true,
parl-2099-cd,diaspora,beta,150000,https://example.org/aep/parl-2099/rezultate.csv,official,2099-06-20,true,
parl-2099-cd,diaspora,gama,200000,https://example.org/aep/parl-2099/rezultate.csv,official,2099-06-20,true,
parl-2099-cd,diaspora,omega,5000,https://example.org/aep/parl-2099/rezultate.csv,official,2099-06-20,true,
parl-2099-cd,total,alfa,2100000,https://example.org/aep/parl-2099/rezultate.csv,official,2099-06-20,true,
parl-2099-cd,total,beta,1650000,https://example.org/aep/parl-2099/rezultate.csv,official,2099-06-20,true,
parl-2099-cd,total,gama,1400000,https://example.org/aep/parl-2099/rezultate.csv,official,2099-06-20,true,
parl-2099-cd,total,omega,50000,https://example.org/aep/parl-2099/rezultate.csv,official,2099-06-20,true,
```

`data/elections/parl-2099-cd/results_totals.csv`
```csv
election_id,scope,registered_voters,voters,valid_votes,invalid_votes,source_url,source_type,retrieved_at,verified,notes
parl-2099-cd,domestic,18000000,4900000,4745000,150000,https://example.org/aep/parl-2099/rezultate.csv,official,2099-06-20,true,
parl-2099-cd,diaspora,,465000,455000,8000,https://example.org/aep/parl-2099/rezultate.csv,official,2099-06-20,true,No permanent-list figure for the diaspora.
parl-2099-cd,total,,5365000,5200000,158000,https://example.org/aep/parl-2099/rezultate.csv,official,2099-06-20,true,
```

`data/elections/parl-2099-cd/archive_manifest.csv`
```csv
document_id,title,published_date,format,archive_url,sha256,raw_path,source_url,source_type,retrieved_at,notes
parl-2099-cd-doc-001,Rezultate finale Camera Deputaților,2099-06-10,csv,,e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855,data/raw/elections/parl-2099-cd/rezultate.csv,https://example.org/aep/parl-2099/rezultate.csv,official,2099-06-20,
```

`data/polls/exemplar/archive_manifest.csv`
```csv
document_id,title,published_date,format,archive_url,sha256,raw_path,source_url,source_type,retrieved_at,notes
exemplar-doc-001,"Barometru politic, mai 2099",2099-05-26,pdf_text,https://web.archive.org/web/20990526120000/https://example.org/exemplar/raport-2099-05.pdf,e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855,data/raw/polls/exemplar/exemplar-doc-001.pdf,https://example.org/exemplar/raport-2099-05.pdf,pollster,2099-05-27,
```

`data/polls/exemplar/polls.csv`
```csv
poll_id,pollster_id,election_id,headline,scenario,fieldwork_start,fieldwork_end,published_date,sample_size,sample_size_expressed,mode,population,population_geo,target_scope,question_type,question_wording,sponsor,sponsor_type,weighting_published,moe_published,margin_of_error,topline_coverage,document_id,extraction_method,source_url,source_type,retrieved_at,verified,notes
exemplar-parl-2099-cd-20990524,exemplar,parl-2099-cd,true,,2099-05-20,2099-05-24,2099-05-26,1100,792,cati,adults,residents,domestic,prompted_list,"Dacă duminica viitoare ar avea loc alegeri pentru Camera Deputaților, cu ce partid sau alianță ați vota?",Televiziunea Exemplu,media,true,true,3,full,exemplar-doc-001,pdf_text,https://example.org/exemplar/raport-2099-05.pdf,pollster,2099-05-27,true,
```

`data/polls/exemplar/poll_results.csv`
```csv
poll_id,share_base,option_order,option_label,option_type,entity_id,share_raw,share_qualifier,source_url,source_type,retrieved_at,verified,notes
exemplar-parl-2099-cd-20990524,all_respondents,1,Partidul Alfa,party,alfa,28,,https://example.org/exemplar/raport-2099-05.pdf,pollster,2099-05-27,true,
exemplar-parl-2099-cd-20990524,all_respondents,2,Partidul Beta,party,beta,22,,https://example.org/exemplar/raport-2099-05.pdf,pollster,2099-05-27,true,
exemplar-parl-2099-cd-20990524,all_respondents,3,Partidul Delta,party,delta,9,,https://example.org/exemplar/raport-2099-05.pdf,pollster,2099-05-27,true,
exemplar-parl-2099-cd-20990524,all_respondents,4,Partidul Epsilon,party,epsilon,6,,https://example.org/exemplar/raport-2099-05.pdf,pollster,2099-05-27,true,
exemplar-parl-2099-cd-20990524,all_respondents,5,Partidul Zeta,party,zeta,3,,https://example.org/exemplar/raport-2099-05.pdf,pollster,2099-05-27,true,
exemplar-parl-2099-cd-20990524,all_respondents,6,Alt partid,other,,4,,https://example.org/exemplar/raport-2099-05.pdf,pollster,2099-05-27,true,
exemplar-parl-2099-cd-20990524,all_respondents,7,Nu știu / Nu răspund,undecided_or_non_response,,18,,https://example.org/exemplar/raport-2099-05.pdf,pollster,2099-05-27,true,
exemplar-parl-2099-cd-20990524,all_respondents,8,Nu voi merge la vot,would_not_vote,,10,,https://example.org/exemplar/raport-2099-05.pdf,pollster,2099-05-27,true,
exemplar-parl-2099-cd-20990524,expressed_option,1,Partidul Alfa,party,alfa,39,,https://example.org/exemplar/raport-2099-05.pdf,pollster,2099-05-27,true,
exemplar-parl-2099-cd-20990524,expressed_option,2,Partidul Beta,party,beta,31,,https://example.org/exemplar/raport-2099-05.pdf,pollster,2099-05-27,true,
exemplar-parl-2099-cd-20990524,expressed_option,3,Partidul Delta,party,delta,13,,https://example.org/exemplar/raport-2099-05.pdf,pollster,2099-05-27,true,
exemplar-parl-2099-cd-20990524,expressed_option,4,Partidul Epsilon,party,epsilon,8,,https://example.org/exemplar/raport-2099-05.pdf,pollster,2099-05-27,true,
exemplar-parl-2099-cd-20990524,expressed_option,5,Partidul Zeta,party,zeta,4,,https://example.org/exemplar/raport-2099-05.pdf,pollster,2099-05-27,true,
exemplar-parl-2099-cd-20990524,expressed_option,6,Alt partid,other,,6,,https://example.org/exemplar/raport-2099-05.pdf,pollster,2099-05-27,true,
```

**What validation checks here (examples).** R-70: the `poll_id` date
`20990524` equals `fieldwork_end`. R-80–R-82: 2099-05-20 ≤ 2099-05-24 <
2099-06-07, and 2099-05-26 ≥ 2099-05-24. R-90: the `all_respondents` base
sums to 100 and the `expressed_option` base to 101, both within ±2.0.
R-41: `delta`, `epsilon`, `zeta` are not contestants in `results.csv`, and
`gama` is. R-51/R-53: 2,000,000 + 100,000 = 2,100,000 for `alfa`, and the
domestic votes sum to 4,745,000 = `valid_votes`. R-64: `residents` →
`domestic`. R-68: the poll's `source_url` equals the document's.

**What the pipeline does with it (illustration only; M-1 and T-020 are
normative).** Using the `all_respondents` base and the `domestic` target
(M-1.4):
1. M-1.5: `delta` (9) + `epsilon` (6) → `gama` = 15; `zeta` (3) is dropped
   because it withdrew, and the adjustment is logged.
2. M-1.1: the non-vote options (18 + 10) are removed. The remaining named
   options plus "others" sum to 28 + 22 + 15 + 4 = 69, so `s_alfa` =
   28/69 = 40.58%, `s_beta` = 31.88%, `s_gama` = 21.74%, `s_others` = 5.80%.
3. Results (domestic): `r_alfa` = 2,000,000 / 4,745,000 = 42.15%, `r_beta` =
   31.61%, `r_gama` = 25.29%, `r_omega` = 0.95%. M-1.2: `omega` is below 1%,
   so it is merged into "others" (0.95%).
4. M-2.1: `e_alfa` = 40.58 − 42.15 = −1.57 pp, and so on.

The data files above are never changed by any of these steps.
