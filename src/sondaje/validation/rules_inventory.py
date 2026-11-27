"""Poll inventory rules (DATA_MODEL.md §6.13): R-73…R-78."""

from sondaje.schema import ARCHIVE_MANIFEST, INVENTORY, POLLS
from sondaje.validation.model import DataFile, Dataset, Reporter, Row

LINKED_STATUSES = ("extracted", "verified")
"""Statuses whose row produced (or fed) a poll: ``document_id`` and ``poll_id`` are required."""
DATE_COLUMNS = ("fieldwork_start", "fieldwork_end")
"""R-78 compares fieldwork dates only: a later publication of a poll has its own date."""


def _index(data_file: DataFile | None, column: str) -> dict[str, Row]:
    index: dict[str, Row] = {}
    for row in data_file.rows if data_file else []:
        value = row.get_str(column)
        if value is not None:
            index.setdefault(value, row)
    return index


def check_status(inventory: DataFile, reporter: Reporter) -> None:
    """R-73: the status decides which link columns are set; R-77: ``other`` needs notes."""
    shown = inventory.display_path
    for row in inventory.rows:
        status, reason = row.get_str("status"), row.get_str("exclusion_reason")
        problems = []
        if status is not None and status != "excluded" and row.is_empty("election_id"):
            problems.append(f"status {status!r} needs an election_id")
        if status == "found" and not (row.is_empty("document_id") and row.is_empty("poll_id")):
            problems.append("status 'found' needs an empty document_id and poll_id")
        if status == "archived":
            if row.is_empty("document_id"):
                problems.append("status 'archived' needs a document_id")
            if not row.is_empty("poll_id"):
                problems.append("status 'archived' needs an empty poll_id")
        if status in LINKED_STATUSES and (row.is_empty("document_id") or row.is_empty("poll_id")):
            problems.append(f"status {status!r} needs a document_id and a poll_id")
        if status == "excluded":
            if row.is_empty("exclusion_reason"):
                problems.append("status 'excluded' needs an exclusion_reason")
            elif reason != "duplicate" and not row.is_empty("poll_id"):
                problems.append(
                    "an excluded row has a poll_id only for exclusion_reason 'duplicate'"
                )
        elif status is not None and not row.is_empty("exclusion_reason"):
            problems.append(f"exclusion_reason is set, but status is {status!r}")
        for problem in problems:
            reporter.error(shown, row.line, "R-73", problem)
        if (row.get_str("found_via") == "other" or reason == "other") and row.is_empty("notes"):
            reporter.warning(
                shown, row.line, "R-77", "found_via / exclusion_reason 'other' needs notes"
            )


def check_links(
    inventory: DataFile,
    documents: dict[str, Row],
    polls: dict[str, Row],
    reporter: Reporter,
) -> None:
    """R-74 (links agree with the linked rows) and R-78 (dates differ from the poll's)."""
    shown = inventory.display_path
    for row in inventory.rows:
        document = documents.get(row.get_str("document_id") or "")
        url = row.get_str("publication_url")
        if document is not None and url is not None and url != document.get_str("source_url"):
            reporter.error(
                shown,
                row.line,
                "R-74",
                f"publication_url differs from the source_url of document "
                f"{document.raw['document_id']!r}",
            )
        poll = polls.get(row.get_str("poll_id") or "")
        if poll is None:
            continue
        election_id = row.get_str("election_id")
        if election_id is not None and election_id != poll.get_str("election_id"):
            reporter.error(
                shown,
                row.line,
                "R-74",
                f"election_id {election_id!r} differs from the election of poll "
                f"{poll.raw['poll_id']!r} ({poll.raw['election_id']!r})",
            )
        if row.get_str("status") not in LINKED_STATUSES:
            continue
        for column in DATE_COLUMNS:
            mine, theirs = row.get_date(column), poll.get_date(column)
            if mine is not None and theirs is not None and mine != theirs:
                reporter.warning(
                    shown,
                    row.line,
                    "R-78",
                    f"{column} {mine} differs from poll {poll.raw['poll_id']!r} ({theirs})",
                )


def check_coverage(
    inventory: DataFile,
    polls_file: DataFile | None,
    manifest_file: DataFile | None,
    reporter: Reporter,
) -> None:
    """R-75: every poll is covered by the inventory; R-76: every document is listed."""
    linked = [row for row in inventory.rows if row.get_str("status") in LINKED_STATUSES]
    by_poll = {poll_id for row in linked if (poll_id := row.get_str("poll_id")) is not None}
    by_document = {
        (row.raw["document_id"], row.raw["election_id"])
        for row in linked
        if not row.is_empty("document_id")
    }
    for poll in polls_file.rows if polls_file else []:
        poll_id = poll.get_str("poll_id")
        if poll_id is None or poll_id in by_poll:
            continue
        if (poll.raw["document_id"], poll.raw["election_id"]) in by_document:
            continue
        reporter.error(
            polls_file.display_path if polls_file else inventory.display_path,
            poll.line,
            "R-75",
            f"poll {poll_id!r} has no inventory row with status extracted or verified "
            "(by poll_id, or by document_id and election_id)",
        )
    listed = {v for row in inventory.rows if (v := row.get_str("document_id")) is not None}
    for document in manifest_file.rows if manifest_file else []:
        document_id = document.get_str("document_id")
        if document_id is not None and document_id not in listed:
            reporter.warning(
                manifest_file.display_path if manifest_file else inventory.display_path,
                document.line,
                "R-76",
                f"document {document_id!r} is not listed in inventory.csv",
            )


def run(dataset: Dataset, reporter: Reporter) -> None:
    for files in dataset.polls.values():
        inventory = files.get(INVENTORY.name)
        if inventory is None:
            continue
        polls_file = files.get(POLLS.name)
        manifest_file = files.get(ARCHIVE_MANIFEST.name)
        check_status(inventory, reporter)
        check_links(
            inventory,
            _index(manifest_file, "document_id"),
            _index(polls_file, "poll_id"),
            reporter,
        )
        check_coverage(inventory, polls_file, manifest_file, reporter)
