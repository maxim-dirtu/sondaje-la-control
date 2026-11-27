# data/

Canonical project data: versioned UTF-8 CSV files
([ADR-0004](../docs/decisions/0004-data-storage-csv-in-git.md)).
The full specification (every column, type, allowed value, ID convention, and
validation rule) is **[docs/DATA_MODEL.md](../docs/DATA_MODEL.md)**. This file
is only a short guide.

## Layout

| Path | Content | Written by | Mode |
|---|---|---|---|
| `registry/elections.csv` | one row per election (each round separate) | T-004, T-061 | append-only |
| `registry/entities.csv` | parties, alliances, candidates, independents | T-004 (+ T-010, pollster tasks) | append-only |
| `registry/pollsters.csv` | polling firms | T-005 (+ pollster tasks) | append-only |
| `registry/pollster_aliases.csv` | pollster name variants | T-005 (+ pollster tasks) | append-only |
| `registry/pollster_affiliations.csv` | sourced client/ownership/personnel links | T-005 (+ pollster tasks) | append-only |
| `elections/<election_id>/entity_map.csv` | polled entity → ballot contestant (alliances, parties on another party's lists, withdrawals) | T-004 (+ pollster tasks) | append-only |
| `elections/<election_id>/candidate_support.csv` | presidential only: candidate → supporting parties | T-004 | owned |
| `elections/<election_id>/results.csv` | votes per contestant, scope `domestic` / `diaspora` / `total` | T-010 | generated |
| `elections/<election_id>/results_totals.csv` | valid/invalid votes and voters per scope | T-010 | generated |
| `elections/<election_id>/archive_manifest.csv` | official source files: URL + SHA-256 | T-010 | generated |
| `polls/<pollster_id>/polls.csv` | one row per poll (metadata, transparency fields) | that pollster's task | owned |
| `polls/<pollster_id>/poll_results.csv` | full topline: one row per poll × option × base | that pollster's task | owned |
| `polls/<pollster_id>/archive_manifest.csv` | archived original reports: URL, Web Archive URL, SHA-256 | that pollster's task | owned |
| `polls/<pollster_id>/inventory.csv` | every discovered publication, how it was found, and its status (`found` → `archived` → `extracted` → `verified`, or `excluded` with a reason) | that pollster's task | owned |
| `raw/` | local copies of downloaded sources | tools | **git-ignored** |

The MVP election directories (`parl-2024-cd`, `pres-2025-r1`, `pres-2025-r2`)
and the registries exist with header lines only. Pollster directories are
created by the pollster tasks; copy the header lines from DATA_MODEL.md §6.14.
Poll collection follows [docs/POLL_INGESTION.md](../docs/POLL_INGESTION.md).

## Rules in one screen

- **Store values exactly as published.** Never normalize, round, re-base, or
  "fix" a sum. Normalization happens in code (METHODOLOGY M-1.1).
- **Full toplines:** every published option is a row, including "other",
  undecided, non-response, and "would not vote", each with an `option_type`.
- **Empty cell = not published / unknown.** Never guess a value; log the gap
  in your task file.
- **Provenance on every row:** `source_url`, `source_type`, `retrieved_at`,
  `verified`. Wikipedia and aggregators are indexes, not sources
  (`verified = false`).
- **Append-only files:** add rows at the end; never delete, reorder, or rename
  IDs. Rebase on `main` and check the ID is new before appending.
- **IDs** are lowercase ASCII slugs and never change: `parl-2024-cd`,
  `pres-2025-r1`, `<pollster_id>-<election_id>-<YYYYMMDD>` for polls.
- **Format:** UTF-8 without BOM, LF, comma-separated, header in the documented
  column order, no line breaks inside fields.
- **Neutral wording** in notes and descriptions
  ([ADR-0003](../docs/decisions/0003-neutral-language.md)).
- Validate before committing: `uv run sondaje validate`. Add `--against main`
  to also check that append-only files were only appended to (R-34).
- The election results files (`results.csv`, `results_totals.csv`,
  `archive_manifest.csv`) are generated: never edit them by hand; re-run
  `uv run sondaje ingest-results <election_id>` (downloads go to `data/raw/`).
