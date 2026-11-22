"""Registry rules: R-20, R-21, R-31, R-32, R-33 (R-30 is in rules_files, R-34 in history)."""

import re

from sondaje.schema import ELECTIONS, ENTITIES, POLLSTER_AFFILIATIONS, POLLSTER_ALIASES
from sondaje.validation.model import Dataset, Reporter, Row

TYPE_PREFIXES = {
    "parl": "parliamentary",
    "pres": "presidential",
    "ep": "european",
    "local": "local",
}
PARLIAMENTARY_BODY_PARTS = {"cd": "chamber_of_deputies", "sen": "senate"}
SINGLE_BODY = {"presidential": "president", "european": "european_parliament"}
YEAR_RE = re.compile(r"^\d{4}$")
ROUND_RE = re.compile(r"^r([1-9][0-9]*)$")


def id_round(election_id: str) -> int | None:
    """The ``N`` of a trailing ``-rN`` part, if any."""
    match = ROUND_RE.match(election_id.rsplit("-", 1)[-1])
    return int(match.group(1)) if match else None


def previous_round_id(election_id: str) -> str | None:
    """``x-rN`` → ``x-r(N-1)`` for N ≥ 2; ``None`` otherwise."""
    number = id_round(election_id)
    if number is None or number < 2:
        return None
    return f"{election_id.rsplit('-', 1)[0]}-r{number - 1}"


def election_id_problems(row: Row) -> list[str]:
    """R-20: disagreements between ``election_id`` and the other cells of its row."""
    election_id = row.get_str("election_id")
    if election_id is None:
        return []
    election_type = row.get_str("election_type")
    body = row.get_str("body")
    round_ = row.get_int("round")
    election_date = row.get_date("election_date")
    parts = election_id.split("-")
    expected_type = TYPE_PREFIXES.get(parts[0])
    if expected_type is None:
        return [f"prefix {parts[0]!r} is not one of {', '.join(TYPE_PREFIXES)}"]
    problems = []
    if election_type is not None and election_type != expected_type:
        problems.append(f"prefix {parts[0]!r} needs election_type {expected_type!r}")
    if expected_type == "local" or election_type == "local":
        problems.append("election_type 'local' is reserved until T-062 defines it (§9)")
        return problems
    if len(parts) < 2 or not YEAR_RE.match(parts[1]):
        problems.append("the second part must be the 4-digit year")
        return problems
    if election_date is not None and int(parts[1]) != election_date.year:
        problems.append(f"year {parts[1]} differs from election_date {election_date}")
    rest = parts[2:]
    id_round_number = None
    if rest and (match := ROUND_RE.match(rest[-1])):
        id_round_number = int(match.group(1))
        rest = rest[:-1]
    if expected_type == "parliamentary":
        if not rest or rest[0] not in PARLIAMENTARY_BODY_PARTS:
            problems.append("parliamentary IDs need a -cd or -sen part")
        elif body is not None and body != PARLIAMENTARY_BODY_PARTS[rest[0]]:
            problems.append(f"-{rest[0]} needs body {PARLIAMENTARY_BODY_PARTS[rest[0]]!r}")
        if id_round_number is not None:
            problems.append("parliamentary elections have a single round; drop the -rN part")
    else:
        expected_body = SINGLE_BODY[expected_type]
        if body is not None and body != expected_body:
            problems.append(f"election_type {expected_type!r} needs body {expected_body!r}")
        if expected_type == "presidential" and id_round_number is None:
            problems.append("presidential IDs need a -rN part")
        if expected_type == "european" and id_round_number is not None:
            problems.append("European elections have a single round; drop the -rN part")
    if round_ is not None:
        if id_round_number is not None and round_ != id_round_number:
            problems.append(f"-r{id_round_number} needs round = {id_round_number}")
        if id_round_number is None and round_ != 1:
            problems.append("an ID without -rN needs round = 1")
    return problems


def check_elections(dataset: Dataset, reporter: Reporter) -> None:
    data_file = dataset.registry.get(ELECTIONS.name)
    if data_file is None:
        return
    index = dataset.registry_index(ELECTIONS.name, "election_id")
    for row in data_file.rows:
        for problem in election_id_problems(row):
            reporter.error(data_file.display_path, row.line, "R-20", problem)
        election_id = row.get_str("election_id")
        round_ = row.get_int("round")
        if election_id is None or round_ is None or round_ < 2 or id_round(election_id) != round_:
            continue
        previous_id = previous_round_id(election_id)
        previous = index.get(previous_id) if previous_id else None
        if previous is None:
            reporter.error(
                data_file.display_path, row.line, "R-21", f"previous round {previous_id!r} missing"
            )
            continue
        date, previous_date = row.get_date("election_date"), previous.get_date("election_date")
        if date is not None and previous_date is not None and previous_date >= date:
            reporter.error(
                data_file.display_path,
                row.line,
                "R-21",
                f"election_date {date} is not after round {round_ - 1} ({previous_date})",
            )


def check_aliases(dataset: Dataset, reporter: Reporter) -> None:
    data_file = dataset.registry.get(POLLSTER_ALIASES.name)
    if data_file is None:
        return
    seen: dict[str, Row] = {}
    for row in data_file.rows:
        alias = row.get_str("alias")
        if alias is None:
            continue
        first = seen.setdefault(alias.casefold(), row)
        if first is not row:
            reporter.error(
                data_file.display_path,
                row.line,
                "R-31",
                f"alias {alias!r} is already used on line {first.line} "
                f"(pollster {first.raw['pollster_id']!r}); aliases are unique, ignoring case",
            )


def check_affiliation_periods(dataset: Dataset, reporter: Reporter) -> None:
    data_file = dataset.registry.get(POLLSTER_AFFILIATIONS.name)
    if data_file is None:
        return
    for row in data_file.rows:
        start, end = row.get_partial_date("period_start"), row.get_partial_date("period_end")
        if start is None or end is None:
            continue
        precision = min(len(start), len(end))
        if start[:precision] > end[:precision]:
            reporter.error(
                data_file.display_path,
                row.line,
                "R-32",
                f"period_start {row.raw['period_start']} is after "
                f"period_end {row.raw['period_end']}",
            )


def check_entity_colors(dataset: Dataset, reporter: Reporter) -> None:
    data_file = dataset.registry.get(ENTITIES.name)
    if data_file is None:
        return
    for row in data_file.rows:
        if row.is_empty("color"):
            reporter.warning(
                data_file.display_path,
                row.line,
                "R-33",
                f"entity {row.raw['entity_id']!r} has no color",
            )


def run(dataset: Dataset, reporter: Reporter) -> None:
    check_elections(dataset, reporter)
    check_aliases(dataset, reporter)
    check_affiliation_periods(dataset, reporter)
    check_entity_colors(dataset, reporter)
