"""Machine-readable schema of the CSV files under ``data/``.

Implements docs/DATA_MODEL.md §3 (column types), §5 (provenance block) and §6
(tables). This module is the single definition used by the validator; the
test suite checks it against the column tables and the §6.14 header lines of
DATA_MODEL.md, and against the header-only files committed under ``data/``.
If this module and DATA_MODEL.md disagree, the document wins (AGENTS.md §3).
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

SCHEMA_VERSION = "1.3"
"""DATA_MODEL.md schema version implemented here."""


class ColumnType(StrEnum):
    """Column types of DATA_MODEL.md §3.2."""

    SLUG = "slug"
    DATE = "date"
    PARTIAL_DATE = "partial_date"
    INT = "int"
    DECIMAL = "decimal"
    BOOL = "bool"
    ENUM = "enum"
    URL = "url"
    SHA256 = "sha256"
    HEX_COLOR = "hex_color"
    PATH = "path"
    TEXT = "text"
    LIST_ENUM = "list<enum>"


class Required(StrEnum):
    """The *Req* flag of DATA_MODEL.md §3.3."""

    YES = "yes"
    NO = "no"
    COND = "cond"


class Location(StrEnum):
    """Where a table's files live under ``data/`` (DATA_MODEL.md §2.1)."""

    REGISTRY = "registry"
    ELECTION = "elections"
    POLL = "polls"


@dataclass(frozen=True)
class Column:
    """One CSV column.

    ``references`` names the referenced key as ``"<table>.<column>"``. References
    to ``polls`` and ``archive_manifest`` resolve within the same directory;
    all other references resolve against the registries.
    """

    name: str
    type: ColumnType
    required: Required
    values: tuple[str, ...] = ()
    min_value: Decimal | None = None
    max_value: Decimal | None = None
    references: str | None = None


@dataclass(frozen=True)
class Table:
    """One CSV file kind: its name, file name, locations, columns, and key."""

    name: str
    filename: str
    locations: tuple[Location, ...]
    columns: tuple[Column, ...]
    key: tuple[str, ...]
    section: str
    append_only: bool = False

    @property
    def header(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.columns)

    def column(self, name: str) -> Column:
        for column in self.columns:
            if column.name == name:
                return column
        raise KeyError(name)


# --- Enum values (DATA_MODEL.md §5.1, §6) ---------------------------------------------------

SOURCE_TYPES = ("official", "pollster", "media", "wikipedia", "aggregator", "other")
ELECTION_TYPES = ("parliamentary", "presidential", "european", "local")
BODIES = ("chamber_of_deputies", "senate", "president", "european_parliament")
ELECTION_STATUSES = ("held", "annulled", "scheduled")
ENTITY_TYPES = ("party", "alliance", "candidate", "independent")
MODES = ("cati", "cawi", "capi", "papi", "face_to_face", "mixed", "other")
AFFILIATION_RELATIONS = ("client", "owner", "personnel", "other")
ENTITY_MAP_RELATIONS = (
    "alliance_member",
    "merged_into",
    "ran_on_list_of",
    "withdrawn",
    "excluded",
    "not_registered",
)
SUPPORT_TYPES = ("nominated", "endorsed")
SCOPES = ("domestic", "diaspora", "total")
DOCUMENT_FORMATS = ("pdf_text", "pdf_image", "html", "image", "csv", "xlsx", "json", "zip", "other")
POPULATIONS = ("adults", "likely_voters", "other")
POPULATION_GEOS = ("residents", "residents_and_diaspora", "diaspora")
QUESTION_TYPES = ("prompted_list", "open", "other")
SPONSOR_TYPES = (
    "self",
    "media",
    "party",
    "candidate",
    "public_institution",
    "civil_society",
    "business",
    "other",
    "not_disclosed",
)
SPONSOR_SOURCES = ("pollster", "media")
TOPLINE_COVERAGES = ("full", "partial")
EXTRACTION_METHODS = ("pdf_text", "html", "manual_double_entry")
SHARE_BASES = ("all_respondents", "expressed_option", "likely_voters", "other_subset")
NAMED_OPTION_TYPES = ("party", "alliance", "candidate", "independent")
"""Option types that name a registry entity (``entity_id`` required, R-61)."""
VOTE_OPTION_TYPES = (*NAMED_OPTION_TYPES, "other")
"""Option types that count as a vote option in M-1.1 (DATA_MODEL.md §6.12)."""
NON_VOTE_OPTION_TYPES = (
    "undecided",
    "non_response",
    "undecided_or_non_response",
    "would_not_vote",
    "none",
    "blank_or_invalid",
    "other_non_vote",
)
OPTION_TYPES = (*VOTE_OPTION_TYPES, *NON_VOTE_OPTION_TYPES)
SHARE_QUALIFIERS = ("lt",)
INVENTORY_STATUSES = ("found", "archived", "extracted", "verified", "excluded")
FOUND_VIA = ("index", "pollster_site", "partner_outlet", "web_search", "reference", "other")
EXCLUSION_REASONS = (
    "out_of_window",
    "out_of_scope",
    "exit_poll",
    "duplicate",
    "no_topline",
    "unavailable",
    "other",
)


# --- Column helpers --------------------------------------------------------------------------


def _col(
    name: str,
    type_: ColumnType,
    required: Required = Required.YES,
    values: tuple[str, ...] = (),
    *,
    min_value: int | None = None,
    max_value: int | None = None,
    references: str | None = None,
) -> Column:
    return Column(
        name=name,
        type=type_,
        required=required,
        values=values,
        min_value=None if min_value is None else Decimal(min_value),
        max_value=None if max_value is None else Decimal(max_value),
        references=references,
    )


T = ColumnType
YES, NO, COND = Required.YES, Required.NO, Required.COND

ELECTION_REF = "elections.election_id"
ENTITY_REF = "entities.entity_id"
POLLSTER_REF = "pollsters.pollster_id"

SOURCE_URL = _col("source_url", T.URL)
SOURCE_TYPE = _col("source_type", T.ENUM, YES, SOURCE_TYPES)
RETRIEVED_AT = _col("retrieved_at", T.DATE)
VERIFIED = _col("verified", T.BOOL)
NOTES = _col("notes", T.TEXT, NO)

PROVENANCE = (SOURCE_URL, SOURCE_TYPE, RETRIEVED_AT, VERIFIED, NOTES)
"""The provenance block of DATA_MODEL.md §5.1; every table ends with it."""
PROVENANCE_COLUMNS = tuple(column.name for column in PROVENANCE)
MANIFEST_PROVENANCE = (SOURCE_URL, SOURCE_TYPE, RETRIEVED_AT, NOTES)
"""The archive manifest's provenance block: no ``verified`` (DATA_MODEL.md §6.10)."""

_REGISTRY = (Location.REGISTRY,)
_ELECTION = (Location.ELECTION,)
_POLL = (Location.POLL,)


# --- Tables (DATA_MODEL.md §6) ---------------------------------------------------------------

ELECTIONS = Table(
    name="elections",
    filename="elections.csv",
    locations=_REGISTRY,
    section="6.1",
    append_only=True,
    key=("election_id",),
    columns=(
        _col("election_id", T.SLUG),
        _col("election_type", T.ENUM, YES, ELECTION_TYPES),
        _col("body", T.ENUM, YES, BODIES),
        _col("round", T.INT, min_value=1),
        _col("election_date", T.DATE),
        _col("name", T.TEXT),
        _col("status", T.ENUM, YES, ELECTION_STATUSES),
        *PROVENANCE,
    ),
)

ENTITIES = Table(
    name="entities",
    filename="entities.csv",
    locations=_REGISTRY,
    section="6.2",
    append_only=True,
    key=("entity_id",),
    columns=(
        _col("entity_id", T.SLUG),
        _col("entity_type", T.ENUM, YES, ENTITY_TYPES),
        _col("name", T.TEXT),
        _col("short_name", T.TEXT),
        _col("color", T.HEX_COLOR, NO),
        *PROVENANCE,
    ),
)

POLLSTERS = Table(
    name="pollsters",
    filename="pollsters.csv",
    locations=_REGISTRY,
    section="6.3",
    append_only=True,
    key=("pollster_id",),
    columns=(
        _col("pollster_id", T.SLUG),
        _col("name", T.TEXT),
        _col("short_name", T.TEXT),
        _col("website", T.URL, NO),
        _col("typical_modes", T.LIST_ENUM, NO, MODES),
        *PROVENANCE,
    ),
)

POLLSTER_ALIASES = Table(
    name="pollster_aliases",
    filename="pollster_aliases.csv",
    locations=_REGISTRY,
    section="6.4",
    append_only=True,
    key=("pollster_id", "alias"),
    columns=(
        _col("pollster_id", T.SLUG, references=POLLSTER_REF),
        _col("alias", T.TEXT),
        *PROVENANCE,
    ),
)

POLLSTER_AFFILIATIONS = Table(
    name="pollster_affiliations",
    filename="pollster_affiliations.csv",
    locations=_REGISTRY,
    section="6.5",
    append_only=True,
    key=("pollster_id", "relation", "counterpart_name", "period_start"),
    columns=(
        _col("pollster_id", T.SLUG, references=POLLSTER_REF),
        _col("relation", T.ENUM, YES, AFFILIATION_RELATIONS),
        _col("counterpart_name", T.TEXT),
        _col("counterpart_entity_id", T.SLUG, NO, references=ENTITY_REF),
        _col("period_start", T.PARTIAL_DATE, NO),
        _col("period_end", T.PARTIAL_DATE, NO),
        _col("description", T.TEXT),
        *PROVENANCE,
    ),
)

ENTITY_MAP = Table(
    name="entity_map",
    filename="entity_map.csv",
    locations=_ELECTION,
    section="6.6",
    append_only=True,
    key=("election_id", "poll_entity_id"),
    columns=(
        _col("election_id", T.SLUG, references=ELECTION_REF),
        _col("poll_entity_id", T.SLUG, references=ENTITY_REF),
        _col("relation", T.ENUM, YES, ENTITY_MAP_RELATIONS),
        _col("result_entity_id", T.SLUG, COND, references=ENTITY_REF),
        _col("effective_date", T.DATE, NO),
        *PROVENANCE,
    ),
)

CANDIDATE_SUPPORT = Table(
    name="candidate_support",
    filename="candidate_support.csv",
    locations=_ELECTION,
    section="6.7",
    key=("election_id", "candidate_entity_id", "party_entity_id", "support_type"),
    columns=(
        _col("election_id", T.SLUG, references=ELECTION_REF),
        _col("candidate_entity_id", T.SLUG, references=ENTITY_REF),
        _col("party_entity_id", T.SLUG, references=ENTITY_REF),
        _col("support_type", T.ENUM, YES, SUPPORT_TYPES),
        _col("announced_date", T.DATE, NO),
        *PROVENANCE,
    ),
)

RESULTS = Table(
    name="results",
    filename="results.csv",
    locations=_ELECTION,
    section="6.8",
    key=("election_id", "scope", "entity_id"),
    columns=(
        _col("election_id", T.SLUG, references=ELECTION_REF),
        _col("scope", T.ENUM, YES, SCOPES),
        _col("entity_id", T.SLUG, references=ENTITY_REF),
        _col("votes", T.INT, min_value=0),
        *PROVENANCE,
    ),
)

RESULTS_TOTALS = Table(
    name="results_totals",
    filename="results_totals.csv",
    locations=_ELECTION,
    section="6.9",
    key=("election_id", "scope"),
    columns=(
        _col("election_id", T.SLUG, references=ELECTION_REF),
        _col("scope", T.ENUM, YES, SCOPES),
        _col("registered_voters", T.INT, NO, min_value=0),
        _col("voters", T.INT, NO, min_value=0),
        _col("valid_votes", T.INT, min_value=0),
        _col("invalid_votes", T.INT, NO, min_value=0),
        *PROVENANCE,
    ),
)

ARCHIVE_MANIFEST = Table(
    name="archive_manifest",
    filename="archive_manifest.csv",
    locations=(Location.ELECTION, Location.POLL),
    section="6.10",
    key=("document_id",),
    columns=(
        _col("document_id", T.SLUG),
        _col("title", T.TEXT, NO),
        _col("published_date", T.DATE, NO),
        _col("format", T.ENUM, YES, DOCUMENT_FORMATS),
        _col("archive_url", T.URL, COND),
        _col("sha256", T.SHA256),
        _col("raw_path", T.PATH, NO),
        *MANIFEST_PROVENANCE,
    ),
)

POLLS = Table(
    name="polls",
    filename="polls.csv",
    locations=_POLL,
    section="6.11",
    key=("poll_id",),
    columns=(
        _col("poll_id", T.SLUG),
        _col("pollster_id", T.SLUG, references=POLLSTER_REF),
        _col("election_id", T.SLUG, references=ELECTION_REF),
        _col("headline", T.BOOL),
        _col("scenario", T.TEXT, COND),
        _col("fieldwork_start", T.DATE, NO),
        _col("fieldwork_end", T.DATE, NO),
        _col("published_date", T.DATE),
        _col("sample_size", T.INT, NO, min_value=1),
        _col("sample_size_expressed", T.INT, NO, min_value=1),
        _col("mode", T.ENUM, NO, MODES),
        _col("population", T.ENUM, NO, POPULATIONS),
        _col("population_geo", T.ENUM, NO, POPULATION_GEOS),
        _col("target_scope", T.ENUM, YES, SCOPES),
        _col("question_type", T.ENUM, NO, QUESTION_TYPES),
        _col("question_wording", T.TEXT, NO),
        _col("sponsor", T.TEXT, COND),
        _col("sponsor_type", T.ENUM, YES, SPONSOR_TYPES),
        _col("weighting_published", T.BOOL),
        _col("moe_published", T.BOOL),
        _col("margin_of_error", T.DECIMAL, NO),
        _col("topline_coverage", T.ENUM, YES, TOPLINE_COVERAGES),
        _col("document_id", T.SLUG, references="archive_manifest.document_id"),
        _col("extraction_method", T.ENUM, YES, EXTRACTION_METHODS),
        _col("sponsor_source", T.ENUM, COND, SPONSOR_SOURCES),
        *PROVENANCE,
    ),
)

POLL_RESULTS = Table(
    name="poll_results",
    filename="poll_results.csv",
    locations=_POLL,
    section="6.12",
    key=("poll_id", "share_base", "option_order"),
    columns=(
        _col("poll_id", T.SLUG, references="polls.poll_id"),
        _col("share_base", T.ENUM, YES, SHARE_BASES),
        _col("option_order", T.INT, min_value=1),
        _col("option_label", T.TEXT),
        _col("option_type", T.ENUM, YES, OPTION_TYPES),
        _col("entity_id", T.SLUG, COND, references=ENTITY_REF),
        _col("share_raw", T.DECIMAL, min_value=0, max_value=100),
        _col("share_qualifier", T.ENUM, NO, SHARE_QUALIFIERS),
        *PROVENANCE,
    ),
)

INVENTORY = Table(
    name="inventory",
    filename="inventory.csv",
    locations=_POLL,
    section="6.13",
    key=("publication_url", "election_id", "poll_id"),
    columns=(
        _col("publication_url", T.URL),
        _col("election_id", T.SLUG, COND, references=ELECTION_REF),
        _col("title", T.TEXT, NO),
        _col("published_date", T.DATE, NO),
        _col("fieldwork_start", T.DATE, NO),
        _col("fieldwork_end", T.DATE, NO),
        _col("found_via", T.ENUM, YES, FOUND_VIA),
        _col("discovery_url", T.URL, NO),
        _col("status", T.ENUM, YES, INVENTORY_STATUSES),
        _col("exclusion_reason", T.ENUM, COND, EXCLUSION_REASONS),
        _col("document_id", T.SLUG, COND, references="archive_manifest.document_id"),
        _col("poll_id", T.SLUG, COND, references="polls.poll_id"),
        *PROVENANCE,
    ),
)

TABLES: tuple[Table, ...] = (
    ELECTIONS,
    ENTITIES,
    POLLSTERS,
    POLLSTER_ALIASES,
    POLLSTER_AFFILIATIONS,
    ENTITY_MAP,
    CANDIDATE_SUPPORT,
    RESULTS,
    RESULTS_TOTALS,
    ARCHIVE_MANIFEST,
    POLLS,
    POLL_RESULTS,
    INVENTORY,
)
"""Every table of DATA_MODEL.md §6, in document order."""

TABLES_BY_NAME = {table.name: table for table in TABLES}

REQUIRED_POLL_FILES = ("polls.csv", "poll_results.csv", "archive_manifest.csv", "inventory.csv")
"""Files every ``data/polls/<pollster_id>/`` directory must have (R-05)."""


def tables_at(location: Location) -> dict[str, Table]:
    """Return the tables allowed in a location, keyed by file name."""
    return {table.filename: table for table in TABLES if location in table.locations}
