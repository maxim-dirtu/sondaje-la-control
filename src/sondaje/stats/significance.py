"""Significance tests (METHODOLOGY M-4.1, M-4.2, M-4.3).

These tests ask whether a deviation is larger than sampling noise alone would produce. They
never recompute an M-1 … M-3 quantity: they read the outputs of
:func:`sondaje.metrics.errors.compute_errors` (signed errors ``e``, with the effective sample
size ``n`` and ``n_method`` of M-1.1 OI-5 carried from :mod:`sondaje.prep`) and of
:func:`sondaje.metrics.relative.compute_relative` (the house effects ``he``, M-2.5). The
design effect is ``MethodologyConfig.deff``, the same parameter as M-3.2 uses.

- :func:`poll_z_scores`: per (eligible poll, compared entity), the sampling z-score of the
  error against the result (M-4.1).
- :func:`lean_units`: the house effects arranged by (house, entity, election), one value per
  (house, election) unit (M-1.6).
- :func:`sign_test`, :func:`t_test`: the two tests on the house effects of one
  (house, entity) across elections (M-4.2, M-4.3).
- :func:`cross_election_tests`: both tests for every (house, entity), with combinations of
  fewer than :data:`MIN_ELECTIONS` elections marked :data:`STATUS_INSUFFICIENT` and not tested.

Wording is neutral (ADR-0003): a small p-value indicates a systematic deviation (a statistical
lean) that sampling noise alone is unlikely to produce; it says nothing about a motive. A large
p-value means the values are consistent with sampling noise, or that the test has too little
power to tell. With 3 elections or fewer every result is preliminary: for example, a two-sided
sign test on 3 elections cannot give a p-value below 0.25.
"""

import argparse
import io
import math
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import numpy as np
import pandas as pd
from scipy import stats

from sondaje.config import MethodologyConfig
from sondaje.metrics.errors import ErrorMetrics, MetricsInputError, compute_errors
from sondaje.metrics.relative import WEIGHTINGS, compute_relative
from sondaje.prep import OTHERS, PrepError, prepare

if TYPE_CHECKING:
    from sondaje.cli import Subparsers

MIN_ELECTIONS = 3
"""Elections (``(house, election)`` units) below which a (house, entity) is not tested."""
PRELIMINARY_MAX_ELECTIONS = 3
"""Up to this many elections, a tested result is marked ``preliminary`` (low power)."""
TIE_TOLERANCE = 1e-9
"""``|he|`` (pp) at or below which a house effect counts as a tie (zero) in the sign test."""
Z_BAND = 1.96
"""``|z|`` beyond which a poll error lies outside the 95% sampling band (summary only)."""

ALTERNATIVES: tuple[str, ...] = ("two-sided", "greater", "less")
"""Alternative hypotheses of M-4.2 and M-4.3; ``two-sided`` is the default."""
ATTRIBUTIONS: tuple[str, ...] = ("party", "entity")
"""How an entity is identified across elections (see :func:`lean_units`)."""

Z_OK = "ok"
Z_NO_SAMPLE_SIZE = "no_sample_size"
Z_DEGENERATE_RESULT = "result_share_0_or_1"

STATUS_TESTED = "tested"
STATUS_INSUFFICIENT = f"insufficient (< {MIN_ELECTIONS} elections)"

Z_SCORE_COLUMNS: tuple[str, ...] = (
    "poll_id",
    "pollster_id",
    "election_id",
    "unit_id",
    "entity_id",
    "supporting_party_id",
    "days_before",
    "in_window",
    "final_poll",
    "s",
    "r",
    "e",
    "n",
    "n_method",
    "deff",
    "se",
    "z",
    "z_status",
)
"""Columns of :attr:`Significance.z_scores`, in order."""

LEAN_UNIT_COLUMNS: tuple[str, ...] = (
    "pollster_id",
    "lean_id",
    "election_id",
    "unit_id",
    "entity_id",
    "poll_id",
    "n_ref_houses",
    "he",
)
"""Columns of :attr:`Significance.lean_units`, in order."""

TEST_COLUMNS: tuple[str, ...] = (
    "pollster_id",
    "lean_id",
    "entities",
    "elections",
    "n_elections",
    "mean_he",
    "sd_he",
    "n_positive",
    "n_negative",
    "n_ties",
    "sign_p",
    "sign_p_min",
    "t_stat",
    "t_df",
    "t_p",
    "alternative",
    "status",
    "preliminary",
)
"""Columns of :attr:`Significance.tests`, in order."""

NOTE = (
    "A small p-value indicates a systematic deviation (statistical lean) that sampling noise "
    "alone is unlikely to produce; it says nothing about a motive. A large p-value means the "
    "values are consistent with sampling noise, or that the test has too little power. "
    f"With {PRELIMINARY_MAX_ELECTIONS} elections or fewer every result is preliminary and "
    "low-powered: a two-sided sign test on 3 elections cannot give a p-value below 0.25."
)


@dataclass(frozen=True)
class Significance:
    """The significance tests of METHODOLOGY M-4.1 … M-4.3.

    ``z_scores``, one row per (eligible poll, compared entity) (M-4.1):
        ``poll_id``, ``pollster_id``, ``election_id``, ``unit_id``, ``entity_id``,
        ``supporting_party_id``, ``days_before``, ``in_window``, ``final_poll``, ``s``,
        ``r`` and ``e`` (pp) as in M-2.1; ``n``, the effective sample size of M-1.1 OI-5, and
        ``n_method``, how it was obtained; ``deff``, the design effect; ``se``, the sampling
        error of the poll share around the result, in pp; ``z``, which is ``e / se``;
        ``z_status``: ``ok``, ``no_sample_size`` (no ``n``: ``se`` and ``z`` are empty, the
        row is kept) or ``result_share_0_or_1`` (``r`` is 0 or 1, so ``se`` is 0 and ``z`` is
        empty).
    ``lean_units``, one row per (house, entity, election) with a defined house effect:
        ``lean_id``, the identity of the entity across elections (see :func:`lean_units`);
        ``unit_id``, the (house, election) unit (M-1.6); ``entity_id`` and ``poll_id``, the
        entity and final poll the value comes from; ``n_ref_houses`` and ``he`` from M-2.5.
    ``tests``, one row per (house, ``lean_id``) (M-4.2, M-4.3):
        ``entities`` and ``elections`` (``;``-separated) and ``n_elections``, the units used;
        ``mean_he`` and ``sd_he`` (pp, sample standard deviation); ``n_positive``,
        ``n_negative``, ``n_ties``, the signs of ``he`` (``|he| <= 1e-9`` pp is a tie);
        ``sign_p``, the binomial sign test p-value (ties left out); ``sign_p_min``, the
        smallest p-value that sign test could give with this many non-tied elections;
        ``t_stat``, ``t_df``, ``t_p``, the one-sample t-test of ``he`` against 0;
        ``alternative``, the alternative hypothesis of both tests; ``status``: ``tested``, or
        ``insufficient (< 3 elections)``, in which case every test column is empty;
        ``preliminary``: true when the result rests on 3 elections or fewer.
    """

    z_scores: pd.DataFrame
    lean_units: pd.DataFrame
    tests: pd.DataFrame
    deff: float
    weighting: str = "recency"
    attribution: str = "party"
    alternative: str = "two-sided"


# --- M-4.1 single-poll sampling error -------------------------------------------------------


def sampling_se(r: pd.Series, n: pd.Series, deff: float) -> pd.Series:
    """``SE_j = sqrt(r_j(1-r_j)/n) · sqrt(deff)``, in pp (METHODOLOGY M-4.1).

    ``r`` is the result share in [0, 1] and ``n`` the effective sample size (M-1.1 OI-5).
    Empty where ``n`` is empty. The value is multiplied by 100, so that it has the unit of
    the signed error ``e`` (M-2.1).
    """
    if deff <= 0:
        raise ValueError("deff must be > 0")
    r = r.astype(float)
    return 100.0 * np.sqrt(r * (1.0 - r) / n.astype(float)) * math.sqrt(deff)


def poll_z_scores(metrics: ErrorMetrics, config: MethodologyConfig | None = None) -> pd.DataFrame:
    """The sampling z-score of every compared entity of every eligible poll (M-4.1).

    Implements METHODOLOGY M-4.1: ``z_j = (s_j - r_j) / SE_j``, computed as ``e_j / SE_j``
    with ``e_j = 100·(s_j - r_j)`` from M-2.1 and ``SE_j`` in pp (:func:`sampling_se`). ``n``
    and ``n_method`` are those of M-1.1 OI-5; ``n_method = sample_size`` overstates ``n``, so
    its ``|z|`` is overstated too. ``deff`` is ``config.deff`` (default 1.5), the parameter
    M-3.2 uses. A poll without ``n`` is kept with empty ``se`` and ``z`` and
    ``z_status = no_sample_size``; an entity whose result share is 0 or 1 has
    ``z_status = result_share_0_or_1``.
    """
    config = config or MethodologyConfig()
    entities, polls = metrics.entities, metrics.polls
    for name, frame, required in (
        ("entities", entities, ("poll_id", "entity_id", "s", "r", "e")),
        ("polls", polls, ("poll_id", "n", "n_method")),
    ):
        missing = [column for column in required if column not in frame.columns]
        if missing:
            raise MetricsInputError(f"ErrorMetrics.{name} lacks column(s) {missing}")
    sizes = polls.set_index("poll_id")[["n", "n_method"]]
    out = entities.join(sizes, on="poll_id")
    out["n"] = out["n"].astype(float)
    out["deff"] = config.deff
    se = sampling_se(out["r"], out["n"], config.deff)
    degenerate = se.eq(0.0)
    out["se"] = se.where(~degenerate)
    out["z"] = out["e"].astype(float) / out["se"]
    out["z_status"] = np.select(
        [out["n"].isna(), degenerate], [Z_NO_SAMPLE_SIZE, Z_DEGENERATE_RESULT], default=Z_OK
    )
    return out[list(Z_SCORE_COLUMNS)].reset_index(drop=True)


# --- M-4.2, M-4.3 across elections ----------------------------------------------------------


def lean_units(house_effects: pd.DataFrame, attribution: str = "party") -> pd.DataFrame:
    """The house effects ``he`` (M-2.5) by (house, entity, election), one per unit (M-1.6).

    ``house_effects`` is :attr:`RelativeMetrics.house_effects`, which holds the final poll of
    each (house, election) only, so every value is one (house, election) unit: extra polls of
    a house in an election never add a value. A table with two rows for the same (house,
    election, entity) raises :class:`MetricsInputError`.

    Left out: rows without a house effect (no other house in the election) and the common
    "others" (:data:`OTHERS`), whose content differs from one election to the next.

    ``lean_id`` identifies the entity across elections. With ``attribution="party"`` (the
    default) a candidate with a single supporting party is counted as that party (M-1.5,
    I-016), so that a lean can be followed from parliamentary to presidential elections; when
    two rows of the same (house, election) would share a ``lean_id``, both keep their own
    ``entity_id``. With ``attribution="entity"``, ``lean_id`` is the ``entity_id``.
    """
    if attribution not in ATTRIBUTIONS:
        raise ValueError(f"attribution must be one of {ATTRIBUTIONS}")
    keys = ["pollster_id", "election_id", "entity_id"]
    if house_effects.duplicated(keys).any():
        raise MetricsInputError(
            "house_effects has several rows for one (house, election, entity): "
            "a (house, election) unit must give one value (M-1.6)"
        )
    rows = house_effects[
        (house_effects["entity_id"] != OTHERS) & house_effects["he"].notna()
    ].copy()
    rows["lean_id"] = rows["entity_id"]
    if attribution == "party":
        party = rows["supporting_party_id"]
        rows["lean_id"] = party.where(party.notna() & party.ne(""), rows["entity_id"])
        clash = rows.duplicated(["pollster_id", "election_id", "lean_id"], keep=False)
        rows.loc[clash, "lean_id"] = rows.loc[clash, "entity_id"]
    rows["he"] = rows["he"].astype(float)
    rows = rows.sort_values(["pollster_id", "lean_id", "election_id"])
    return rows[list(LEAN_UNIT_COLUMNS)].reset_index(drop=True)


class SignTest(NamedTuple):
    n_positive: int
    n_negative: int
    n_ties: int
    p: float
    p_min: float


class TTest(NamedTuple):
    statistic: float
    df: int
    p: float


def _check_alternative(alternative: str) -> None:
    if alternative not in ALTERNATIVES:
        raise ValueError(f"alternative must be one of {ALTERNATIVES}")


def sign_test(he: Sequence[float], alternative: str = "two-sided") -> SignTest:
    """Binomial sign test of the house effects against p = 0.5 (METHODOLOGY M-4.2).

    Implements METHODOLOGY M-4.2: counts the elections with ``he > 0`` and tests that count
    against a binomial with p = 0.5 (``scipy.stats.binomtest``). ``he`` holds one value per
    election (M-1.6). A value with ``|he| <= TIE_TOLERANCE`` is a tie: it carries no sign,
    so it is left out and the test runs on the other elections (the usual convention of the
    sign test). ``greater`` tests for more positive than negative values. ``p_min`` is the
    smallest p-value the test can give with this many non-tied values (``2·0.5^m`` two-sided,
    ``0.5^m`` one-sided, at most 1). Both are NaN when every value is a tie.
    """
    _check_alternative(alternative)
    values = np.asarray(he, dtype=float)
    ties = int((np.abs(values) <= TIE_TOLERANCE).sum())
    positive = int((values > TIE_TOLERANCE).sum())
    negative = int((values < -TIE_TOLERANCE).sum())
    m = positive + negative
    if m == 0:
        return SignTest(positive, negative, ties, math.nan, math.nan)
    p = float(stats.binomtest(positive, m, 0.5, alternative=alternative).pvalue)
    p_min = min(1.0, (2.0 if alternative == "two-sided" else 1.0) * 0.5**m)
    return SignTest(positive, negative, ties, p, p_min)


def t_test(he: Sequence[float], alternative: str = "two-sided") -> TTest:
    """One-sample t-test of the house effects against 0 (METHODOLOGY M-4.3).

    Implements METHODOLOGY M-4.3 with ``scipy.stats.ttest_1samp``: ``he`` holds one value per
    election (M-1.6), ``df = len(he) - 1``. Ties (``he = 0``) are ordinary values here.
    ``statistic`` and ``p`` are NaN with fewer than 2 values or when every value is the same
    (the standard deviation is 0 and the statistic is undefined).
    """
    _check_alternative(alternative)
    values = np.asarray(he, dtype=float)
    df = len(values) - 1
    if len(values) < 2 or float(np.ptp(values)) == 0.0:
        return TTest(math.nan, max(df, 0), math.nan)
    result = stats.ttest_1samp(values, 0.0, alternative=alternative)
    return TTest(float(result.statistic), df, float(result.pvalue))


def cross_election_tests(
    units: pd.DataFrame, alternative: str = "two-sided", min_elections: int = MIN_ELECTIONS
) -> pd.DataFrame:
    """Sign test and t-test of ``he`` across elections, per (house, entity) (M-4.2, M-4.3).

    Implements METHODOLOGY M-4.2 and M-4.3 with the (house, election) pair as the unit
    (M-1.6). ``units`` is the output of :func:`lean_units`: one ``he`` per (house,
    ``lean_id``, election). A (house, ``lean_id``) with fewer than ``min_elections`` elections
    gets ``status = insufficient (< 3 elections)`` and is **not tested**: its test columns
    are empty, and only the descriptive columns (elections, mean, signs) are filled in.
    """
    _check_alternative(alternative)
    if min_elections < 2:
        raise ValueError("min_elections must be >= 2")
    if units.duplicated(["pollster_id", "lean_id", "election_id"]).any():
        raise MetricsInputError("several house effects for one (house, entity, election) unit")
    records = []
    for (house, lean_id), rows in units.groupby(["pollster_id", "lean_id"], sort=True):
        he = rows["he"].to_numpy(dtype=float)
        n = len(he)
        sign = sign_test(he, alternative)
        record: dict[str, object] = {
            "pollster_id": house,
            "lean_id": lean_id,
            "entities": ";".join(sorted(set(rows["entity_id"]))),
            "elections": ";".join(rows["election_id"]),
            "n_elections": n,
            "mean_he": float(he.mean()),
            "sd_he": float(he.std(ddof=1)) if n >= 2 else math.nan,
            "n_positive": sign.n_positive,
            "n_negative": sign.n_negative,
            "n_ties": sign.n_ties,
            "sign_p": math.nan,
            "sign_p_min": math.nan,
            "t_stat": math.nan,
            "t_df": pd.NA,
            "t_p": math.nan,
            "alternative": alternative,
            "status": STATUS_INSUFFICIENT,
            "preliminary": n <= PRELIMINARY_MAX_ELECTIONS,
        }
        if n >= min_elections:
            t = t_test(he, alternative)
            record.update(
                sign_p=sign.p,
                sign_p_min=sign.p_min,
                t_stat=t.statistic,
                t_df=t.df,
                t_p=t.p,
                status=STATUS_TESTED,
            )
        records.append(record)
    out = pd.DataFrame.from_records(records, columns=list(TEST_COLUMNS))
    for column in ("n_elections", "n_positive", "n_negative", "n_ties", "t_df"):
        out[column] = out[column].astype("Int64")
    out["preliminary"] = out["preliminary"].astype(bool)
    return out


def compute_significance(
    metrics: ErrorMetrics,
    config: MethodologyConfig | None = None,
    *,
    weighting: str = "recency",
    attribution: str = "party",
    alternative: str = "two-sided",
) -> Significance:
    """M-4.1 z-scores and the M-4.2/M-4.3 tests from the T-021 error metrics.

    ``metrics`` is :func:`compute_errors` of the prepared data; the house effects
    come from :func:`compute_relative` with ``weighting`` (M-2.5, M-2.8). ``config`` must be
    the configuration the data was prepared with (``Prepared.config``), for ``deff``.
    """
    if weighting not in WEIGHTINGS:
        raise ValueError(f"weighting must be one of {WEIGHTINGS}")
    _check_alternative(alternative)
    config = config or MethodologyConfig()
    relative = compute_relative(metrics, weighting)
    units = lean_units(relative.house_effects, attribution)
    return Significance(
        z_scores=poll_z_scores(metrics, config),
        lean_units=units,
        tests=cross_election_tests(units, alternative),
        deff=config.deff,
        weighting=weighting,
        attribution=attribution,
        alternative=alternative,
    )


# --- Summary and CLI ------------------------------------------------------------------------


def _fmt(value: object, spec: str = ".2f") -> str:
    return "-" if pd.isna(value) else format(value, spec)


def _final_poll_table(z_scores: pd.DataFrame) -> pd.DataFrame:
    finals = z_scores[z_scores["final_poll"]]
    records = []
    for (election, house, poll_id), rows in finals.groupby(
        ["election_id", "pollster_id", "poll_id"], sort=True
    ):
        defined = rows[rows["z_status"] == Z_OK]
        abs_z = defined["z"].abs()
        top = defined.loc[abs_z.idxmax()] if len(defined) else None
        records.append(
            {
                "election_id": election,
                "pollster_id": house,
                "poll_id": poll_id,
                "n": _fmt(rows["n"].iloc[0], ".0f"),
                "n_method": rows["n_method"].iloc[0],
                "k": len(rows),
                "outside_band": f"{int((abs_z > Z_BAND).sum())}/{len(defined)}",
                "max_abs_z": "-" if top is None else f"{abs(top['z']):.2f}",
                "at": "-" if top is None else top["entity_id"],
            }
        )
    return pd.DataFrame.from_records(records)


def summarize(result: Significance) -> str:
    """A plain-text report: z-scores of the final polls, then the cross-election tests."""
    out = io.StringIO()
    out.write(f"Significance tests (METHODOLOGY M-4.1 to M-4.3). {NOTE}\n\n")
    z = result.z_scores
    out.write(
        f"M-4.1 sampling z-scores: z = e / SE, SE = 100*sqrt(r(1-r)/n)*sqrt(deff), "
        f"deff = {result.deff:g}; {len(z)} rows of {z['poll_id'].nunique()} eligible polls, "
        f"{int((z['z_status'] == Z_NO_SAMPLE_SIZE).sum())} rows without a sample size.\n"
        f"n_method 'sample_size' overstates n, so it overstates |z|.\n"
    )
    finals = _final_poll_table(z)
    if finals.empty:
        out.write("No final polls.\n")
    else:
        out.write(
            f"Final poll of each (election, house): entities outside the 95% sampling band "
            f"(|z| > {Z_BAND}) and the largest |z|:\n"
        )
        out.write(finals.to_string(index=False) + "\n")
    tests = result.tests
    tested = int((tests["status"] == STATUS_TESTED).sum())
    out.write(
        f"\nM-4.2 sign test and M-4.3 t-test of the house effect he (M-2.5) across elections, "
        f"one value per (house, election) (M-1.6); {result.alternative}; entities identified "
        f"by {result.attribution}; market weights {result.weighting}. "
        f"{tested} of {len(tests)} (house, entity) combinations tested, "
        f"{len(tests) - tested} {STATUS_INSUFFICIENT}.\n"
    )
    if tests.empty:
        out.write("No house effects.\n")
        return out.getvalue()
    table = pd.DataFrame(
        {
            "house": tests["pollster_id"],
            "entity": tests["lean_id"],
            "elections": tests["n_elections"],
            "mean_he": tests["mean_he"].map(lambda v: _fmt(v, "+.2f")),
            "+/-/0": [
                f"{p}/{m}/{t}"
                for p, m, t in zip(
                    tests["n_positive"], tests["n_negative"], tests["n_ties"], strict=True
                )
            ],
            "sign_p": tests["sign_p"].map(lambda v: _fmt(v, ".3f")),
            "sign_p_min": tests["sign_p_min"].map(lambda v: _fmt(v, ".3f")),
            "t": tests["t_stat"].map(_fmt),
            "t_p": tests["t_p"].map(lambda v: _fmt(v, ".3f")),
            "status": tests["status"],
        }
    )
    out.write(table.to_string(index=False) + "\n")
    return out.getvalue()


def register(subparsers: "Subparsers") -> None:
    parser = subparsers.add_parser(
        "significance",
        help="Significance tests of poll errors and house effects (METHODOLOGY M-4.1 to M-4.3).",
        description=(
            "Prepare the data (M-1), compute the errors (M-2.1 to M-2.4) and the house effects "
            "(M-2.5), then compute the sampling z-score of every poll error (M-4.1) and, per "
            "(house, entity), a sign test (M-4.2) and a t-test (M-4.3) of the house effect "
            "across elections, one value per (house, election) (M-1.6). Combinations with "
            f"fewer than {MIN_ELECTIONS} elections are reported as insufficient, not tested. "
            "With --output, also write z_scores.csv, lean_units.csv and tests.csv to that "
            "directory."
        ),
    )
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data"), help="data directory (default: data)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="directory for the CSV outputs (e.g. build/significance)",
    )
    parser.add_argument(
        "--weighting",
        choices=WEIGHTINGS,
        default="recency",
        help="weights of the other houses in the market error of he (default: recency)",
    )
    parser.add_argument(
        "--attribution",
        choices=ATTRIBUTIONS,
        default="party",
        help="identify a candidate with its single supporting party across elections "
        "(party, default) or keep every entity separate (entity)",
    )
    parser.add_argument(
        "--alternative",
        choices=ALTERNATIVES,
        default="two-sided",
        help="alternative hypothesis of the sign test and the t-test (default: two-sided)",
    )
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    out = sys.stdout
    if isinstance(out, io.TextIOWrapper):
        out.reconfigure(errors="backslashreplace")
    try:
        prepared = prepare(args.data_dir)
        result = compute_significance(
            compute_errors(prepared),
            prepared.config,
            weighting=args.weighting,
            attribution=args.attribution,
            alternative=args.alternative,
        )
    except (PrepError, ValueError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1
    out.write(summarize(result))
    if args.output is not None:
        args.output.mkdir(parents=True, exist_ok=True)
        result.z_scores.to_csv(args.output / "z_scores.csv", index=False)
        result.lean_units.to_csv(args.output / "lean_units.csv", index=False)
        result.tests.to_csv(args.output / "tests.csv", index=False)
        out.write(f"\nwrote 3 CSV files to {args.output}\n")
    return 0
