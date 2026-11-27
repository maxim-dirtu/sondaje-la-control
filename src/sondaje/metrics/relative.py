"""Comparisons between houses on their final polls (METHODOLOGY M-2.5, M-2.6, M-2.8).

Input is the output of :func:`sondaje.metrics.errors.compute_errors` (M-2.1 … M-2.4): this
module never recomputes shares, errors, windows, or final polls. It uses the final poll of
each (house, election) only (M-1.3, M-1.7), one per house, so each house counts once (M-1.6).

- :func:`comparison_sets`: the common comparison set of each election (M-2.8): the entities
  that every house with a final poll names, plus one common "others" bucket.
- :func:`common_entity_errors`: the T-021 errors of each final poll on that common set.
- :func:`house_effects`: the relative house effect ``he`` per (house, election, entity)
  against the leave-one-house-out market (M-2.5).
- :func:`relative_accuracy`: ``RA`` per (house, election) against the median of the other
  houses (M-2.6).
- :func:`compute_relative`: all of the above.

The results are **descriptive**: they carry no significance test yet (T-024, M-4). Wording is
neutral (ADR-0003): a positive house effect means the house's estimate was higher than the
other houses' estimates, relative to the result; it says nothing about a motive.
"""

import argparse
import io
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from sondaje.metrics.errors import ErrorMetrics, MetricsInputError, compute_errors
from sondaje.prep import OTHERS, PrepError, prepare

if TYPE_CHECKING:
    from sondaje.cli import Subparsers

WEIGHTINGS: tuple[str, ...] = ("recency", "equal")
"""Weights of the reference houses in the market error (M-2.5). ``recency`` is the default."""

COMPARISON_SET_COLUMNS: tuple[str, ...] = (
    "election_id",
    "n_houses",
    "houses",
    "k_common",
    "common_entities",
    "merged_entities",
)
"""Columns of :attr:`RelativeMetrics.comparison_sets`, in order."""

HOUSE_EFFECT_COLUMNS: tuple[str, ...] = (
    "election_id",
    "pollster_id",
    "unit_id",
    "poll_id",
    "entity_id",
    "supporting_party_id",
    "days_before",
    "weight",
    "s",
    "r",
    "e",
    "n_ref_houses",
    "market_e",
    "he",
)
"""Columns of :attr:`RelativeMetrics.house_effects`, in order."""

RELATIVE_ACCURACY_COLUMNS: tuple[str, ...] = (
    "election_id",
    "pollster_id",
    "unit_id",
    "poll_id",
    "days_before",
    "k_common",
    "mae_common",
    "te_common",
    "n_ref_houses",
    "ref_mae",
    "ra",
)
"""Columns of :attr:`RelativeMetrics.relative_accuracy`, in order."""

_ENTITY_COLUMNS = HOUSE_EFFECT_COLUMNS[:11]
"""Columns of :func:`common_entity_errors`."""

NOT_SIGNIFICANCE = (
    "Descriptive only: no significance test yet (T-024). A difference between houses can be "
    "sampling noise."
)


@dataclass(frozen=True)
class RelativeMetrics:
    """Comparisons between the final polls of the houses (METHODOLOGY M-2.5, M-2.6, M-2.8).

    Column meanings (errors in pp). Every table starts with ``election_id``. The per-house
    tables also carry ``pollster_id``, ``unit_id`` (the (house, election) unit, M-1.6),
    ``poll_id`` (the final poll, M-1.3) and its ``days_before`` (election day minus the end
    of fieldwork). ``house_effects`` adds ``entity_id`` (``_others`` for the common "others")
    and ``supporting_party_id`` (M-1.5; empty for "others").

    ``comparison_sets``, one row per election:
        ``n_houses`` houses with a final poll, listed in ``houses`` (``;``-separated);
        ``common_entities``, the entities every one of them names (``;``-separated, by result
        share); ``merged_entities``, the entities named by some but not all of them, which
        enter the common "others"; ``k_common``, the size of the common set, the common
        "others" included when it is not empty.
    ``house_effects``, one row per (house, election, common entity):
        ``s``, ``r``, ``e`` as in M-2.1, on the common set (for :data:`OTHERS`, the sums over
        every entity outside the common set); ``weight`` is the recency weight of the poll
        (M-1.3); ``n_ref_houses``, the number of other houses in the market;
        ``market_e``, their weighted mean ``e``; ``he``, which is ``e - market_e`` (M-2.5).
        ``market_e`` and ``he`` are NaN when no other house has a final poll.
    ``relative_accuracy``, one row per (house, election):
        ``k_common``, ``mae_common`` (M-2.2) and ``te_common`` (M-2.3) on the common set;
        ``ref_mae``, the median ``mae_common`` of the ``n_ref_houses`` other houses;
        ``ra``, which is ``mae_common - ref_mae`` (M-2.6), negative when the house was
        closer to the result than the other houses' median. NaN without another house.
    """

    comparison_sets: pd.DataFrame
    house_effects: pd.DataFrame
    relative_accuracy: pd.DataFrame
    weighting: str = "recency"


# --- Common comparison set (M-2.8) ----------------------------------------------------------


def _final_entities(metrics: ErrorMetrics) -> pd.DataFrame:
    finals = metrics.final_entities
    per_house = finals.groupby(["election_id", "pollster_id"])["poll_id"].nunique()
    if (per_house > 1).any():
        raise MetricsInputError("a house has more than one final poll in an election")
    return finals


def comparison_sets(metrics: ErrorMetrics) -> pd.DataFrame:
    """The common comparison set of each election (METHODOLOGY M-2.8).

    The common entities are the named entities (not "others") that the final poll of
    **every** house of the election compares on its own (M-1.2). An entity that some house
    rolls into its "others" (unnamed, or below the threshold in its target scope) is a merged
    entity: it enters the common "others" of every house. Common entities are ordered by
    their mean result share, largest first. ``k_common`` counts the common "others" when any
    house has a non-zero share on either side of it.
    """
    finals = _final_entities(metrics)
    records = []
    for election_id, rows in finals.groupby("election_id", sort=True):
        houses = sorted(rows["pollster_id"].unique())
        named = rows[rows["entity_id"] != OTHERS]
        per_poll = named.groupby("poll_id")["entity_id"].agg(set)
        polls = rows["poll_id"].unique()
        sets = [per_poll.get(poll_id, set()) for poll_id in polls]
        common = set.intersection(*sets) if sets else set()
        merged = set.union(*sets) - common if sets else set()
        mean_r = named.groupby("entity_id")["r"].mean()
        ordered = sorted(common, key=lambda entity: (-mean_r[entity], entity))
        outside = rows[~rows["entity_id"].isin(common)]
        has_others = bool((outside["s"] > 0).any() or (outside["r"] > 0).any())
        records.append(
            {
                "election_id": election_id,
                "n_houses": len(houses),
                "houses": ";".join(houses),
                "k_common": len(ordered) + int(has_others),
                "common_entities": ";".join(ordered),
                "merged_entities": ";".join(sorted(merged)),
            }
        )
    out = pd.DataFrame(records, columns=list(COMPARISON_SET_COLUMNS))
    out["n_houses"] = out["n_houses"].astype("Int64")
    out["k_common"] = out["k_common"].astype("Int64")
    return out


def common_entity_errors(metrics: ErrorMetrics, sets: pd.DataFrame | None = None) -> pd.DataFrame:
    """The errors of every final poll on the common comparison set of its election (M-2.8).

    A common entity keeps its T-021 row unchanged (``s``, ``r``, ``e``; M-2.1). Every other
    row of the poll (merged entities and the poll's own "others") is summed into one
    :data:`OTHERS` row: ``s`` and ``r`` are the shares of everything outside the common set,
    so both sides still sum to 1 and ``e`` is the sum of the merged errors. No share is
    renormalized. The "others" row is present when ``comparison_sets`` counts it in
    ``k_common``.
    """
    finals = _final_entities(metrics)
    if sets is None:
        sets = comparison_sets(metrics)
    pieces = []
    for spec in sets.itertuples(index=False):
        common = [entity for entity in str(spec.common_entities).split(";") if entity]
        has_others = int(spec.k_common) > len(common)
        rows = finals[finals["election_id"] == spec.election_id]
        for _, poll in rows.groupby("poll_id", sort=False):
            keep = poll.set_index("entity_id").loc[common].reset_index()
            pieces.append(keep[list(_ENTITY_COLUMNS)])
            if has_others:
                rest = poll[~poll["entity_id"].isin(common)]
                first = poll.iloc[0]
                others = {column: first[column] for column in _ENTITY_COLUMNS}
                others.update(
                    entity_id=OTHERS,
                    supporting_party_id=None,
                    s=float(rest["s"].sum()),
                    r=float(rest["r"].sum()),
                    e=float(rest["e"].sum()),
                )
                pieces.append(pd.DataFrame([others], columns=list(_ENTITY_COLUMNS)))
    if not pieces:
        return pd.DataFrame(columns=list(_ENTITY_COLUMNS))
    return pd.concat(pieces, ignore_index=True)


# --- M-2.5 relative house effect ------------------------------------------------------------


def _reference_weights(rows: pd.DataFrame, weighting: str) -> pd.Series:
    if weighting == "equal":
        return pd.Series(1.0, index=rows.index)
    weights = rows["weight"].astype(float)
    if weights.isna().any() or (weights <= 0).any():
        raise MetricsInputError("a final poll has no positive recency weight")
    return weights


def house_effects(common: pd.DataFrame, weighting: str = "recency") -> pd.DataFrame:
    """``he_{h,j,E} = e_{h,j,E} - ē_{-h,j,E}`` for every final poll and common entity (M-2.5).

    ``common`` is the output of :func:`common_entity_errors`. The market error
    ``ē_{-h,j,E}`` (``market_e``) is the weighted mean ``e`` of the **other** houses' final
    polls for entity ``j`` (leave-one-house-out, M-2.8), with weights
    ``w = exp(-days_before / τ)`` (M-1.3; ``weighting="recency"``, the default) or equal
    weights (``weighting="equal"``, a sensitivity option). ``n_ref_houses`` counts the other
    houses; with none, ``market_e`` and ``he`` are NaN. Because the house itself is left out,
    a house whose errors are the market's plus a constant offset gets that offset back
    exactly, whatever the weights.
    """
    if weighting not in WEIGHTINGS:
        raise ValueError(f"weighting must be one of {WEIGHTINGS}")
    out = common.copy()
    out["n_ref_houses"] = 0
    out["market_e"] = math.nan
    for _, rows in out.groupby(["election_id", "entity_id"], sort=False):
        weights = _reference_weights(rows, weighting)
        for index in rows.index:
            others = rows.index[rows.index != index]
            out.loc[index, "n_ref_houses"] = len(others)
            if len(others):
                w = weights.loc[others]
                out.loc[index, "market_e"] = float((w * rows.loc[others, "e"]).sum() / w.sum())
    out["n_ref_houses"] = out["n_ref_houses"].astype("Int64")
    out["he"] = out["e"] - out["market_e"]
    return out[list(HOUSE_EFFECT_COLUMNS)].reset_index(drop=True)


# --- M-2.6 relative accuracy ----------------------------------------------------------------


def relative_accuracy(common: pd.DataFrame) -> pd.DataFrame:
    """``RA_{h,E} = MAE_{h,E} - median_{h'≠h}(MAE_{h',E})`` on the common set (M-2.6).

    ``common`` is the output of :func:`common_entity_errors`. ``mae_common`` (M-2.2) and
    ``te_common`` (M-2.3) are computed over the ``k_common`` rows of the common set, so every
    house of an election is measured on the same entities. ``ref_mae`` is the unweighted
    median of the other houses' ``mae_common`` (leave-one-house-out, M-2.8); with an even
    number of other houses it is the mean of the two middle values. With no other house,
    ``ref_mae`` and ``ra`` are NaN.
    """
    abs_e = common.assign(abs_e=common["e"].abs())
    grouped = abs_e.groupby("poll_id", sort=False)
    polls = grouped[["election_id", "pollster_id", "unit_id", "days_before"]].first()
    polls["k_common"] = grouped.size().astype("Int64")
    polls["mae_common"] = grouped["abs_e"].mean()
    polls["te_common"] = 0.5 * grouped["abs_e"].sum()
    polls = polls.reset_index()
    polls["n_ref_houses"] = 0
    polls["ref_mae"] = math.nan
    for _, rows in polls.groupby("election_id", sort=False):
        for index in rows.index:
            others = rows.loc[rows.index != index, "mae_common"]
            polls.loc[index, "n_ref_houses"] = len(others)
            if len(others):
                polls.loc[index, "ref_mae"] = float(np.median(others))
    polls["n_ref_houses"] = polls["n_ref_houses"].astype("Int64")
    polls["ra"] = polls["mae_common"] - polls["ref_mae"]
    return polls[list(RELATIVE_ACCURACY_COLUMNS)].reset_index(drop=True)


def compute_relative(metrics: ErrorMetrics, weighting: str = "recency") -> RelativeMetrics:
    """The comparison sets, house effects, and relative accuracy (M-2.5, M-2.6, M-2.8)."""
    if weighting not in WEIGHTINGS:
        raise ValueError(f"weighting must be one of {WEIGHTINGS}")
    sets = comparison_sets(metrics)
    common = common_entity_errors(metrics, sets)
    return RelativeMetrics(
        sets, house_effects(common, weighting), relative_accuracy(common), weighting
    )


# --- Summary and CLI ------------------------------------------------------------------------


def _fmt(value: float) -> str:
    return f"{value:+.2f}" if not pd.isna(value) else "-"


def summarize(relative: RelativeMetrics) -> str:
    """A plain-text report per election: comparison set, house effects, relative accuracy."""
    out = io.StringIO()
    out.write(
        f"Comparisons between houses on their final polls (METHODOLOGY M-2.5, M-2.6, M-2.8); "
        f"errors in pp; market weights: {relative.weighting}.\n{NOT_SIGNIFICANCE}\n"
    )
    if relative.comparison_sets.empty:
        out.write("\nNo final polls.\n")
        return out.getvalue()
    for spec in relative.comparison_sets.itertuples(index=False):
        election = spec.election_id
        out.write(f"\n== {election}: {spec.n_houses} house(s), k_common = {spec.k_common}\n")
        out.write(f"common entities: {spec.common_entities or '-'}\n")
        out.write(f"merged into others: {spec.merged_entities or '-'}\n")
        if spec.n_houses < 2:
            out.write("only one house: no comparison.\n")
        elif spec.n_houses == 2:
            out.write(
                "two houses: each house effect is the gap to the other house; the two are "
                "mirror images and do not show which house deviates.\n"
            )
        he = relative.house_effects[relative.house_effects["election_id"] == election]
        table = he.pivot(index="pollster_id", columns="entity_id", values="he")
        entities = [e for e in str(spec.common_entities).split(";") if e]
        if OTHERS in table.columns:
            entities.append(OTHERS)
        table = table[entities].map(_fmt)
        out.write("house effect he (e minus the other houses' market error):\n")
        out.write(table.to_string() + "\n")
        ra = relative.relative_accuracy[relative.relative_accuracy["election_id"] == election]
        ra = ra.sort_values(["mae_common", "pollster_id"])
        columns = ["pollster_id", "days_before", "mae_common", "te_common", "ref_mae", "ra"]
        out.write("relative accuracy (MAE on the common set minus the other houses' median):\n")
        out.write(ra[columns].to_string(index=False, float_format=lambda v: f"{v:.2f}") + "\n")
    return out.getvalue()


def register(subparsers: "Subparsers") -> None:
    parser = subparsers.add_parser(
        "relative",
        help="Compare houses on their final polls (METHODOLOGY M-2.5, M-2.6).",
        description=(
            "Prepare the data (M-1) and compute the errors (M-2.1 to M-2.4), then compare the "
            "final poll of each house with the other houses' final polls on a common "
            "comparison set (M-2.8): the relative house effect per entity (M-2.5) and the "
            "relative accuracy (M-2.6). Descriptive only, with no significance test (T-024). "
            "With --output, also write comparison_sets.csv, house_effects.csv and "
            "relative_accuracy.csv to that directory."
        ),
    )
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data"), help="data directory (default: data)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="directory for the CSV outputs (e.g. build/relative)",
    )
    parser.add_argument(
        "--weighting",
        choices=WEIGHTINGS,
        default="recency",
        help="weights of the other houses in the market error (default: recency, M-1.3)",
    )
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    out = sys.stdout
    if isinstance(out, io.TextIOWrapper):
        out.reconfigure(errors="backslashreplace")
    try:
        relative = compute_relative(compute_errors(prepare(args.data_dir)), args.weighting)
    except (PrepError, ValueError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1
    out.write(summarize(relative))
    if args.output is not None:
        args.output.mkdir(parents=True, exist_ok=True)
        relative.comparison_sets.to_csv(args.output / "comparison_sets.csv", index=False)
        relative.house_effects.to_csv(args.output / "house_effects.csv", index=False)
        relative.relative_accuracy.to_csv(args.output / "relative_accuracy.csv", index=False)
        out.write(f"\nwrote 3 CSV files to {args.output}\n")
    return 0
