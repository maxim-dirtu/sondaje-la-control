"""Error metrics per poll and per final poll (METHODOLOGY M-2.1 … M-2.4).

Input is the output of :func:`sondaje.prep.prepare` (M-1): this module never recomputes
normalization, the comparison set, windows, or eligibility. It reads ``rows`` (one row per
poll and compared entity, with the normalized poll share ``s`` and the result share ``r``) and
``polls`` (one row per poll, with ``eligible``, ``in_window``, and ``final_poll``).

- :func:`entity_errors`: the signed error ``e`` (M-2.1) and the log-odds error ``A'`` (M-2.4)
  of every compared entity, for every eligible poll.
- :func:`poll_errors`: per poll, ``MAE`` (M-2.2), ``TE`` (M-2.3), and ``B`` (M-2.4).
- :func:`compute_errors`: both tables, plus the view restricted to the final poll of each
  (house, election) (M-1.3, M-1.7).

Polls that are not ``eligible`` (scenarios, polls published on or after election day, polls
without a fieldwork end; M-1.3, M-1.7) have no metrics. Polls outside the accuracy window
keep their metrics, with ``in_window = False``, so that error can be plotted against time;
accuracy summaries use ``in_window`` polls (M-1.3), and the final polls are always inside it.

Errors are in percentage points (pp), except ``A'`` and ``B``, which are on the log-odds
scale. Wording is neutral (ADR-0003): a positive error is an overestimate, not a motive.
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

from sondaje.prep import Prepared, PrepError, prepare

if TYPE_CHECKING:
    from sondaje.cli import Subparsers

ENTITY_ERROR_COLUMNS: tuple[str, ...] = (
    "poll_id",
    "pollster_id",
    "election_id",
    "unit_id",
    "entity_id",
    "supporting_party_id",
    "s",
    "r",
    "e",
    "abs_e",
    "a_prime",
    "adjusted",
    "has_lt",
    "days_before",
    "weight",
    "in_window",
    "final_poll",
)
"""Columns of :attr:`ErrorMetrics.entities`, in order."""

POLL_ERROR_COLUMNS: tuple[str, ...] = (
    "poll_id",
    "pollster_id",
    "election_id",
    "unit_id",
    "fieldwork_end",
    "days_before",
    "weight",
    "in_window",
    "final_poll",
    "target_scope",
    "has_lt",
    "n",
    "n_method",
    "k",
    "mae",
    "te",
    "b",
    "b_terms",
    "b_undefined",
)
"""Columns of :attr:`ErrorMetrics.polls`, in order."""

_POLL_INFO_COLUMNS = POLL_ERROR_COLUMNS[:13]
"""Columns of ``Prepared.polls`` copied into :attr:`ErrorMetrics.polls`."""
_ROW_COLUMNS = tuple(c for c in ENTITY_ERROR_COLUMNS if c not in ("e", "abs_e", "a_prime"))
"""Columns of ``Prepared.rows`` copied into :attr:`ErrorMetrics.entities`."""


class MetricsInputError(ValueError):
    """The prepared tables lack a column, or hold a share this module cannot use."""


@dataclass(frozen=True)
class ErrorMetrics:
    """Error metrics of the eligible polls (METHODOLOGY M-2.1 … M-2.4)."""

    entities: pd.DataFrame
    """One row per (eligible poll, compared entity): ``e`` (pp), ``abs_e`` (pp), ``a_prime``."""
    polls: pd.DataFrame
    """One row per eligible poll: ``k``, ``mae`` (pp), ``te`` (pp), ``b``, ``b_terms``."""

    @property
    def final_entities(self) -> pd.DataFrame:
        """Entity errors of the final poll of each (house, election) (M-1.3, M-1.7)."""
        return self.entities[self.entities["final_poll"]].reset_index(drop=True)

    @property
    def final_polls(self) -> pd.DataFrame:
        """Poll metrics of the final poll of each (house, election): one row per ``unit_id``."""
        return self.polls[self.polls["final_poll"]].reset_index(drop=True)


# --- Scalar metrics -------------------------------------------------------------------------


def signed_error(s: pd.Series, r: pd.Series) -> pd.Series:
    """Signed error in pp, ``e_j = 100 · (s_j - r_j)`` (METHODOLOGY M-2.1).

    Positive values mean overestimation, negative values underestimation.
    """
    return 100.0 * (s - r)


def mean_absolute_error(e: pd.Series) -> float:
    """``MAE = (1/k) · Σ_j |e_j|`` over the ``k`` compared entities (METHODOLOGY M-2.2).

    ``e`` holds the signed errors of one poll, in pp. An empty input gives NaN.
    """
    return float(e.abs().mean()) if len(e) else math.nan


def total_error(e: pd.Series) -> float:
    """``TE = ½ · Σ_j |e_j|``, the "misallocated share" in pp (METHODOLOGY M-2.3).

    Both sides sum to 1 over the comparison set (M-1.2), so TE equals the sum of the
    overestimates, and also the sum of the underestimates. An empty input gives NaN.
    """
    return float(0.5 * e.abs().sum()) if len(e) else math.nan


def log_odds_error(s: pd.Series, r: pd.Series, zero_floor: float | None = None) -> pd.Series:
    """``A'_j = ln[ (s_j/(1-s_j)) / (r_j/(1-r_j)) ]`` (METHODOLOGY M-2.4, Arzheimer & Evans).

    The log-odds are undefined when a share is 0 or 1 (for example a poll that publishes no
    "others" while the result has some, or a named party shown at 0). By default such a term
    is NaN, so that :func:`poll_errors` leaves it out of ``B`` and reports it in
    ``b_undefined`` (M-2.7). With ``zero_floor`` (a sensitivity option; M-2.7),
    both shares are first clipped to ``[zero_floor, 1 - zero_floor]``, so that no term is
    undefined and a missing share counts as a large error.
    """
    if zero_floor is not None:
        if not 0.0 < zero_floor < 0.5:
            raise ValueError("zero_floor must be in (0, 0.5)")
        s, r = s.clip(zero_floor, 1.0 - zero_floor), r.clip(zero_floor, 1.0 - zero_floor)
    defined = (s > 0) & (s < 1) & (r > 0) & (r < 1)
    s_ok, r_ok = s.where(defined), r.where(defined)
    return np.log(s_ok / (1.0 - s_ok)) - np.log(r_ok / (1.0 - r_ok))


# --- Tables ---------------------------------------------------------------------------------


def _check(frame: pd.DataFrame, name: str, required: tuple[str, ...]) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise MetricsInputError(f"Prepared.{name} lacks column(s) {missing}")


def entity_errors(prepared: Prepared, zero_floor: float | None = None) -> pd.DataFrame:
    """Signed and log-odds error of every compared entity of every eligible poll.

    Implements METHODOLOGY M-2.1 (``e``, in pp) and M-2.4 (``a_prime``, NaN where undefined,
    see :func:`log_odds_error`). Only ``eligible`` polls are used (M-1.3, M-1.7). The
    "others" bucket (``entity_id`` ``_others``) is a compared entity like any other (M-1.2),
    and an entity the poll does not name enters with its share in the poll's "others"
    (M-1.2), so no entity is ever missing from a poll's comparison.
    Raises :class:`MetricsInputError` when a share is missing: M-1 never produces one, and
    this module does not fill it in.
    """
    _check(prepared.rows, "rows", (*_ROW_COLUMNS, "eligible"))
    rows = prepared.rows[prepared.rows["eligible"]]
    if rows[["s", "r"]].isna().any(axis=None):
        raise MetricsInputError("a prepared row has no poll share s or result share r")
    out = rows[list(_ROW_COLUMNS)].copy()
    out["e"] = signed_error(out["s"], out["r"])
    out["abs_e"] = out["e"].abs()
    out["a_prime"] = log_odds_error(out["s"], out["r"], zero_floor)
    return out[list(ENTITY_ERROR_COLUMNS)].reset_index(drop=True)


def poll_errors(prepared: Prepared, entities: pd.DataFrame | None = None) -> pd.DataFrame:
    """``MAE``, ``TE`` and ``B`` of every eligible poll (METHODOLOGY M-2.2, M-2.3, M-2.4).

    ``k`` is the number of compared entities, "others" included (M-1.2). ``MAE`` and ``TE``
    are in pp. ``B = mean_j |A'_j|`` is taken over the entities where the log-odds are
    defined (``b_terms``); ``b_undefined = k - b_terms`` counts the others, and ``B`` is NaN
    when none is defined. ``entities`` is the output of :func:`entity_errors`, computed with
    the default options when omitted. The order follows ``Prepared.polls``.
    """
    _check(prepared.polls, "polls", (*_POLL_INFO_COLUMNS, "eligible"))
    if entities is None:
        entities = entity_errors(prepared)
    grouped = entities.assign(abs_a=entities["a_prime"].abs()).groupby("poll_id", sort=False)
    metrics = pd.DataFrame(
        {
            "k": grouped.size(),
            "mae": grouped["abs_e"].mean(),
            "te": 0.5 * grouped["abs_e"].sum(),
            "b": grouped["abs_a"].mean(),
            "b_terms": grouped["a_prime"].count(),
        }
    )
    metrics["b_undefined"] = metrics["k"] - metrics["b_terms"]
    polls = prepared.polls[prepared.polls["eligible"]]
    out = polls[list(_POLL_INFO_COLUMNS)].join(metrics, on="poll_id", how="inner")
    for column in ("k", "b_terms", "b_undefined"):
        out[column] = out[column].astype("Int64")
    return out[list(POLL_ERROR_COLUMNS)].reset_index(drop=True)


def compute_errors(prepared: Prepared, zero_floor: float | None = None) -> ErrorMetrics:
    """Error metrics per eligible poll and, through ``final_*``, per final poll (M-2.1 … M-2.4).

    ``zero_floor`` is the optional sensitivity option of :func:`log_odds_error`; the default
    leaves undefined log-odds terms out of ``B``.
    """
    entities = entity_errors(prepared, zero_floor)
    return ErrorMetrics(entities, poll_errors(prepared, entities))


# --- Summary and CLI ------------------------------------------------------------------------


def summarize(metrics: ErrorMetrics) -> str:
    """A plain-text table of the final poll of each (election, house), in pp and log-odds."""
    finals = metrics.final_polls
    out = io.StringIO()
    out.write(
        f"{len(metrics.polls)} eligible polls, {int(metrics.polls['in_window'].sum())} in the "
        f"accuracy window, {len(finals)} final polls\n\n"
    )
    if finals.empty:
        out.write("No final polls.\n")
        return out.getvalue()
    columns = ["election_id", "pollster_id", "poll_id", "days_before"]
    columns += ["k", "mae", "te", "b", "b_undefined", "has_lt"]
    table = finals.sort_values(["election_id", "mae", "pollster_id"])[columns]
    out.write("Final poll of each (election, house); errors in pp, B on the log-odds scale:\n")
    out.write(table.to_string(index=False, float_format=lambda v: f"{v:.3f}") + "\n")
    return out.getvalue()


def register(subparsers: "Subparsers") -> None:
    parser = subparsers.add_parser(
        "errors",
        help="Compute the error metrics of the polls (METHODOLOGY M-2.1 to M-2.4).",
        description=(
            "Prepare the data (METHODOLOGY M-1), then compute the signed error, MAE, total "
            "error and log-odds accuracy of every eligible poll, and print them for the final "
            "poll of each (election, house). With --output, also write entity_errors.csv, "
            "poll_errors.csv and final_polls.csv to that directory."
        ),
    )
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data"), help="data directory (default: data)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="directory for the CSV outputs (e.g. build/errors)",
    )
    parser.add_argument(
        "--zero-floor",
        type=float,
        default=None,
        help="clip shares to [f, 1-f] before the log-odds, so that no term is undefined "
        "(sensitivity option; default: undefined terms are left out of B)",
    )
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    out = sys.stdout
    if isinstance(out, io.TextIOWrapper):
        out.reconfigure(errors="backslashreplace")
    try:
        prepared = prepare(args.data_dir)
        metrics = compute_errors(prepared, args.zero_floor)
    except (PrepError, ValueError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1
    out.write(summarize(metrics))
    if args.output is not None:
        args.output.mkdir(parents=True, exist_ok=True)
        metrics.entities.to_csv(args.output / "entity_errors.csv", index=False)
        metrics.polls.to_csv(args.output / "poll_errors.csv", index=False)
        metrics.final_polls.to_csv(args.output / "final_polls.csv", index=False)
        out.write(f"\nwrote 3 CSV files to {args.output}\n")
    return 0
