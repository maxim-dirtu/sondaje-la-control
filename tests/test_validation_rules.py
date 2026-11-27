"""Integrity rules of DATA_MODEL.md §7: each rule has a passing and a failing fixture.

The passing fixtures are ``tests/fixtures/example`` (the fictitious worked example of
DATA_MODEL.md §10, verbatim) and ``tests/fixtures/presidential`` (a fictitious two-round
presidential election). Each failing fixture is a copy of one of them with one small
mutation; the test asserts exactly which (rule, severity) pairs the mutation adds.
"""

import datetime as dt
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import pytest

from conftest import FIXTURE_REFERENCE_DATE, FIXTURES, REPO_ROOT, DataDir, DataDirFactory
from sondaje.validation import Issue, Severity, ValidationConfig, validate

E, W = Severity.ERROR, Severity.WARNING
EXAMPLE, PRESIDENTIAL = "example", "presidential"

ELECTIONS = "registry/elections.csv"
ENTITIES = "registry/entities.csv"
POLLSTERS = "registry/pollsters.csv"
ALIASES = "registry/pollster_aliases.csv"
AFFILIATIONS = "registry/pollster_affiliations.csv"
EX = "elections/parl-2099-cd/"
ENTITY_MAP, RESULTS, TOTALS = EX + "entity_map.csv", EX + "results.csv", EX + "results_totals.csv"
R1, R2 = "elections/pres-2099-r1/", "elections/pres-2099-r2/"
POLLS = "polls/exemplar/polls.csv"
POLL_RESULTS = "polls/exemplar/poll_results.csv"
MANIFEST = "polls/exemplar/archive_manifest.csv"
INVENTORY = "polls/exemplar/inventory.csv"
EXAMPLE_POLL = "exemplar-parl-2099-cd-20990524"
CANDIDATE_SUPPORT_HEADER = (
    b"election_id,candidate_entity_id,party_entity_id,support_type,announced_date,"
    b"source_url,source_type,retrieved_at,verified,notes\n"
)

type Mutation = Callable[[DataDir], None]


def rules(issues: list[Issue]) -> set[tuple[str, Severity]]:
    return {(issue.rule, issue.severity) for issue in issues}


def rename_poll(d: DataDir, old: str, new: str) -> None:
    d.replace_value(POLLS, "poll_id", old, new)
    d.replace_value(POLL_RESULTS, "poll_id", old, new)
    d.replace_value(INVENTORY, "poll_id", old, new)


def update_poll(d: DataDir, line: int, inventory_line: int, **changes: str) -> None:
    """Change a poll and copy its date changes to its inventory row (so R-78 stays quiet)."""
    d.update(POLLS, line, **changes)
    dates = {
        k: v
        for k, v in changes.items()
        if k in ("published_date", "fieldwork_start", "fieldwork_end")
    }
    if dates:
        d.update(INVENTORY, inventory_line, **dates)


def clear_fieldwork(d: DataDir) -> None:
    d.update(POLLS, 2, fieldwork_start="", fieldwork_end="")
    rename_poll(d, EXAMPLE_POLL, "exemplar-parl-2099-cd-20990526")


def second_survey(d: DataDir, poll_id: str) -> None:
    """Add another headline poll of the same pollster and election, from a new document."""
    d.append_copy(MANIFEST, 2, document_id="exemplar-doc-002", sha256="a" * 64)
    d.append_copy(POLLS, 2, poll_id=f"{poll_id}-2", document_id="exemplar-doc-002")
    d.append_copy(
        INVENTORY,
        2,
        publication_url="https://example.org/exemplar/raport-2099-05-b.pdf",
        document_id="exemplar-doc-002",
        poll_id=f"{poll_id}-2",
    )
    d.update(MANIFEST, 3, source_url="https://example.org/exemplar/raport-2099-05-b.pdf")
    d.update(POLLS, 3, source_url="https://example.org/exemplar/raport-2099-05-b.pdf")
    _, rows = d.read(POLL_RESULTS)
    for line in range(2, len(rows) + 2):
        d.append_copy(POLL_RESULTS, line, poll_id=f"{poll_id}-2")


def edit_bytes(rel: str, old: bytes, new: bytes) -> Mutation:
    def mutate(d: DataDir) -> None:
        content = d.read_bytes(rel)
        assert old in content
        d.write_bytes(rel, content.replace(old, new))

    return mutate


def case(name: str, fixture: str, mutate: Mutation, *expected: tuple[str, Severity]) -> object:
    return pytest.param(fixture, mutate, set(expected), id=name)


CASES = [
    # --- 7.1 Files and types ---
    case(
        "R-01-bom",
        EXAMPLE,
        edit_bytes(ALIASES, b"pollster_id,", b"\xef\xbb\xbfpollster_id,"),
        ("R-01", E),
    ),
    case("R-01-crlf", EXAMPLE, edit_bytes(ALIASES, b"\n", b"\r\n"), ("R-01", E)),
    case("R-01-not-utf8", EXAMPLE, edit_bytes(ALIASES, b"news site", b"news\xffsite"), ("R-01", E)),
    case(
        "R-01-line-break-in-field",
        EXAMPLE,
        lambda d: d.update(ALIASES, 2, notes="A\nB"),
        ("R-01", E),
    ),
    case("R-01-no-final-newline", EXAMPLE, edit_bytes(ALIASES, b"site.\n", b"site."), ("R-01", E)),
    case(
        "R-01-malformed-quotes",
        EXAMPLE,
        edit_bytes(ALIASES, b",Variant", b',"Variant"x'),
        ("R-01", E),
    ),
    case("R-02-renamed-column", EXAMPLE, edit_bytes(ALIASES, b"alias,", b"aliases,"), ("R-02", E)),
    case(
        "R-02-reordered-columns",
        EXAMPLE,
        edit_bytes(ALIASES, b"pollster_id,alias,", b"alias,pollster_id,"),
        ("R-02", E),
    ),
    case("R-02-empty-file", EXAMPLE, lambda d: d.write_bytes(ALIASES, b""), ("R-02", E)),
    case(
        "R-03-field-count", EXAMPLE, edit_bytes(ALIASES, b"site.\n", b"site.\nx,y\n"), ("R-03", E)
    ),
    case("R-03-required", EXAMPLE, lambda d: d.update(ENTITIES, 2, short_name=""), ("R-03", E)),
    case("R-03-whitespace", EXAMPLE, lambda d: d.update(ENTITIES, 2, name=" PA"), ("R-03", E)),
    case(
        "R-03-slug",
        EXAMPLE,
        lambda d: d.update(AFFILIATIONS, 2, counterpart_entity_id="Alfa"),
        ("R-03", E),
    ),
    case(
        "R-03-date",
        EXAMPLE,
        lambda d: d.update(ENTITY_MAP, 2, effective_date="2099-02-30"),
        ("R-03", E),
    ),
    case(
        "R-03-partial-date",
        EXAMPLE,
        lambda d: d.update(AFFILIATIONS, 2, period_start="2099-13"),
        ("R-03", E),
    ),
    case("R-03-int", EXAMPLE, lambda d: d.update(POLLS, 2, sample_size="1,100"), ("R-03", E)),
    case("R-03-int-minimum", EXAMPLE, lambda d: d.update(POLLS, 2, sample_size="0"), ("R-03", E)),
    case(
        "R-03-decimal", EXAMPLE, lambda d: d.update(POLL_RESULTS, 2, share_raw="28,0"), ("R-03", E)
    ),
    case(
        "R-03-decimal-maximum",
        EXAMPLE,
        lambda d: d.update(POLL_RESULTS, 2, share_raw="100.5"),
        ("R-03", E),
    ),
    case("R-03-bool", EXAMPLE, lambda d: d.update(POLLS, 2, headline="TRUE"), ("R-03", E)),
    case("R-03-enum", EXAMPLE, lambda d: d.update(POLLS, 2, mode="phone"), ("R-03", E)),
    case(
        "R-03-list-enum",
        EXAMPLE,
        lambda d: d.update(POLLSTERS, 2, typical_modes="cati;cati"),
        ("R-03", E),
    ),
    case("R-03-url", EXAMPLE, lambda d: d.update(POLLSTERS, 2, website="example.org"), ("R-03", E)),
    case("R-03-sha256", EXAMPLE, lambda d: d.update(MANIFEST, 2, sha256="E3B0" * 16), ("R-03", E)),
    case("R-03-hex-color", EXAMPLE, lambda d: d.update(ENTITIES, 2, color="#1f77b4"), ("R-03", E)),
    case("R-03-path", EXAMPLE, lambda d: d.update(MANIFEST, 2, raw_path="raw/x.pdf"), ("R-03", E)),
    case("R-04-duplicate-key", EXAMPLE, lambda d: d.append_copy(ENTITY_MAP, 2), ("R-04", E)),
    case(
        "R-05-unexpected-file",
        EXAMPLE,
        lambda d: d.write_bytes("registry/extra.csv", b"a\n"),
        ("R-05", E),
    ),
    case(
        "R-05-candidate-support-not-presidential",
        EXAMPLE,
        lambda d: d.write_bytes(EX + "candidate_support.csv", CANDIDATE_SUPPORT_HEADER),
        ("R-05", E),
    ),
    case(
        "R-05-poll-directory-incomplete",
        EXAMPLE,
        lambda d: d.write_bytes("polls/nou/.gitkeep", b""),
        ("R-05", E),
    ),
    case(
        "R-05-directory-name",
        EXAMPLE,
        lambda d: d.write_bytes(
            "elections/Parl_2099/results.csv", d.read_bytes(RESULTS).split(b"\n")[0] + b"\n"
        ),
        ("R-05", E),
    ),
    case(
        "R-05-directory-not-registered",
        EXAMPLE,
        lambda d: d.delete(ELECTIONS, 2),
        ("R-05", E),
        ("R-06", E),
    ),
    case(
        "R-05-inventory-missing",
        EXAMPLE,
        lambda d: d.remove(INVENTORY),
        ("R-05", E),
    ),
    case(
        "R-06-entity",
        EXAMPLE,
        lambda d: d.update(AFFILIATIONS, 2, counterpart_entity_id="kappa"),
        ("R-06", E),
    ),
    case(
        "R-06-document",
        EXAMPLE,
        lambda d: d.update(POLLS, 2, document_id="exemplar-doc-002"),
        ("R-06", E),
    ),
    case(
        "R-06-poll",
        EXAMPLE,
        lambda d: d.append_copy(POLL_RESULTS, 2, poll_id="exemplar-parl-2099-cd-20990101"),
        ("R-06", E),
    ),
    case(
        "R-07",
        PRESIDENTIAL,
        lambda d: d.update(R2 + "candidate_support.csv", 2, election_id="pres-2099-r1"),
        ("R-07", E),
    ),
    # --- 7.2 Provenance ---
    case("R-10-verified", EXAMPLE, lambda d: d.update(ENTITIES, 2, verified=""), ("R-10", E)),
    case("R-10-source-url", EXAMPLE, lambda d: d.update(RESULTS, 2, source_url=""), ("R-10", E)),
    case(
        "R-10-retrieved-at", EXAMPLE, lambda d: d.update(MANIFEST, 2, retrieved_at=""), ("R-10", E)
    ),
    case("R-11", EXAMPLE, lambda d: d.update(ALIASES, 2, retrieved_at="2100-01-01"), ("R-11", E)),
    case("R-12", EXAMPLE, lambda d: d.update(POLLS, 2, retrieved_at="2099-05-25"), ("R-12", E)),
    case("R-13", EXAMPLE, lambda d: d.update(ENTITIES, 2, source_type="other"), ("R-13", W)),
    case(
        "R-14",
        EXAMPLE,
        lambda d: d.update(ALIASES, 2, source_type="wikipedia", verified="true"),
        ("R-14", E),
    ),
    case("R-15", EXAMPLE, lambda d: d.update(RESULTS, 2, source_type="media"), ("R-15", W)),
    # --- 7.3 Registries ---
    case("R-20-body", EXAMPLE, lambda d: d.update(ELECTIONS, 2, body="senate"), ("R-20", E)),
    case(
        "R-20-type",
        EXAMPLE,
        lambda d: d.update(ELECTIONS, 2, election_type="european"),
        ("R-20", E),
    ),
    case("R-20-round", PRESIDENTIAL, lambda d: d.update(ELECTIONS, 2, round="2"), ("R-20", E)),
    case(
        "R-21",
        PRESIDENTIAL,
        lambda d: d.update(ELECTIONS, 2, election_date="2099-11-20"),
        ("R-21", E),
        ("R-84", E),
    ),
    case("R-30", EXAMPLE, lambda d: d.append_copy(ENTITIES, 8), ("R-30", E)),
    case(
        "R-31",
        EXAMPLE,
        lambda d: d.append_copy(ALIASES, 2, alias="institutul EXEMPLAR"),
        ("R-31", E),
    ),
    case(
        "R-32", PRESIDENTIAL, lambda d: d.update(AFFILIATIONS, 2, period_end="2099-02"), ("R-32", E)
    ),
    case("R-33", PRESIDENTIAL, lambda d: d.update(ENTITIES, 2, color=""), ("R-33", W)),
    case(
        "R-35-name",
        EXAMPLE,
        lambda d: d.update(AFFILIATIONS, 2, counterpart_name="Partidul Alfa"),
        ("R-35", W),
    ),
    case(
        "R-35-short-name-ignoring-case",
        EXAMPLE,
        lambda d: d.update(AFFILIATIONS, 2, counterpart_name="pa"),
        ("R-35", W),
    ),
    # --- 7.4 Election files ---
    case(
        "R-40-forbidden-target",
        EXAMPLE,
        lambda d: d.update(ENTITY_MAP, 4, result_entity_id="gama"),
        ("R-40", E),
    ),
    case(
        "R-40-missing-target",
        EXAMPLE,
        lambda d: d.update(ENTITY_MAP, 2, result_entity_id=""),
        ("R-40", E),
    ),
    case(
        "R-40-not-alliance",
        EXAMPLE,
        lambda d: d.update(ENTITY_MAP, 2, result_entity_id="alfa"),
        ("R-40", E),
    ),
    case(
        "R-41",
        EXAMPLE,
        lambda d: d.append_copy(ENTITY_MAP, 4, poll_entity_id="omega", relation="not_registered"),
        ("R-41", E),
    ),
    case(
        "R-42",
        PRESIDENTIAL,
        lambda d: d.update(R1 + "candidate_support.csv", 2, party_entity_id="ana-exemplu"),
        ("R-42", E),
    ),
    case("R-43", PRESIDENTIAL, lambda d: add_unknown_candidate(d), ("R-43", W)),
    case("R-44", EXAMPLE, lambda d: d.delete(ENTITY_MAP, 4), ("R-44", E)),
    case(
        "R-40-ran-on-list-of-missing-host",
        EXAMPLE,
        lambda d: add_guest(d, host=""),
        ("R-40", E),
    ),
    case(
        "R-41-ran-on-list-of-host-not-on-ballot",
        EXAMPLE,
        lambda d: (
            d.append_copy(ENTITIES, 2, entity_id="theta", name="Partidul Theta", short_name="PT"),
            add_guest(d, host="theta"),
        ),
        ("R-41", E),
    ),
    case(
        "R-41-ran-on-list-of-guest-on-ballot",
        EXAMPLE,
        lambda d: d.append_copy(
            ENTITY_MAP,
            2,
            poll_entity_id="omega",
            relation="ran_on_list_of",
            result_entity_id="beta",
            effective_date="",
        ),
        ("R-41", E),
    ),
    case(
        "R-45-guest-type",
        EXAMPLE,
        lambda d: add_guest(d, entity_type="candidate"),
        ("R-45", E),
    ),
    case("R-45-host-type", EXAMPLE, lambda d: host_beta_as_independent(d), ("R-45", E)),
    case(
        "R-45-not-a-list-election",
        PRESIDENTIAL,
        lambda d: d.append_copy(
            R1 + "entity_map.csv",
            2,
            poll_entity_id="alfa",
            relation="ran_on_list_of",
            result_entity_id="ion-exemplu",
            effective_date="",
        ),
        ("R-45", E),
    ),
    case(
        "R-46-target-mapped",
        EXAMPLE,
        lambda d: d.update(ENTITY_MAP, 3, relation="merged_into", result_entity_id="delta"),
        ("R-46", E),
        ("R-41", E),
    ),
    case(
        "R-46-without-results",
        EXAMPLE,
        lambda d: (add_guest(d, host="zeta"), d.write(RESULTS, d.read(RESULTS)[0], [])),
        ("R-46", E),
    ),
    case("R-50", EXAMPLE, lambda d: d.delete(RESULTS, 9), ("R-50", E), ("R-53", E)),
    case(
        "R-51-results",
        EXAMPLE,
        lambda d: d.update(RESULTS, 10, votes="2100001"),
        ("R-51", E),
        ("R-53", E),
    ),
    case(
        "R-51-totals", EXAMPLE, lambda d: d.update(TOTALS, 4, invalid_votes="158001"), ("R-51", E)
    ),
    case("R-52", EXAMPLE, lambda d: d.update(ENTITIES, 8, entity_type="candidate"), ("R-52", E)),
    case("R-53", EXAMPLE, lambda d: bump_valid_votes(d), ("R-53", E)),
    case("R-53-missing-totals", EXAMPLE, lambda d: d.remove(TOTALS), ("R-53", E)),
    case("R-54", EXAMPLE, lambda d: raise_invalid_votes(d), ("R-54", W)),
    case("R-55", EXAMPLE, lambda d: d.update(TOTALS, 2, registered_voters="4000000"), ("R-55", W)),
    # --- 7.5 Poll files ---
    case("R-60-gap", EXAMPLE, lambda d: d.update(POLL_RESULTS, 9, option_order="9"), ("R-60", E)),
    case(
        "R-60-poll-without-results",
        PRESIDENTIAL,
        lambda d: d.delete(POLL_RESULTS, 13, 14),
        ("R-60", E),
    ),
    case(
        "R-61-entity-required",
        EXAMPLE,
        lambda d: d.update(POLL_RESULTS, 7, option_type="party"),
        ("R-61", E),
    ),
    case(
        "R-61-entity-forbidden",
        EXAMPLE,
        lambda d: d.update(POLL_RESULTS, 8, entity_id="omega"),
        ("R-61", E),
    ),
    case(
        "R-61-type-mismatch",
        EXAMPLE,
        lambda d: d.update(POLL_RESULTS, 4, option_type="alliance"),
        ("R-61", E),
    ),
    case(
        "R-61-election-type",
        PRESIDENTIAL,
        lambda d: d.update(POLL_RESULTS, 4, option_type="party", entity_id="alfa"),
        ("R-61", E),
        ("R-44", E),
    ),
    case(
        "R-62-label", EXAMPLE, lambda d: d.update(POLL_RESULTS, 10, entity_id="beta"), ("R-62", E)
    ),
    case(
        "R-62-entity-twice",
        EXAMPLE,
        lambda d: d.update(POLL_RESULTS, 11, option_label="Partidul Alfa", entity_id="alfa"),
        ("R-62", E),
    ),
    case("R-63-no-headline", EXAMPLE, lambda d: d.update(POLLS, 2, headline="false"), ("R-63", E)),
    case(
        "R-63-two-headlines",
        PRESIDENTIAL,
        lambda d: d.update(POLLS, 3, headline="true"),
        ("R-63", E),
        ("R-93", E),
    ),
    case(
        "R-64-mismatch",
        EXAMPLE,
        lambda d: d.update(POLLS, 2, population_geo="diaspora"),
        ("R-64", E),
    ),
    case(
        "R-64-empty-geo",
        EXAMPLE,
        lambda d: d.update(POLLS, 2, population_geo="", target_scope="total"),
        ("R-64", E),
    ),
    case(
        "R-64-empty-geo-explained",
        EXAMPLE,
        lambda d: d.update(
            POLLS, 2, population_geo="", target_scope="total", notes="Diaspora too."
        ),
        ("R-64", W),
    ),
    case("R-65-missing-sponsor", EXAMPLE, lambda d: d.update(POLLS, 2, sponsor=""), ("R-65", E)),
    case(
        "R-65-undisclosed-with-sponsor",
        EXAMPLE,
        lambda d: d.update(POLLS, 2, sponsor_type="not_disclosed"),
        ("R-65", E),
    ),
    case(
        "R-65-missing-sponsor-source",
        EXAMPLE,
        lambda d: d.update(POLLS, 2, sponsor_source=""),
        ("R-65", E),
    ),
    case(
        "R-65-undisclosed-with-sponsor-source",
        PRESIDENTIAL,
        lambda d: d.update(POLLS, 4, sponsor_source="media", notes="Named by a news site."),
        ("R-65", E),
    ),
    case(
        "R-65-self-needs-sponsor-source",
        EXAMPLE,
        lambda d: d.update(POLLS, 2, sponsor="", sponsor_type="self", sponsor_source=""),
        ("R-65", E),
    ),
    case(
        "R-03-sponsor-source",
        EXAMPLE,
        lambda d: d.update(POLLS, 2, sponsor_source="client"),
        ("R-03", E),
    ),
    case("R-79", EXAMPLE, lambda d: d.update(POLLS, 2, sponsor_source="media"), ("R-79", W)),
    case("R-66-moe", EXAMPLE, lambda d: d.update(POLLS, 2, moe_published="false"), ("R-66", E)),
    case(
        "R-66-sample",
        EXAMPLE,
        lambda d: d.update(POLLS, 2, sample_size_expressed="2000"),
        ("R-66", E),
    ),
    case("R-67", EXAMPLE, lambda d: d.update(POLLS, 2, extraction_method="html"), ("R-67", E)),
    case(
        "R-68",
        EXAMPLE,
        lambda d: d.update(POLLS, 2, source_url="https://example.org/x.pdf"),
        ("R-68", E),
    ),
    case(
        "R-69",
        EXAMPLE,
        lambda d: d.update(POLL_RESULTS, 7, option_type="other_non_vote"),
        ("R-69", W),
    ),
    case(
        "R-70",
        EXAMPLE,
        lambda d: rename_poll(d, EXAMPLE_POLL, "exemplar-parl-2099-cd-20990523"),
        ("R-70", E),
    ),
    case("R-71-archive-url", EXAMPLE, lambda d: d.update(MANIFEST, 2, archive_url=""), ("R-71", E)),
    case("R-71-document-id", EXAMPLE, lambda d: rename_document(d, "exemplar-001"), ("R-71", E)),
    case(
        "R-72",
        EXAMPLE,
        lambda d: d.append_copy(MANIFEST, 2, document_id="exemplar-doc-002"),
        ("R-72", W),
        ("R-76", W),
    ),
    # --- 7.5 Poll inventory ---
    case(
        "R-06-inventory-poll",
        EXAMPLE,
        lambda d: d.update(INVENTORY, 3, poll_id="exemplar-parl-2099-cd-20990101"),
        ("R-06", E),
    ),
    case(
        "R-73-found-with-links",
        EXAMPLE,
        lambda d: d.update(INVENTORY, 2, status="found"),
        ("R-73", E),
        ("R-75", E),
    ),
    case(
        "R-73-archived-with-poll",
        EXAMPLE,
        lambda d: d.update(INVENTORY, 2, status="archived"),
        ("R-73", E),
        ("R-75", E),
    ),
    case(
        "R-73-verified-without-poll",
        EXAMPLE,
        lambda d: d.update(INVENTORY, 2, poll_id=""),
        ("R-73", E),
    ),
    case(
        "R-73-missing-election",
        EXAMPLE,
        lambda d: d.update(INVENTORY, 2, election_id=""),
        ("R-73", E),
    ),
    case(
        "R-73-excluded-without-reason",
        EXAMPLE,
        lambda d: d.update(INVENTORY, 4, exclusion_reason=""),
        ("R-73", E),
    ),
    case(
        "R-73-reason-without-exclusion",
        EXAMPLE,
        lambda d: d.update(INVENTORY, 2, exclusion_reason="duplicate"),
        ("R-73", E),
    ),
    case(
        "R-73-excluded-poll-not-duplicate",
        EXAMPLE,
        lambda d: d.update(INVENTORY, 4, poll_id=EXAMPLE_POLL),
        ("R-73", E),
    ),
    case(
        "R-74-publication-url",
        EXAMPLE,
        lambda d: d.update(INVENTORY, 2, publication_url="https://example.org/x.pdf"),
        ("R-74", E),
    ),
    case(
        "R-74-election",
        PRESIDENTIAL,
        lambda d: d.update(INVENTORY, 2, poll_id="exemplar-pres-2099-r2-20991105"),
        ("R-74", E),
        ("R-78", W),
    ),
    case(
        "R-75",
        EXAMPLE,
        lambda d: d.delete(INVENTORY, 2),
        ("R-75", E),
        ("R-76", W),
    ),
    case(
        "R-76",
        EXAMPLE,
        lambda d: d.append_copy(MANIFEST, 2, document_id="exemplar-doc-002", sha256="a" * 64),
        ("R-76", W),
    ),
    case("R-77", EXAMPLE, lambda d: d.update(INVENTORY, 4, found_via="other"), ("R-77", W)),
    case(
        "R-78", EXAMPLE, lambda d: d.update(INVENTORY, 2, fieldwork_end="2099-05-23"), ("R-78", W)
    ),
    # --- 7.6 Dates ---
    case(
        "R-80", EXAMPLE, lambda d: update_poll(d, 2, 2, fieldwork_start="2099-05-25"), ("R-80", E)
    ),
    case(
        "R-81",
        EXAMPLE,
        lambda d: d.update(ELECTIONS, 2, election_date="2099-05-24"),
        ("R-81", E),
        ("R-83", W),
    ),
    case("R-82", EXAMPLE, lambda d: update_poll(d, 2, 2, published_date="2099-05-23"), ("R-82", E)),
    case(
        "R-83",
        EXAMPLE,
        lambda d: update_poll(d, 2, 2, published_date="2099-06-08", retrieved_at="2099-06-08"),
        ("R-83", W),
    ),
    case(
        "R-84",
        PRESIDENTIAL,
        lambda d: update_poll(d, 4, 3, fieldwork_start="2099-10-30"),
        ("R-84", E),
    ),
    case("R-85", EXAMPLE, lambda d: move_fieldwork_to_2098(d), ("R-85", W)),
    case("R-86", EXAMPLE, clear_fieldwork, ("R-86", W)),
    # --- 7.7 Sums and duplicates ---
    case("R-90", EXAMPLE, lambda d: d.update(POLL_RESULTS, 2, share_raw="20"), ("R-90", E)),
    case(
        "R-90-with-lt",
        PRESIDENTIAL,
        lambda d: d.update(POLL_RESULTS, 6, share_raw="12"),
        ("R-90", E),
    ),
    case("R-91-full", EXAMPLE, lambda d: d.update(POLL_RESULTS, 10, share_raw="50"), ("R-91", E)),
    case(
        "R-91-partial",
        PRESIDENTIAL,
        lambda d: d.update(POLL_RESULTS, 13, share_raw="60"),
        ("R-91", E),
    ),
    case(
        "R-92",
        EXAMPLE,
        lambda d: d.append_copy(
            POLL_RESULTS,
            15,
            option_order="7",
            option_label="Nu știu",
            option_type="undecided",
            entity_id="",
            share_raw="0",
        ),
        ("R-92", W),
    ),
    case("R-93", EXAMPLE, lambda d: second_survey(d, EXAMPLE_POLL), ("R-93", E)),
    case(
        "R-94",
        EXAMPLE,
        lambda d: (clear_fieldwork(d), second_survey(d, "exemplar-parl-2099-cd-20990526")),
        ("R-94", W),
        ("R-86", W),
    ),
    # --- Boundaries that must pass ---
    case(
        "pass-R-90-within-tolerance", EXAMPLE, lambda d: d.update(POLL_RESULTS, 2, share_raw="26")
    ),
    case(
        "pass-R-90-lt-within-tolerance",
        PRESIDENTIAL,
        lambda d: d.update(POLL_RESULTS, 6, share_raw="13"),
    ),
    case(
        "pass-R-91-partial-low-sum",
        PRESIDENTIAL,
        lambda d: d.update(POLL_RESULTS, 13, share_raw="10"),
    ),
    case(
        "pass-R-32-shared-precision",
        PRESIDENTIAL,
        lambda d: d.update(AFFILIATIONS, 2, period_end="2099-03"),
    ),
    case("pass-R-31-other-alias", EXAMPLE, lambda d: d.append_copy(ALIASES, 2, alias="IES")),
    case(
        "pass-R-14-unverified-index",
        EXAMPLE,
        lambda d: d.update(ALIASES, 2, source_type="wikipedia"),
    ),
    case(
        "pass-R-70-suffix",
        EXAMPLE,
        lambda d: rename_poll(d, EXAMPLE_POLL, EXAMPLE_POLL + "-2"),
    ),
    case("pass-R-34-not-checked-without-against", EXAMPLE, lambda d: d.delete(ALIASES, 2)),
    case(
        "pass-R-35-linked",
        EXAMPLE,
        lambda d: d.update(
            AFFILIATIONS, 2, counterpart_name="Partidul Alfa", counterpart_entity_id="alfa"
        ),
    ),
    case("pass-ran-on-list-of", EXAMPLE, lambda d: add_guest(d)),
    case(
        "pass-ran-on-list-of-alliance-host",
        EXAMPLE,
        lambda d: add_guest(d, host="gama"),
    ),
    case("pass-mode-face-to-face", EXAMPLE, lambda d: d.update(POLLS, 2, mode="face_to_face")),
    case(
        "pass-R-79-media-sponsor-cited",
        EXAMPLE,
        lambda d: d.update(
            POLLS, 2, sponsor_source="media", notes="Client named by the outlet (doc-002)."
        ),
    ),
    case(
        "pass-self-sponsor-source",
        EXAMPLE,
        lambda d: d.update(POLLS, 2, sponsor="", sponsor_type="self"),
    ),
    case(
        "pass-typical-modes-face-to-face",
        EXAMPLE,
        lambda d: d.update(POLLSTERS, 2, typical_modes="face_to_face;cati"),
    ),
    case(
        "pass-R-75-scenario-covered-by-document",
        PRESIDENTIAL,
        lambda d: d.update(INVENTORY, 2, poll_id="exemplar-pres-2099-r1-20991025-scenario-b"),
    ),
    case(
        "pass-inventory-found",
        EXAMPLE,
        lambda d: d.append_copy(
            INVENTORY,
            4,
            publication_url="https://example.org/exemplar/nou",
            status="found",
            exclusion_reason="",
        ),
    ),
]


def add_guest(d: DataDir, host: str = "beta", entity_type: str = "party") -> None:
    """Party ``eta`` filed no lists; its candidates ran on the lists of ``host``."""
    d.append_copy(
        ENTITIES, 5, entity_id="eta", entity_type=entity_type, name="Partidul Eta", short_name="PH"
    )
    d.append_copy(
        ENTITY_MAP,
        2,
        poll_entity_id="eta",
        relation="ran_on_list_of",
        result_entity_id=host,
        effective_date="",
    )


def host_beta_as_independent(d: DataDir) -> None:
    """``beta`` becomes an independent (a valid contestant type), then hosts ``eta``."""
    d.update(ENTITIES, 3, entity_type="independent")
    d.update(POLL_RESULTS, 3, option_type="independent")
    d.update(POLL_RESULTS, 11, option_type="independent")
    add_guest(d)


def add_unknown_candidate(d: DataDir) -> None:
    d.append_copy(ENTITIES, 6, entity_id="petre-exemplu", name="Petre Exemplu", short_name="Petre")
    d.append_copy(R1 + "candidate_support.csv", 2, candidate_entity_id="petre-exemplu")


def bump_valid_votes(d: DataDir) -> None:
    d.update(TOTALS, 2, valid_votes="4745001")
    d.update(TOTALS, 4, valid_votes="5200001")


def raise_invalid_votes(d: DataDir) -> None:
    d.update(TOTALS, 2, invalid_votes="160000")
    d.update(TOTALS, 4, invalid_votes="168000")


def rename_document(d: DataDir, document_id: str) -> None:
    d.update(MANIFEST, 2, document_id=document_id)
    d.update(POLLS, 2, document_id=document_id)
    d.update(INVENTORY, 2, document_id=document_id)


def move_fieldwork_to_2098(d: DataDir) -> None:
    update_poll(d, 2, 2, fieldwork_start="2098-05-20", fieldwork_end="2098-05-24")
    rename_poll(d, EXAMPLE_POLL, "exemplar-parl-2099-cd-20980524")


@pytest.fixture(scope="module")
def baselines() -> dict[str, set[tuple[str, Severity]]]:
    config = ValidationConfig(reference_date=FIXTURE_REFERENCE_DATE)
    return {name: rules(validate(FIXTURES / name, config)) for name in (EXAMPLE, PRESIDENTIAL)}


@pytest.mark.parametrize(("fixture", "mutate", "expected"), CASES)
def test_rule(
    fixture_copy: DataDirFactory,
    baselines: dict[str, set[tuple[str, Severity]]],
    fixture: str,
    mutate: Mutation,
    expected: set[tuple[str, Severity]],
) -> None:
    data = fixture_copy(fixture)
    mutate(data)
    issues = data.issues()
    added = rules(issues) - baselines[fixture]
    assert added == expected, "\n".join(issue.format() for issue in issues)


def test_example_fixture_is_valid(fixture_copy: DataDirFactory) -> None:
    """DATA_MODEL.md §10 is valid; its only findings are the two entities without a color."""
    issues = fixture_copy(EXAMPLE).issues()
    assert [(i.rule, i.severity, i.row) for i in issues] == [("R-33", W, 5), ("R-33", W, 6)]


def test_presidential_fixture_is_valid(fixture_copy: DataDirFactory) -> None:
    assert fixture_copy(PRESIDENTIAL).issues() == []


def test_repository_data_has_no_errors() -> None:
    """The real data/ must have no errors; warnings (e.g. R-33) are legitimate there."""
    issues = validate(REPO_ROOT / "data", ValidationConfig(reference_date=dt.date.today()))
    errors = [issue.format() for issue in issues if issue.severity is E]
    assert errors == [], "\n".join(errors)


def test_reference_date_is_injectable(fixture_copy: DataDirFactory) -> None:
    issues = fixture_copy(EXAMPLE).issues(reference_date=dt.date(2099, 6, 19))
    assert {i.rule for i in issues if i.severity is E} == {"R-11"}


def test_tolerance_is_a_parameter() -> None:
    """The expressed_option base of ?10 sums to 101: valid at ?2.0, not at ?0.5."""
    strict = ValidationConfig(FIXTURE_REFERENCE_DATE, share_sum_tolerance_pp=Decimal("0.5"))
    assert ("R-91", E) in rules(validate(FIXTURES / EXAMPLE, strict))


def test_max_poll_age_is_a_parameter() -> None:
    config = ValidationConfig(FIXTURE_REFERENCE_DATE, max_poll_age_days=10)
    assert ("R-85", W) in rules(validate(FIXTURES / EXAMPLE, config))


def test_issue_locations(fixture_copy: DataDirFactory) -> None:
    data = fixture_copy(EXAMPLE)
    data.update(POLLS, 2, published_date="2099-05-23")
    [issue] = [i for i in data.issues() if i.rule == "R-82"]
    assert issue.row == 2
    assert issue.path.endswith("polls/exemplar/polls.csv")
    assert issue.format().endswith(f"polls.csv:2: [R-82] error: {issue.message}")


def test_missing_data_directory(tmp_path: Path) -> None:
    issues = validate(tmp_path / "nope", ValidationConfig(reference_date=dt.date(2099, 1, 1)))
    assert rules(issues) == {("R-05", E)}


FIXTURE_FILES = [
    (name, path.relative_to(FIXTURES / name).as_posix())
    for name in (EXAMPLE, PRESIDENTIAL)
    for path in sorted((FIXTURES / name).rglob("*.csv"))
    if path.read_bytes().count(b"\n") > 1
]


@pytest.mark.parametrize("filler", ["", "x", "-1"])
@pytest.mark.parametrize(("fixture", "rel"), FIXTURE_FILES)
def test_garbage_rows_are_reported_not_fatal(
    fixture_copy: DataDirFactory, fixture: str, rel: str, filler: str
) -> None:
    data = fixture_copy(fixture)
    header, rows = data.read(rel)
    data.write(rel, header, [[filler] * len(header), *rows])
    issues = data.issues()
    assert any(issue.severity is E and issue.path.endswith(rel) for issue in issues)
