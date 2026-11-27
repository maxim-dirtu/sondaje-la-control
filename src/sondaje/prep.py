"""Data preparation pipeline: canonical CSVs → analysis-ready tables (METHODOLOGY M-1).

Implements METHODOLOGY M-1.1 … M-1.7, with the resolutions of OI-1 … OI-5. One call,
:func:`prepare`, loads ``data/`` through the validation loader and returns a
:class:`Prepared` bundle:

- ``rows``: one row per (poll, compared entity), with the normalized poll share ``s``, the
  result share ``r``, days before the election, recency weight, ``n``, target scope, house,
  and the poll's eligibility flags. The "others" bucket has ``entity_id`` :data:`OTHERS`.
- ``polls``: one row per poll, with the same flags and the exclusion reasons.
- ``adjustments``: every change the pipeline made to a published value (M-1.1 "<x" values
  and partial toplines, M-1.2 merges into "others", M-1.5 mappings), one row each.

Every poll is kept, including the ones excluded from the metrics (scenarios, polls published
after the vote, polls without a fieldwork end), so the UI can show them. Metric code filters
on ``eligible``, ``in_window``, or ``final_poll``. No metric is computed here.
"""

import argparse
import datetime as dt
import io
import logging
import math
import sys
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from sondaje.config import MethodologyConfig
from sondaje.schema import VOTE_OPTION_TYPES
from sondaje.validation.loader import load
from sondaje.validation.model import Dataset, Reporter, Row, Severity

if TYPE_CHECKING:
    from sondaje.cli import Subparsers

logger = logging.getLogger(__name__)

OTHERS = "_others"
"""``entity_id`` of the "others" bucket (M-1.2). Not a valid slug, so it never clashes."""

ALL_RESPONDENTS = "all_respondents"
EXPRESSED_OPTION = "expressed_option"

ADDED_RELATIONS = ("alliance_member", "merged_into", "ran_on_list_of")
"""``entity_map`` relations whose poll share is added to ``result_entity_id`` (M-1.5)."""
DROPPED_RELATIONS = ("withdrawn", "excluded", "not_registered")
"""``entity_map`` relations whose poll share is dropped before renormalization (M-1.5)."""
PRESIDENTIAL = "presidential"

# Exclusion reasons (a poll may have several; they are joined with ";").
NOT_HEADLINE = "not_headline"
"""OI-3 (M-1.3): a non-headline scenario."""
PUBLISHED_AFTER_VOTE = "published_on_or_after_election_day"
"""M-1.7: first published on or after election day."""
NO_FIELDWORK_END = "no_fieldwork_end"
"""OI-4 (M-1.3): ``fieldwork_end`` not published, so the poll has no date ``t``."""
NO_RESULTS = "no_results"
"""The election has no official result for the poll's target scope."""
NO_VOTE_OPTIONS = "no_vote_options"
"""No share base with a vote option is left after M-1.5 (nothing to normalize)."""

# Values of ``n_method`` (OI-5).
N_EXPRESSED = "sample_size_expressed"
N_SCALED = "sample_size_x_expressed_share"
N_SAMPLE = "sample_size"
N_MISSING = "missing"

POLL_COLUMNS: tuple[str, ...] = (
    "poll_id",
    "pollster_id",
    "election_id",
    "unit_id",
    "headline",
    "scenario",
    "fieldwork_start",
    "fieldwork_end",
    "published_date",
    "election_date",
    "days_before",
    "weight",
    "published_after_vote",
    "eligible",
    "in_window",
    "final_poll",
    "exclusion_reason",
    "share_base",
    "target_scope",
    "topline_coverage",
    "has_lt",
    "sample_size",
    "n",
    "n_method",
    "k",
)
"""Columns of :attr:`Prepared.polls`, in order."""

ROW_COLUMNS: tuple[str, ...] = (
    "poll_id",
    "pollster_id",
    "election_id",
    "unit_id",
    "entity_id",
    "supporting_party_id",
    "share_raw",
    "s",
    "r",
    "adjusted",
    "has_lt",
    "fieldwork_end",
    "election_date",
    "days_before",
    "weight",
    "n",
    "n_method",
    "target_scope",
    "share_base",
    "topline_coverage",
    "headline",
    "published_after_vote",
    "eligible",
    "in_window",
    "final_poll",
    "exclusion_reason",
)
"""Columns of :attr:`Prepared.rows`, in order."""

ADJUSTMENT_COLUMNS: tuple[str, ...] = (
    "poll_id",
    "rule",
    "kind",
    "entity_id",
    "target_id",
    "share_raw",
    "detail",
)
"""Columns of :attr:`Prepared.adjustments`, in order."""


class PrepError(Exception):
    """The data cannot be prepared (it does not load, or breaks a rule M-1 relies on)."""


@dataclass(frozen=True)
class Adjustment:
    """One logged change to a published value (M-1.1, M-1.2, M-1.5).

    ``share_raw`` is the value affected, in percentage points of the poll's share base.
    """

    poll_id: str
    rule: str
    kind: str
    entity_id: str | None
    target_id: str | None
    share_raw: float | None
    detail: str


@dataclass(frozen=True)
class Prepared:
    """The output of :func:`prepare`: per-entity rows, per-poll flags, and the adjustment log."""

    rows: pd.DataFrame
    polls: pd.DataFrame
    adjustments: pd.DataFrame
    config: MethodologyConfig


@dataclass
class _Election:
    """What M-1 needs from one election's files."""

    election_id: str
    election_type: str
    election_date: dt.date
    result_shares: dict[str, dict[str, float]] = field(default_factory=dict)
    """scope → contestant → ``r`` in [0, 1] (M-1.4)."""
    mapping: dict[str, tuple[str, str | None]] = field(default_factory=dict)
    """poll entity → (relation, result entity) from ``entity_map.csv`` (M-1.5)."""
    supporters: dict[str, set[str]] = field(default_factory=dict)
    """candidate → supporting parties from ``candidate_support.csv`` (M-1.5, I-016)."""

    @property
    def contestants(self) -> set[str]:
        return {entity for shares in self.result_shares.values() for entity in shares}


# --- Loading --------------------------------------------------------------------------------


def _load(data_dir: Path) -> Dataset:
    reporter = Reporter()
    dataset = load(data_dir, reporter)
    errors = [issue for issue in reporter.issues if issue.severity is Severity.ERROR]
    if errors:
        listed = "\n".join(issue.format() for issue in errors[:20])
        raise PrepError(
            f"{len(errors)} error(s) while loading {data_dir}; run 'sondaje validate':\n{listed}"
        )
    return dataset


def _result_shares(dataset: Dataset, election_id: str) -> dict[str, dict[str, float]]:
    """Result shares per scope: ``r_j = votes_j / valid_votes`` (DATA_MODEL §6.8, M-1.4)."""
    votes: dict[str, dict[str, int]] = defaultdict(dict)
    for row in dataset.election_rows(election_id, "results"):
        scope, entity, count = row.get_str("scope"), row.get_str("entity_id"), row.get_int("votes")
        if scope and entity and count is not None:
            votes[scope][entity] = count
    valid: dict[str, int] = {}
    for row in dataset.election_rows(election_id, "results_totals"):
        scope, count = row.get_str("scope"), row.get_int("valid_votes")
        if scope and count is not None:
            valid[scope] = count
    shares: dict[str, dict[str, float]] = {}
    for scope, by_entity in votes.items():
        denominator = valid.get(scope) or sum(by_entity.values())
        if denominator > 0:
            shares[scope] = {entity: count / denominator for entity, count in by_entity.items()}
    return shares


def _elections(dataset: Dataset) -> dict[str, _Election]:
    elections: dict[str, _Election] = {}
    for row in dataset.registry_rows("elections"):
        election_id, election_date = row.get_str("election_id"), row.get_date("election_date")
        if election_id is None or election_date is None:
            continue
        election = _Election(
            election_id=election_id,
            election_type=row.get_str("election_type") or "",
            election_date=election_date,
            result_shares=_result_shares(dataset, election_id),
        )
        for map_row in dataset.election_rows(election_id, "entity_map"):
            poll_entity, relation = map_row.get_str("poll_entity_id"), map_row.get_str("relation")
            if poll_entity and relation:
                election.mapping[poll_entity] = (relation, map_row.get_str("result_entity_id"))
        for support_row in dataset.election_rows(election_id, "candidate_support"):
            candidate = support_row.get_str("candidate_entity_id")
            party = support_row.get_str("party_entity_id")
            if candidate and party:
                election.supporters.setdefault(candidate, set()).add(party)
        elections[election_id] = election
    return elections


# --- Per-poll rules -------------------------------------------------------------------------


def _value(row: Row, config: MethodologyConfig) -> tuple[float, bool]:
    """Numeric value of a published share, in pp (OI-2 resolution in M-1.1).

    A value published as "<x" (``share_qualifier = lt``) enters as ``x * lt_fraction``.
    """
    share = row.get_decimal("share_raw")
    raw = float(share) if share is not None else 0.0
    if row.get_str("share_qualifier") == "lt":
        return raw * config.lt_fraction, True
    return raw, False


def _is_vote_option(row: Row) -> bool:
    return row.get_str("option_type") in VOTE_OPTION_TYPES


def select_share_base(bases: dict[str, list[Row]], config: MethodologyConfig) -> str | None:
    """The share base used for a poll (OI-1 resolution in M-1.1).

    The first base in ``config.share_base_priority`` that the poll publishes with at least one
    vote option (a named party/candidate or "other").
    """
    for base in config.share_base_priority:
        if any(_is_vote_option(row) for row in bases.get(base, [])):
            return base
    return None


def effective_sample_size(
    poll: Row, bases: dict[str, list[Row]], config: MethodologyConfig
) -> tuple[float, str]:
    """``n``: the number of respondents behind the normalized shares (OI-5 resolution, M-1.1).

    1. ``sample_size_expressed`` when published;
    2. otherwise ``sample_size`` × the share of all respondents who named a vote option, when the
       poll publishes an ``all_respondents`` base ("<x" values per OI-2, capped at 100%);
    3. otherwise ``sample_size`` (an upper bound of the true ``n``);
    4. ``NaN`` when no sample size is published.
    """
    expressed = poll.get_int("sample_size_expressed")
    if expressed is not None:
        return float(expressed), N_EXPRESSED
    size = poll.get_int("sample_size")
    if size is None:
        return math.nan, N_MISSING
    vote_share = sum(
        _value(row, config)[0] for row in bases.get(ALL_RESPONDENTS, []) if _is_vote_option(row)
    )
    if vote_share > 0:
        return size * min(vote_share, 100.0) / 100.0, N_SCALED
    return float(size), N_SAMPLE


def recency_weight(days_before: int | None, config: MethodologyConfig) -> float:
    """``w = exp(−days_before_election / τ)`` (M-1.3); ``NaN`` when the date is unknown."""
    if days_before is None:
        return math.nan
    return math.exp(-days_before / config.tau)


def supporting_party(election: _Election, entity_id: str) -> str | None:
    """The party a presidential candidate's lean is attributed to (M-1.5, I-016).

    The single party or alliance that nominated or endorsed the candidate; ``None`` when there
    are none or several (the error then stays with the candidate), and outside presidential
    elections.
    """
    if election.election_type != PRESIDENTIAL:
        return None
    parties = election.supporters.get(entity_id, set())
    return next(iter(parties)) if len(parties) == 1 else None


@dataclass
class _PollOutcome:
    record: dict[str, object]
    rows: list[dict[str, object]]
    adjustments: list[Adjustment]


def _exclusion_reasons(poll: Row, election: _Election) -> list[str]:
    """Reasons a poll is kept out of every metric (OI-3, OI-4, M-1.7)."""
    reasons = []
    if poll.get_bool("headline") is False:
        reasons.append(NOT_HEADLINE)
    published = poll.get_date("published_date")
    if published is not None and published >= election.election_date:
        reasons.append(PUBLISHED_AFTER_VOTE)
    if poll.get_date("fieldwork_end") is None:
        reasons.append(NO_FIELDWORK_END)
    return reasons


def _prepare_poll(
    poll: Row, bases: dict[str, list[Row]], election: _Election, config: MethodologyConfig
) -> _PollOutcome:
    poll_id = poll.get_str("poll_id") or ""
    pollster_id = poll.get_str("pollster_id") or ""
    scope = poll.get_str("target_scope") or ""
    coverage = poll.get_str("topline_coverage") or ""
    fieldwork_end = poll.get_date("fieldwork_end")
    days_before = (election.election_date - fieldwork_end).days if fieldwork_end else None
    reasons = _exclusion_reasons(poll, election)
    n, n_method = effective_sample_size(poll, bases, config)
    base = select_share_base(bases, config)
    adjustments: list[Adjustment] = []

    def adjust(
        rule: str,
        kind: str,
        entity: str | None,
        target: str | None,
        share: float | None,
        detail: str,
    ) -> None:
        adjustments.append(Adjustment(poll_id, rule, kind, entity, target, share, detail))

    record: dict[str, object] = {
        "poll_id": poll_id,
        "pollster_id": pollster_id,
        "election_id": election.election_id,
        "unit_id": f"{pollster_id}:{election.election_id}",
        "headline": poll.get_bool("headline"),
        "scenario": poll.get_str("scenario"),
        "fieldwork_start": poll.get_date("fieldwork_start"),
        "fieldwork_end": fieldwork_end,
        "published_date": poll.get_date("published_date"),
        "election_date": election.election_date,
        "days_before": days_before,
        "weight": recency_weight(days_before, config),
        "published_after_vote": PUBLISHED_AFTER_VOTE in reasons,
        "share_base": base,
        "target_scope": scope,
        "topline_coverage": coverage,
        "has_lt": False,
        "sample_size": poll.get_int("sample_size"),
        "n": n,
        "n_method": n_method,
        "k": 0,
    }
    result = election.result_shares.get(scope)
    if not result:
        reasons.append(NO_RESULTS)
    if base is None:
        reasons.append(NO_VOTE_OPTIONS)
    if not result or base is None:
        record["exclusion_reason"] = ";".join(reasons)
        return _PollOutcome(record, [], adjustments)

    # M-1.5 (mapping) and OI-2 ("<x" values), on the vote options of the chosen base (OI-1).
    values: dict[str, float] = defaultdict(float)
    adjusted: set[str] = set()
    lt_entities: set[str] = set()
    others = 0.0
    published_total = 0.0
    contestants = election.contestants
    for row in sorted(bases[base], key=lambda r: r.get_int("option_order") or 0):
        if not _is_vote_option(row):
            continue
        value, is_lt = _value(row, config)
        published_total += value
        entity = row.get_str("entity_id")
        if is_lt:
            record["has_lt"] = True
            adjust(
                "M-1.1",
                "lt_value",
                entity,
                None,
                value,
                f"published as <{row.raw['share_raw']}; enters as {value:g} "
                f"(lt_fraction {config.lt_fraction:g})",
            )
        if entity is None:  # option_type "other"
            others += value
            if is_lt:
                lt_entities.add(OTHERS)
            continue
        if entity in contestants:
            target = entity
        elif entity in election.mapping:
            relation, mapped_to = election.mapping[entity]
            if relation in DROPPED_RELATIONS or mapped_to is None:
                adjust(
                    "M-1.5",
                    relation,
                    entity,
                    None,
                    value,
                    f"{relation}: share dropped; the other shares are renormalized",
                )
                continue
            target = mapped_to
            adjusted.add(target)
            adjust("M-1.5", relation, entity, target, value, f"{relation}: share added to {target}")
        else:
            raise PrepError(
                f"{poll_id}: entity {entity!r} is neither a contestant of {election.election_id} "
                "nor mapped in its entity_map.csv (R-44)"
            )
        values[target] += value
        if is_lt:
            lt_entities.add(target)

    # Partial topline on the expressed base: the unpublished remainder goes to "others" (M-1.1).
    if coverage == "partial" and base == EXPRESSED_OPTION and published_total < 100.0:
        residual = 100.0 - published_total
        others += residual
        adjusted.add(OTHERS)
        adjust(
            "M-1.1",
            "partial_residual",
            None,
            OTHERS,
            residual,
            f"partial topline: unpublished remainder {residual:g} pp added to others",
        )

    # M-1.2: comparison set, and merges into "others" below the threshold.
    compared: dict[str, float] = {}
    for target, value in values.items():
        if result.get(target, 0.0) >= config.small_party_threshold:
            compared[target] = value
            continue
        others += value
        adjusted.add(OTHERS)
        if target in lt_entities:
            lt_entities.add(OTHERS)
        adjust(
            "M-1.2",
            "below_threshold",
            target,
            OTHERS,
            value,
            f"result share {result.get(target, 0.0):.4%} < threshold "
            f"{config.small_party_threshold:.2%}: merged into others",
        )

    # M-1.1: normalization over the compared entities plus "others".
    total = sum(compared.values()) + others
    if total <= 0:
        reasons.append(NO_VOTE_OPTIONS)
        record["exclusion_reason"] = ";".join(reasons)
        return _PollOutcome(record, [], adjustments)
    rows: list[dict[str, object]] = []
    for entity in sorted(compared, key=lambda e: (-result.get(e, 0.0), e)):
        rows.append(
            {
                "poll_id": poll_id,
                "entity_id": entity,
                "supporting_party_id": supporting_party(election, entity),
                "share_raw": compared[entity],
                "s": compared[entity] / total,
                "r": result.get(entity, 0.0),
                "adjusted": entity in adjusted or entity in lt_entities,
                "has_lt": entity in lt_entities,
            }
        )
    r_others = sum(share for entity, share in result.items() if entity not in compared)
    if others > 0 or r_others > 0:
        rows.append(
            {
                "poll_id": poll_id,
                "entity_id": OTHERS,
                "supporting_party_id": None,
                "share_raw": others,
                "s": others / total,
                "r": r_others,
                "adjusted": OTHERS in adjusted or OTHERS in lt_entities,
                "has_lt": OTHERS in lt_entities,
            }
        )
    record["k"] = len(rows)
    record["exclusion_reason"] = ";".join(reasons) or None
    return _PollOutcome(record, rows, adjustments)


# --- Assembly -------------------------------------------------------------------------------


def _mark_windows(polls: pd.DataFrame, config: MethodologyConfig) -> pd.DataFrame:
    """``eligible``, ``in_window``, and ``final_poll`` (M-1.3, M-1.7, OI-3, OI-4).

    ``final_poll``: per (house, election), the in-window eligible poll with the latest
    ``fieldwork_end`` (ties: the later ``published_date``, then the larger ``poll_id``).
    """
    polls = polls.copy()
    polls["eligible"] = polls["exclusion_reason"].isna()
    days = polls["days_before"]
    polls["in_window"] = polls["eligible"] & days.notna() & (days <= config.window_days)
    polls["in_window"] = polls["in_window"].fillna(False).astype(bool)
    polls["final_poll"] = False
    window = polls[polls["in_window"]]
    if not window.empty:
        ordered = window.sort_values(["fieldwork_end", "published_date", "poll_id"])
        finals = ordered.groupby(["pollster_id", "election_id"]).tail(1).index
        polls.loc[finals, "final_poll"] = True
    return polls


def _frame(records: Iterable[dict[str, object]], columns: tuple[str, ...]) -> pd.DataFrame:
    return pd.DataFrame.from_records(list(records), columns=list(columns))


def _typed_polls(polls: pd.DataFrame) -> pd.DataFrame:
    for column in ("fieldwork_start", "fieldwork_end", "published_date", "election_date"):
        polls[column] = pd.to_datetime(polls[column])
    for column in ("days_before", "sample_size", "k"):
        polls[column] = polls[column].astype("Int64")
    for column in ("weight", "n"):
        polls[column] = polls[column].astype(float)
    for column in ("headline", "published_after_vote", "has_lt"):
        polls[column] = polls[column].astype(bool)
    return polls


def prepare(data_dir: Path, config: MethodologyConfig | None = None) -> Prepared:
    """Turn the canonical CSVs under ``data_dir`` into analysis-ready tables (M-1.1 … M-1.7).

    Implements METHODOLOGY M-1.1 (normalization, OI-1 share base, OI-2 "<x" values, partial
    toplines, OI-5 ``n``), M-1.2 (comparison set, "others"), M-1.3 (window, recency weight,
    final poll, OI-3 scenarios, OI-4 missing dates), M-1.4 (target scope), M-1.5 (alliances,
    parties on another party's list, withdrawals and exclusions, rounds, candidate → party),
    M-1.6 (``unit_id`` = house × election), and M-1.7 (polls published on or after election
    day). Every adjustment is returned in :attr:`Prepared.adjustments` and logged at INFO level.

    Raises :class:`PrepError` when the data does not load cleanly, a poll refers to an unknown
    election, or a polled entity is neither a contestant nor mapped (R-44).
    """
    config = config or MethodologyConfig()
    dataset = _load(data_dir)
    elections = _elections(dataset)
    records: list[dict[str, object]] = []
    entity_rows: list[dict[str, object]] = []
    adjustments: list[Adjustment] = []
    for pollster_id in sorted(dataset.polls):
        files = dataset.polls[pollster_id]
        bases_by_poll: dict[str, dict[str, list[Row]]] = defaultdict(lambda: defaultdict(list))
        if "poll_results" in files:
            for row in files["poll_results"].rows:
                poll_id, base = row.get_str("poll_id"), row.get_str("share_base")
                if poll_id and base:
                    bases_by_poll[poll_id][base].append(row)
        poll_file = files.get("polls")
        for poll in poll_file.rows if poll_file else []:
            poll_id, election_id = poll.get_str("poll_id"), poll.get_str("election_id")
            if poll_id is None or election_id is None:
                continue
            election = elections.get(election_id)
            if election is None:
                raise PrepError(f"{poll_id}: unknown election {election_id!r}")
            outcome = _prepare_poll(poll, bases_by_poll.get(poll_id, {}), election, config)
            records.append(outcome.record)
            entity_rows.extend(outcome.rows)
            adjustments.extend(outcome.adjustments)

    for adjustment in adjustments:
        logger.info(
            "%s [%s %s] %s → %s: %s",
            adjustment.poll_id,
            adjustment.rule,
            adjustment.kind,
            adjustment.entity_id,
            adjustment.target_id,
            adjustment.detail,
        )

    poll_frame = _frame(records, tuple(c for c in POLL_COLUMNS if c not in _DERIVED))
    poll_frame = _mark_windows(_typed_polls(poll_frame), config)
    poll_frame = poll_frame.sort_values(["election_id", "pollster_id", "fieldwork_end", "poll_id"])
    poll_frame = poll_frame[list(POLL_COLUMNS)].reset_index(drop=True)

    shared = [c for c in ROW_COLUMNS if c in POLL_COLUMNS and c not in _ROW_OWN_COLUMNS]
    row_frame = _frame(entity_rows, _ROW_OWN_COLUMNS)
    row_frame = row_frame.merge(poll_frame[["poll_id", *shared]], on="poll_id", how="left")
    row_frame["s"] = row_frame["s"].astype(float)
    row_frame["r"] = row_frame["r"].astype(float)
    row_frame["share_raw"] = row_frame["share_raw"].astype(float)
    row_frame = row_frame[list(ROW_COLUMNS)]
    order = {poll_id: i for i, poll_id in enumerate(poll_frame["poll_id"])}
    row_frame = row_frame.sort_values(
        "poll_id", key=lambda ids: ids.map(order), kind="stable"
    ).reset_index(drop=True)

    adjustment_frame = _frame((asdict(a) for a in adjustments), ADJUSTMENT_COLUMNS)
    return Prepared(row_frame, poll_frame, adjustment_frame, config)


_DERIVED = ("eligible", "in_window", "final_poll")
_ROW_OWN_COLUMNS = (
    "poll_id",
    "entity_id",
    "supporting_party_id",
    "share_raw",
    "s",
    "r",
    "adjusted",
    "has_lt",
)


# --- Summary and CLI ------------------------------------------------------------------------


def summarize(prepared: Prepared) -> str:
    """A plain-text summary: per (election, house) counts, excluded polls, adjustments."""
    polls, rows = prepared.polls, prepared.rows
    out = io.StringIO()
    out.write(
        f"{len(polls)} polls, {int(polls['eligible'].sum())} eligible, "
        f"{int(polls['in_window'].sum())} in the {prepared.config.window_days}-day window, "
        f"{int(polls['final_poll'].sum())} final; {len(rows)} rows; "
        f"{len(prepared.adjustments)} adjustments\n\n"
    )
    if not polls.empty:
        row_counts = rows.groupby("poll_id").size()
        per = polls.assign(rows=polls["poll_id"].map(row_counts).fillna(0).astype(int))
        finals = polls[polls["final_poll"]].set_index(["election_id", "pollster_id"])["poll_id"]
        table = per.groupby(["election_id", "pollster_id"]).agg(
            polls=("poll_id", "size"),
            eligible=("eligible", "sum"),
            in_window=("in_window", "sum"),
            rows=("rows", "sum"),
        )
        table["final_poll"] = [finals.get(key, "-") for key in table.index]
        out.write("Per election and house:\n")
        out.write(table.to_string() + "\n\n")
        excluded = polls[~polls["eligible"]][["poll_id", "exclusion_reason"]]
        out.write(f"Excluded from the metrics ({len(excluded)}):\n")
        out.write((excluded.to_string(index=False) if len(excluded) else "(none)") + "\n\n")
    if not prepared.adjustments.empty:
        counts = prepared.adjustments.groupby(["rule", "kind"]).size().rename("count")
        out.write("Adjustments:\n" + counts.to_string() + "\n")
    return out.getvalue()


def register(subparsers: "Subparsers") -> None:
    parser = subparsers.add_parser(
        "prep",
        help="Prepare the analysis table from data/ (METHODOLOGY M-1) and print a summary.",
        description=(
            "Load the canonical CSVs, apply METHODOLOGY M-1 (normalization, comparison set, "
            "windows and weights, target scope, alliances and withdrawals, publication timing) "
            "and print a summary. With --output, also write rows.csv, polls.csv and "
            "adjustments.csv to that directory."
        ),
    )
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data"), help="data directory (default: data)"
    )
    parser.add_argument(
        "--output", type=Path, default=None, help="directory for the CSV outputs (e.g. build/prep)"
    )
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    out = sys.stdout
    if isinstance(out, io.TextIOWrapper):
        out.reconfigure(errors="backslashreplace")
    try:
        prepared = prepare(args.data_dir)
    except PrepError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1
    out.write(summarize(prepared))
    if args.output is not None:
        args.output.mkdir(parents=True, exist_ok=True)
        for name, frame in (
            ("rows", prepared.rows),
            ("polls", prepared.polls),
            ("adjustments", prepared.adjustments),
        ):
            frame.to_csv(args.output / f"{name}.csv", index=False, lineterminator="\n")
        out.write(f"wrote rows.csv, polls.csv, adjustments.csv to {args.output}\n")
    return 0
