"""Poll-file rules: R-60…R-72."""

import re
from collections import defaultdict

from sondaje.schema import (
    ARCHIVE_MANIFEST,
    ELECTIONS,
    ENTITIES,
    NAMED_OPTION_TYPES,
    POLL_RESULTS,
    POLLS,
    Location,
)
from sondaje.validation.cells import SLUG_RE
from sondaje.validation.model import DataFile, Dataset, Reporter, Row
from sondaje.validation.rules_elections import CONTESTANT_TYPES

TARGET_SCOPE_BY_GEO = {
    "residents": "domestic",
    "residents_and_diaspora": "total",
    "diaspora": "diaspora",
}
SPONSOR_OPTIONAL = ("self", "not_disclosed")
FORMAT_BY_EXTRACTION = {"pdf_text": "pdf_text", "html": "html"}
"""R-67: extraction methods that need one document format (others fit any format)."""


def check_poll_results(
    polls_file: DataFile | None,
    results_file: DataFile,
    entity_types: dict[str, str | None],
    election_types: dict[str, str | None],
    reporter: Reporter,
) -> None:
    """R-60 (option order), R-61, R-62, R-69 on ``poll_results.csv``."""
    shown = results_file.display_path
    poll_elections = {
        poll_id: row.get_str("election_id")
        for row in (polls_file.rows if polls_file else [])
        if (poll_id := row.get_str("poll_id")) is not None
    }
    groups: dict[tuple[str, str], list[Row]] = defaultdict(list)
    labels: dict[tuple[str, str], tuple[str, Row]] = {}
    for row in results_file.rows:
        poll_id, base = row.get_str("poll_id"), row.get_str("share_base")
        if poll_id is not None and base is not None:
            groups[poll_id, base].append(row)
        option_type, entity_id = row.get_str("option_type"), row.get_str("entity_id")
        election_id = poll_elections.get(poll_id) if poll_id else None
        if option_type in NAMED_OPTION_TYPES and row.is_empty("entity_id"):
            reporter.error(shown, row.line, "R-61", f"option_type {option_type!r} needs entity_id")
        elif option_type is not None and option_type not in NAMED_OPTION_TYPES:
            if not row.is_empty("entity_id"):
                reporter.error(
                    shown, row.line, "R-61", f"option_type {option_type!r} needs an empty entity_id"
                )
        elif entity_id in entity_types and entity_types[entity_id] != option_type:
            reporter.error(
                shown,
                row.line,
                "R-61",
                f"entity {entity_id!r} has entity_type {entity_types[entity_id]!r}, "
                f"but option_type is {option_type!r}",
            )
        else:
            election_type = election_types.get(election_id) if election_id else None
            allowed = CONTESTANT_TYPES.get(election_type or "")
            if allowed and option_type in NAMED_OPTION_TYPES and option_type not in allowed:
                reporter.error(
                    shown,
                    row.line,
                    "R-61",
                    f"option_type {option_type!r} does not fit a {election_type} election "
                    f"(allowed: {', '.join(allowed)})",
                )
        label = row.get_str("option_label")
        if label is not None and election_id is not None:
            first = labels.setdefault((election_id, label), (row.raw["entity_id"], row))
            if first[0] != row.raw["entity_id"]:
                reporter.error(
                    shown,
                    row.line,
                    "R-62",
                    f"label {label!r} maps to entity_id {row.raw['entity_id']!r}, but to "
                    f"{first[0]!r} on line {first[1].line} (same pollster and election)",
                )
        if (base == "other_subset" or option_type == "other_non_vote") and row.is_empty("notes"):
            reporter.warning(
                shown,
                row.line,
                "R-69",
                "other_subset / other_non_vote needs an explanation in notes",
            )
    for (poll_id, base), rows in groups.items():
        orders = sorted(o for row in rows if (o := row.get_int("option_order")) is not None)
        missing = sorted(set(range(1, max(orders, default=0) + 1)) - set(orders))
        if missing:
            reporter.error(
                shown,
                rows[0].line,
                "R-60",
                f"poll {poll_id!r}, base {base!r}: option_order is not contiguous from 1 "
                f"(missing {', '.join(map(str, missing))})",
            )
        seen: dict[str, int] = {}
        for row in rows:
            entity_id = row.get_str("entity_id")
            if entity_id is None:
                continue
            if entity_id in seen:
                reporter.error(
                    shown,
                    row.line,
                    "R-62",
                    f"entity {entity_id!r} appears twice in poll {poll_id!r}, base {base!r} "
                    f"(first on line {seen[entity_id]})",
                )
            else:
                seen[entity_id] = row.line


def _check_poll_id(row: Row) -> str | None:
    """R-70: ``<pollster_id>-<election_id>-<YYYYMMDD>[-<suffix>]``; returns the problem, if any."""
    poll_id, pollster_id = row.get_str("poll_id"), row.get_str("pollster_id")
    election_id = row.get_str("election_id")
    date_column = "published_date" if row.is_empty("fieldwork_end") else "fieldwork_end"
    date = row.get_date(date_column)
    if poll_id is None or pollster_id is None or election_id is None or date is None:
        return None
    prefix = f"{pollster_id}-{election_id}-{date:%Y%m%d}"
    if poll_id == prefix:
        return None
    if poll_id.startswith(prefix + "-") and SLUG_RE.match(poll_id[len(prefix) + 1 :]):
        return None
    return f"poll_id {poll_id!r} must be {prefix!r} (+ optional -suffix), from {date_column}"


def check_polls(
    polls_file: DataFile,
    results_file: DataFile | None,
    manifest_file: DataFile | None,
    reporter: Reporter,
) -> None:
    """R-60 (poll without results), R-63…R-68, R-70 on ``polls.csv``."""
    shown = polls_file.display_path
    polls_with_results = {
        poll_id
        for row in (results_file.rows if results_file else [])
        if (poll_id := row.get_str("poll_id")) is not None
    }
    documents: dict[str, Row] = {}
    for row in manifest_file.rows if manifest_file else []:
        document_id = row.get_str("document_id")
        if document_id is not None:
            documents.setdefault(document_id, row)
    surveys: dict[tuple[str, ...], list[Row]] = defaultdict(list)
    for row in polls_file.rows:
        line = row.line
        poll_id = row.get_str("poll_id")
        if poll_id is not None and results_file is not None and poll_id not in polls_with_results:
            reporter.error(shown, line, "R-60", f"poll {poll_id!r} has no rows in poll_results.csv")
        surveys[
            tuple(
                row.raw[c]
                for c in ("document_id", "election_id", "fieldwork_start", "fieldwork_end")
            )
        ].append(row)
        if row.get_bool("headline") is False and row.is_empty("scenario"):
            reporter.error(shown, line, "R-63", "headline = false needs a scenario")
        geo, target = row.get_str("population_geo"), row.get_str("target_scope")
        if geo is not None and target is not None and TARGET_SCOPE_BY_GEO[geo] != target:
            reporter.error(
                shown,
                line,
                "R-64",
                f"population_geo {geo!r} needs target_scope {TARGET_SCOPE_BY_GEO[geo]!r}",
            )
        elif row.is_empty("population_geo") and target is not None and target != "domestic":
            message = (
                f"population_geo is empty, so target_scope should be 'domestic', not {target!r}"
            )
            if row.is_empty("notes"):
                reporter.error(shown, line, "R-64", message)
            else:
                reporter.warning(shown, line, "R-64", message + " (explained in notes)")
        sponsor_type = row.get_str("sponsor_type")
        if sponsor_type is not None:
            if sponsor_type not in SPONSOR_OPTIONAL and row.is_empty("sponsor"):
                reporter.error(
                    shown, line, "R-65", f"sponsor_type {sponsor_type!r} needs a sponsor"
                )
            if sponsor_type == "not_disclosed" and not row.is_empty("sponsor"):
                reporter.error(shown, line, "R-65", "sponsor must be empty when not_disclosed")
        if not row.is_empty("margin_of_error") and row.get_bool("moe_published") is False:
            reporter.error(shown, line, "R-66", "margin_of_error is set but moe_published = false")
        size, expressed = row.get_int("sample_size"), row.get_int("sample_size_expressed")
        if size is not None and expressed is not None and expressed > size:
            reporter.error(
                shown, line, "R-66", f"sample_size_expressed {expressed} exceeds sample_size {size}"
            )
        document = documents.get(row.get_str("document_id") or "")
        if document is not None:
            method, doc_format = row.get_str("extraction_method"), document.get_str("format")
            needed = FORMAT_BY_EXTRACTION.get(method or "")
            if needed is not None and doc_format is not None and doc_format != needed:
                reporter.error(
                    shown,
                    line,
                    "R-67",
                    f"extraction_method {method!r} needs a {needed!r} document, "
                    f"but {document.raw['document_id']!r} is {doc_format!r}",
                )
            source_url = row.get_str("source_url")
            if source_url is not None and source_url != document.get_str("source_url"):
                reporter.error(
                    shown,
                    line,
                    "R-68",
                    f"source_url differs from the source_url of document "
                    f"{document.raw['document_id']!r}",
                )
        problem = _check_poll_id(row)
        if problem:
            reporter.error(shown, line, "R-70", problem)
    for key, rows in surveys.items():
        if any(row.get_bool("headline") is None for row in rows):
            continue
        headlines = sum(1 for row in rows if row.get_bool("headline"))
        if headlines != 1:
            reporter.error(
                shown,
                rows[0].line,
                "R-63",
                f"survey (document_id, election_id, fieldwork_start, fieldwork_end) = "
                f"({', '.join(key)}) has {headlines} headline polls; exactly one is required",
            )


def check_manifest(data_file: DataFile, reporter: Reporter) -> None:
    """R-71 and R-72."""
    shown = data_file.display_path
    pattern = re.compile(rf"^{re.escape(data_file.directory_id or '')}-doc-\d{{3,}}$")
    hashes: dict[str, int] = {}
    for row in data_file.rows:
        if data_file.location is Location.POLL and row.is_empty("archive_url"):
            reporter.error(shown, row.line, "R-71", "archive_url is required in poll manifests")
        document_id = row.get_str("document_id")
        if document_id is not None and not pattern.match(document_id):
            reporter.error(
                shown,
                row.line,
                "R-71",
                f"document_id {document_id!r} must be '{data_file.directory_id}-doc-NNN'",
            )
        sha256 = row.get_str("sha256")
        if sha256 is not None:
            if sha256 in hashes:
                reporter.warning(
                    shown,
                    row.line,
                    "R-72",
                    f"same sha256 as line {hashes[sha256]} (same file archived twice?)",
                )
            else:
                hashes[sha256] = row.line


def run(dataset: Dataset, reporter: Reporter) -> None:
    entity_types = {
        entity_id: row.get_str("entity_type")
        for entity_id, row in dataset.registry_index(ENTITIES.name, "entity_id").items()
    }
    election_types = {
        election_id: row.get_str("election_type")
        for election_id, row in dataset.registry_index(ELECTIONS.name, "election_id").items()
    }
    for files in dataset.polls.values():
        polls_file = files.get(POLLS.name)
        results_file = files.get(POLL_RESULTS.name)
        manifest_file = files.get(ARCHIVE_MANIFEST.name)
        if results_file is not None:
            check_poll_results(polls_file, results_file, entity_types, election_types, reporter)
        if polls_file is not None:
            check_polls(polls_file, results_file, manifest_file, reporter)
    for files in (*dataset.elections.values(), *dataset.polls.values()):
        manifest_file = files.get(ARCHIVE_MANIFEST.name)
        if manifest_file is not None:
            check_manifest(manifest_file, reporter)
