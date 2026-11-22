"""Election-file rules: R-40…R-46 and R-50…R-55."""

from collections import defaultdict

from sondaje.schema import (
    CANDIDATE_SUPPORT,
    ELECTIONS,
    ENTITIES,
    ENTITY_MAP,
    POLL_RESULTS,
    POLLS,
    RESULTS,
    RESULTS_TOTALS,
    SCOPES,
)
from sondaje.validation.model import DataFile, Dataset, Reporter, Row

MAPPED_RELATIONS = ("alliance_member", "merged_into", "ran_on_list_of")
"""``entity_map`` relations that need a ``result_entity_id`` (R-40)."""

LIST_ELECTION_TYPES = ("parliamentary", "european")
"""Election types with party lists, where ``ran_on_list_of`` applies (R-45)."""

LIST_ENTITY_TYPES = ("party", "alliance")
"""Entity types that can be the guest or the host of ``ran_on_list_of`` (R-45)."""

CONTESTANT_TYPES = {
    "presidential": ("candidate",),
    "parliamentary": ("party", "alliance", "independent"),
    "european": ("party", "alliance", "independent"),
}
"""Entity types allowed as contestants per election type (R-52, R-61)."""

TOTALS_COLUMNS = ("registered_voters", "voters", "valid_votes", "invalid_votes")


def contestants(dataset: Dataset, election_id: str) -> set[str]:
    return {
        entity_id
        for row in dataset.election_rows(election_id, RESULTS.name)
        if (entity_id := row.get_str("entity_id")) is not None
    }


def mapped_entities(dataset: Dataset, election_id: str) -> set[str]:
    return {
        entity_id
        for row in dataset.election_rows(election_id, ENTITY_MAP.name)
        if (entity_id := row.get_str("poll_entity_id")) is not None
    }


def check_entity_map(
    dataset: Dataset,
    entity_types: dict[str, str | None],
    election_types: dict[str, str | None],
    reporter: Reporter,
) -> None:
    """R-40, R-41, R-45 and R-46."""
    for election_id in dataset.elections:
        data_file = dataset.election_file(election_id, ENTITY_MAP.name)
        if data_file is None:
            continue
        has_results = bool(dataset.election_rows(election_id, RESULTS.name))
        on_ballot = contestants(dataset, election_id)
        mapped = mapped_entities(dataset, election_id)
        for row in data_file.rows:
            shown, line = data_file.display_path, row.line
            relation = row.get_str("relation")
            target = row.get_str("result_entity_id")
            if relation in MAPPED_RELATIONS and row.is_empty("result_entity_id"):
                reporter.error(shown, line, "R-40", f"relation {relation!r} needs result_entity_id")
            elif (
                relation is not None
                and relation not in MAPPED_RELATIONS
                and not row.is_empty("result_entity_id")
            ):
                reporter.error(
                    shown, line, "R-40", f"relation {relation!r} needs an empty result_entity_id"
                )
            target_type = entity_types.get(target) if target else None
            if relation == "alliance_member" and target_type not in (None, "alliance"):
                reporter.error(
                    shown,
                    line,
                    "R-40",
                    f"alliance_member target {target!r} has entity_type {target_type!r}, "
                    "expected 'alliance'",
                )
            if relation == "ran_on_list_of":
                _check_ran_on_list_of(shown, row, entity_types, election_types, reporter)
            if target is not None and target in mapped:
                reporter.error(
                    shown,
                    line,
                    "R-46",
                    f"result_entity_id {target!r} is itself a poll_entity_id in this file; "
                    "map to the ballot contestant directly",
                )
            if not has_results:
                continue
            polled = row.get_str("poll_entity_id")
            if polled is not None and polled in on_ballot:
                reporter.error(
                    shown,
                    line,
                    "R-41",
                    f"poll_entity_id {polled!r} is a contestant in results.csv, "
                    "so it needs no mapping",
                )
            if target is not None and target not in on_ballot:
                reporter.error(
                    shown,
                    line,
                    "R-41",
                    f"result_entity_id {target!r} is not a contestant in results.csv",
                )


def _check_ran_on_list_of(
    shown: str,
    row: Row,
    entity_types: dict[str, str | None],
    election_types: dict[str, str | None],
    reporter: Reporter,
) -> None:
    """R-45: a guest party on a host's lists, in a list election."""
    election_id = row.get_str("election_id")
    election_type = election_types.get(election_id) if election_id else None
    if election_type is not None and election_type not in LIST_ELECTION_TYPES:
        reporter.error(
            shown,
            row.line,
            "R-45",
            f"ran_on_list_of needs a list election, but {election_id!r} is {election_type}",
        )
    for column, role in (("poll_entity_id", "guest"), ("result_entity_id", "host")):
        entity_id = row.get_str(column)
        entity_type = entity_types.get(entity_id) if entity_id else None
        if entity_type is not None and entity_type not in LIST_ENTITY_TYPES:
            reporter.error(
                shown,
                row.line,
                "R-45",
                f"ran_on_list_of {role} {entity_id!r} has entity_type {entity_type!r}, "
                "expected 'party' or 'alliance'",
            )


def check_candidate_support(
    dataset: Dataset,
    entity_types: dict[str, str | None],
    election_types: dict[str, str | None],
    reporter: Reporter,
) -> None:
    """R-42 and R-43."""
    for election_id in dataset.elections:
        data_file = dataset.election_file(election_id, CANDIDATE_SUPPORT.name)
        if data_file is None:
            continue
        has_results = bool(dataset.election_rows(election_id, RESULTS.name))
        known = contestants(dataset, election_id) | mapped_entities(dataset, election_id)
        for row in data_file.rows:
            shown, line = data_file.display_path, row.line
            row_election = row.get_str("election_id")
            election_type = election_types.get(row_election) if row_election else None
            if election_type is not None and election_type != "presidential":
                reporter.error(
                    shown,
                    line,
                    "R-42",
                    f"election {row_election!r} is {election_type}, not presidential",
                )
            candidate = row.get_str("candidate_entity_id")
            if candidate in entity_types and entity_types[candidate] != "candidate":
                reporter.error(
                    shown,
                    line,
                    "R-42",
                    f"candidate_entity_id {candidate!r} has entity_type "
                    f"{entity_types[candidate]!r}, expected 'candidate'",
                )
            party = row.get_str("party_entity_id")
            if party in entity_types and entity_types[party] not in ("party", "alliance"):
                reporter.error(
                    shown,
                    line,
                    "R-42",
                    f"party_entity_id {party!r} has entity_type {entity_types[party]!r}, "
                    "expected 'party' or 'alliance'",
                )
            if has_results and candidate is not None and candidate not in known:
                reporter.warning(
                    shown,
                    line,
                    "R-43",
                    f"candidate {candidate!r} is neither in results.csv nor in entity_map.csv",
                )


def check_poll_entities(dataset: Dataset, reporter: Reporter) -> None:
    """R-44: every entity in a poll for election E is on E's ballot or mapped in E's entity_map."""
    resolvable: dict[str, set[str] | None] = {}
    for files in dataset.polls.values():
        polls_file, results_file = files.get(POLLS.name), files.get(POLL_RESULTS.name)
        if polls_file is None or results_file is None:
            continue
        poll_elections = {
            poll_id: row.get_str("election_id")
            for row in polls_file.rows
            if (poll_id := row.get_str("poll_id")) is not None
        }
        for row in results_file.rows:
            entity_id = row.get_str("entity_id")
            poll_id = row.get_str("poll_id")
            election_id = poll_elections.get(poll_id) if poll_id else None
            if entity_id is None or election_id is None:
                continue
            if election_id not in resolvable:
                on_ballot = contestants(dataset, election_id)
                resolvable[election_id] = (
                    on_ballot | mapped_entities(dataset, election_id) if on_ballot else None
                )
            allowed = resolvable[election_id]
            if allowed is not None and entity_id not in allowed:
                reporter.error(
                    results_file.display_path,
                    row.line,
                    "R-44",
                    f"entity_id {entity_id!r} is neither a contestant in results.csv of "
                    f"{election_id!r} nor a poll_entity_id in its entity_map.csv",
                )


def _by_scope(rows: list[Row]) -> dict[str, Row]:
    scoped: dict[str, Row] = {}
    for row in rows:
        scope = row.get_str("scope")
        if scope is not None:
            scoped.setdefault(scope, row)
    return scoped


def check_results(
    dataset: Dataset,
    entity_types: dict[str, str | None],
    election_types: dict[str, str | None],
    reporter: Reporter,
) -> None:
    """R-50…R-55."""
    for election_id in dataset.elections:
        results = dataset.election_file(election_id, RESULTS.name)
        totals = dataset.election_file(election_id, RESULTS_TOTALS.name)
        result_rows = results.rows if results else []
        totals_by_scope = _by_scope(totals.rows) if totals else {}
        election_type = election_types.get(election_id)
        if results is not None:
            per_entity: dict[str, list[Row]] = defaultdict(list)
            for row in result_rows:
                entity_id = row.get_str("entity_id")
                if entity_id is not None:
                    per_entity[entity_id].append(row)
            for entity_id, rows in per_entity.items():
                scoped = _by_scope(rows)
                missing = [scope for scope in SCOPES if scope not in scoped]
                if missing:
                    reporter.error(
                        results.display_path,
                        rows[0].line,
                        "R-50",
                        f"contestant {entity_id!r} has no row for scope(s) {', '.join(missing)}",
                    )
                else:
                    _check_scope_sum(results.display_path, scoped, "votes", entity_id, reporter)
                allowed = CONTESTANT_TYPES.get(election_type or "")
                entity_type = entity_types.get(entity_id)
                if allowed and entity_type is not None and entity_type not in allowed:
                    reporter.error(
                        results.display_path,
                        rows[0].line,
                        "R-52",
                        f"contestant {entity_id!r} has entity_type {entity_type!r}; "
                        f"a {election_type} election allows {', '.join(allowed)}",
                    )
        if totals is not None and all(scope in totals_by_scope for scope in SCOPES):
            for column in TOTALS_COLUMNS:
                _check_scope_sum(totals.display_path, totals_by_scope, column, None, reporter)
        if results is not None and results.rows:
            _check_valid_votes(results, totals, totals_by_scope, reporter)
        for row in totals.rows if totals else []:
            _check_turnout(totals.display_path, row, reporter)


def _check_scope_sum(
    shown: str, scoped: dict[str, Row], column: str, entity_id: str | None, reporter: Reporter
) -> None:
    """R-51: domestic + diaspora = total, when all three cells are set."""
    domestic, diaspora, total = (scoped[scope].get_int(column) for scope in SCOPES)
    if domestic is None or diaspora is None or total is None:
        return
    if domestic + diaspora != total:
        subject = f"contestant {entity_id!r}" if entity_id else column
        reporter.error(
            shown,
            scoped["total"].line,
            "R-51",
            f"{subject}: domestic {domestic} + diaspora {diaspora} = {domestic + diaspora}, "
            f"but total is {total}",
        )


def _check_valid_votes(
    results_file: DataFile,
    totals_file: DataFile | None,
    totals_by_scope: dict[str, Row],
    reporter: Reporter,
) -> None:
    """R-53: per scope, the sum of votes equals valid_votes."""
    for scope in SCOPES:
        rows = [row for row in results_file.rows if row.get_str("scope") == scope]
        votes = [row.get_int("votes") for row in rows]
        if any(v is None for v in votes):
            continue
        total_row = totals_by_scope.get(scope)
        if total_row is None or totals_file is None:
            reporter.error(
                results_file.display_path,
                None,
                "R-53",
                f"no results_totals.csv row for scope {scope!r} to check valid_votes against",
            )
            continue
        valid_votes = total_row.get_int("valid_votes")
        vote_sum = sum(v for v in votes if v is not None)
        if valid_votes is not None and vote_sum != valid_votes:
            reporter.error(
                totals_file.display_path,
                total_row.line,
                "R-53",
                f"scope {scope!r}: valid_votes is {valid_votes}, "
                f"but the votes in results.csv sum to {vote_sum}",
            )


def _check_turnout(shown: str, row: Row, reporter: Reporter) -> None:
    """R-54 and R-55."""
    voters = row.get_int("voters")
    valid_votes, invalid_votes = row.get_int("valid_votes"), row.get_int("invalid_votes")
    if voters is None:
        return
    if (
        valid_votes is not None
        and invalid_votes is not None
        and valid_votes + invalid_votes > voters
    ):
        reporter.warning(
            shown,
            row.line,
            "R-54",
            f"valid_votes + invalid_votes = {valid_votes + invalid_votes} exceeds voters {voters}",
        )
    registered = row.get_int("registered_voters")
    if row.get_str("scope") == "domestic" and registered is not None and voters > registered:
        reporter.warning(
            shown, row.line, "R-55", f"voters {voters} exceeds registered_voters {registered}"
        )


def run(dataset: Dataset, reporter: Reporter) -> None:
    entity_types = {
        entity_id: row.get_str("entity_type")
        for entity_id, row in dataset.registry_index(ENTITIES.name, "entity_id").items()
    }
    election_types = {
        election_id: row.get_str("election_type")
        for election_id, row in dataset.registry_index(ELECTIONS.name, "election_id").items()
    }
    check_entity_map(dataset, entity_types, election_types, reporter)
    check_candidate_support(dataset, entity_types, election_types, reporter)
    check_poll_entities(dataset, reporter)
    check_results(dataset, entity_types, election_types, reporter)
