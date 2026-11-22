"""Rules on files, keys, and references: R-04, R-05 (directories), R-06, R-07, R-30."""

from sondaje.schema import (
    ARCHIVE_MANIFEST,
    CANDIDATE_SUPPORT,
    ELECTIONS,
    ENTITIES,
    POLLS,
    POLLSTER_ALIASES,
    POLLSTERS,
    REQUIRED_POLL_FILES,
    Location,
    Required,
)
from sondaje.validation.cells import SLUG_RE
from sondaje.validation.loader import display_path
from sondaje.validation.model import DataFile, Dataset, Reporter

ID_REGISTRIES = (ELECTIONS.name, ENTITIES.name, POLLSTERS.name)
"""Registries whose key is a single stable ID; a repeated ID is reported as R-30."""


def election_type_of(dataset: Dataset, election_id: str) -> str | None:
    """The registry ``election_type`` of an election, if registered."""
    row = dataset.registry_index(ELECTIONS.name, "election_id").get(election_id)
    return row.get_str("election_type") if row else None


def check_directories(dataset: Dataset, reporter: Reporter) -> None:
    """R-05: directory names, required poll files, registry IDs, candidate_support placement."""
    elections = dataset.registry_index(ELECTIONS.name, "election_id")
    pollsters = dataset.registry_index(POLLSTERS.name, "pollster_id")
    for location, group, registry, registry_file in (
        (Location.ELECTION, dataset.elections, elections, "registry/elections.csv"),
        (Location.POLL, dataset.polls, pollsters, "registry/pollsters.csv"),
    ):
        for directory_id, files in group.items():
            directory = dataset.root / location / directory_id
            shown = display_path(directory)
            if not SLUG_RE.match(directory_id):
                reporter.error(shown, None, "R-05", f"directory name {directory_id!r} is not an ID")
            if location is Location.POLL:
                for filename in REQUIRED_POLL_FILES:
                    if not (directory / filename).is_file():
                        reporter.error(
                            display_path(directory / filename),
                            None,
                            "R-05",
                            "required file missing",
                        )
            if any(f.has_rows for f in files.values()) and directory_id not in registry:
                reporter.error(
                    shown, None, "R-05", f"{directory_id!r} has data but is not in {registry_file}"
                )
            if location is Location.ELECTION and CANDIDATE_SUPPORT.name in files:
                election_type = election_type_of(dataset, directory_id)
                presidential = (
                    election_type == "presidential"
                    if election_type is not None
                    else directory_id.startswith("pres-")
                )
                if not presidential:
                    reporter.error(
                        files[CANDIDATE_SUPPORT.name].display_path,
                        None,
                        "R-05",
                        "candidate_support.csv exists only for presidential elections",
                    )


def check_keys(dataset: Dataset, reporter: Reporter) -> None:
    """R-04 (duplicate keys) and R-30 (ID reuse in the ID registries).

    Duplicate aliases are left to R-31, which is stricter (case-insensitive, all pollsters).
    """
    for data_file in dataset.files():
        table = data_file.table
        if table.name == POLLSTER_ALIASES.name:
            continue
        rule = "R-30" if table.name in ID_REGISTRIES else "R-04"
        required_key = [c for c in table.key if table.column(c).required is Required.YES]
        seen: dict[tuple[str, ...], int] = {}
        for row in data_file.rows:
            if any(row.is_empty(column) for column in required_key):
                continue
            key = tuple(row.raw[column] for column in table.key)
            if key in seen:
                reporter.error(
                    data_file.display_path,
                    row.line,
                    rule,
                    f"duplicate key ({', '.join(table.key)}) = ({', '.join(key)}); "
                    f"first used on line {seen[key]}",
                )
            else:
                seen[key] = row.line


def _local_ids(files: dict[str, DataFile], table: str, column: str) -> set[str]:
    data_file = files.get(table)
    if data_file is None:
        return set()
    return {v for row in data_file.rows if (v := row.get_str(column)) is not None}


def check_references(dataset: Dataset, reporter: Reporter) -> None:
    """R-06: every foreign key resolves (registries globally, polls/manifests per directory)."""
    registry_ids = {
        f"{table}.{column}": set(dataset.registry_index(table, column))
        for table, column in (
            (ELECTIONS.name, "election_id"),
            (ENTITIES.name, "entity_id"),
            (POLLSTERS.name, "pollster_id"),
        )
    }
    local_tables = (POLLS.name, ARCHIVE_MANIFEST.name)
    for data_file in dataset.files():
        siblings: dict[str, DataFile] = {}
        if data_file.location is Location.POLL and data_file.directory_id is not None:
            siblings = dataset.polls.get(data_file.directory_id, {})
        for column in data_file.table.columns:
            if column.references is None:
                continue
            table, key = column.references.split(".")
            if table in local_tables:
                targets = _local_ids(siblings, table, key)
                where = f"{table}.csv in the same directory"
            else:
                targets = registry_ids[column.references]
                where = f"registry/{table}.csv"
            for row in data_file.rows:
                value = row.get_str(column.name)
                if value is not None and value not in targets:
                    reporter.error(
                        data_file.display_path,
                        row.line,
                        "R-06",
                        f"{column.name} {value!r} not found in {where}",
                    )


def check_directory_ids(dataset: Dataset, reporter: Reporter) -> None:
    """R-07: ``election_id`` / ``pollster_id`` of a per-directory file equals the directory name."""
    for data_file in dataset.files():
        if data_file.location is Location.ELECTION:
            column = "election_id"
        elif data_file.table.name == POLLS.name:
            column = "pollster_id"
        else:
            continue
        if column not in data_file.table.header:
            continue
        for row in data_file.rows:
            value = row.get_str(column)
            if value is not None and value != data_file.directory_id:
                reporter.error(
                    data_file.display_path,
                    row.line,
                    "R-07",
                    f"{column} {value!r} differs from the directory name "
                    f"{data_file.directory_id!r}",
                )


def run(dataset: Dataset, reporter: Reporter) -> None:
    check_directories(dataset, reporter)
    check_keys(dataset, reporter)
    check_references(dataset, reporter)
    check_directory_ids(dataset, reporter)
