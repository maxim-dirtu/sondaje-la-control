"""Market average and campaign house effect (METHODOLOGY M-3.1, M-3.2).

The **market average** (M-3.1) is the trend of the polls of several houses, fitted with one
additive offset per house (a partially linear model). Two steps, both linear in the poll
values:

1. **House offsets**, by backfitting with a Gaussian kernel mean (local constant) as the trend.
   The offsets of the houses in the fit sum to zero (equal weight per house), so the market is
   the level of the *average* house, whatever the number of polls each house published.
2. **Market curve**: a local linear smoother with a Gaussian kernel over the fieldwork end
   date, applied to the house-adjusted polls (each poll minus its house offset).

The **campaign house effect** (M-3.2) of house ``h`` for entity ``j`` at election ``E`` is the
mean deviation of ``h``'s campaign polls from the market fitted to the *other* houses' polls
(leave-one-house-out), with a standard error and a 90% interval.

Polls asked about a different ballot (a candidate later excluded or withdrawn with a large
share, M-1.5) form a separate *ballot regime*; the smoother never mixes regimes.

The input is the output of :func:`sondaje.prep.prepare` (``rows`` and ``adjustments``); no M-1
rule is recomputed here. Shares, deviations, and standard errors are in percentage points.
"""

import argparse
import io
import math
import sys
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from sondaje.prep import Prepared, PrepError, prepare

if TYPE_CHECKING:
    from sondaje.cli import Subparsers

LOCAL_LINEAR = "local_linear"
LOCAL_CONSTANT = "local_constant"

FINAL_BALLOT = "final_ballot"
"""Ballot regime of the polls that asked about the final ballot (M-3.1)."""
REGIME_PREFIX = "with:"
"""Prefix of the other ballot regimes, followed by the dropped entities joined with "+"."""
BALLOT_CHANGE_KINDS = ("excluded", "withdrawn")
"""M-1.5 adjustment kinds that reflect a change of the ballot during the campaign."""

STATUS_OK = "ok"
STATUS_FEW_POLLS = "few_polls"
STATUS_NO_REFERENCE = "no_reference"

CAMPAIGN_COLUMNS: tuple[str, ...] = (
    "poll_id",
    "pollster_id",
    "election_id",
    "regime",
    "entity_id",
    "fieldwork_end",
    "election_date",
    "days_before",
    "y",
    "var",
)
"""Columns of :func:`campaign_rows`: ``y`` is ``100·s`` (pp), ``var`` its sampling variance."""

DEVIATION_COLUMNS: tuple[str, ...] = (
    "poll_id",
    "pollster_id",
    "election_id",
    "regime",
    "entity_id",
    "fieldwork_end",
    "days_before",
    "y",
    "market_loho",
    "deviation",
    "evaluated",
    "method",
    "ref_houses",
)
"""Columns of :func:`house_deviations`."""

EFFECT_COLUMNS: tuple[str, ...] = (
    "pollster_id",
    "election_id",
    "entity_id",
    "che",
    "se",
    "ci90_low",
    "ci90_high",
    "se_sampling",
    "se_spread",
    "n_polls",
    "n_evaluated",
    "ref_houses",
    "status",
)
"""Columns of :func:`campaign_house_effects`."""

MARKET_COLUMNS: tuple[str, ...] = (
    "election_id",
    "regime",
    "entity_id",
    "date",
    "days_before",
    "market",
    "method",
    "houses",
    "polls",
)
"""Columns of :func:`market_curve`."""


@dataclass(frozen=True)
class MarketConfig:
    """Tunable parameters of M-3.1 and M-3.2 (METHODOLOGY, "Tunable parameters").

    ``campaign_days`` (M-3.2) and ``deff`` (M-4.1) are read from the
    :class:`~sondaje.config.MethodologyConfig` of the prepared bundle.
    """

    bandwidth_days: float = 14.0
    """Standard deviation of the Gaussian kernel, in days."""
    max_gap_days: float = 28.0
    """The market is defined at a date only if a poll of the fit lies within this many days."""
    max_extrapolation_days: float = 7.0
    """Local linear fit up to this many days outside the fit's date range; beyond, local
    constant (no trend extrapolation)."""
    regime_min_dropped: float = 10.0
    """Share (pp of the poll's share base) of an excluded or withdrawn entity from which a poll
    belongs to a separate ballot regime."""
    min_polls: int = 3
    """Evaluated polls below which a campaign house effect has status ``few_polls``."""
    interval_z: float = 1.645
    """Normal quantile of the reported interval (1.645: 90%, as in M-4.4)."""

    def __post_init__(self) -> None:
        if self.bandwidth_days <= 0:
            raise ValueError("bandwidth_days must be > 0")
        if self.max_gap_days < 0:
            raise ValueError("max_gap_days must be >= 0")
        if self.max_extrapolation_days < 0:
            raise ValueError("max_extrapolation_days must be >= 0")
        if self.regime_min_dropped < 0:
            raise ValueError("regime_min_dropped must be >= 0")
        if self.min_polls < 1:
            raise ValueError("min_polls must be >= 1")
        if self.interval_z <= 0:
            raise ValueError("interval_z must be > 0")


@dataclass(frozen=True)
class MarketResult:
    """Everything :func:`analyze` computes, as data frames (see the ``*_COLUMNS`` constants)."""

    campaign: pd.DataFrame
    market: pd.DataFrame
    deviations: pd.DataFrame
    effects: pd.DataFrame
    config: MarketConfig


# --- Input ----------------------------------------------------------------------------------


def ballot_regimes(adjustments: pd.DataFrame, config: MarketConfig | None = None) -> dict[str, str]:
    """The ballot regime of every poll that asked about a different ballot (M-3.1).

    A poll from which M-1.5 dropped at least ``regime_min_dropped`` pp for an ``excluded`` or
    ``withdrawn`` entity asked about a ballot that changed later in the campaign. Its regime is
    ``"with:" + "+".join(sorted(entities))``; polls not listed here are in :data:`FINAL_BALLOT`.
    """
    config = config or MarketConfig()
    if adjustments.empty:
        return {}
    dropped = adjustments[
        (adjustments["rule"] == "M-1.5")
        & adjustments["kind"].isin(BALLOT_CHANGE_KINDS)
        & (adjustments["share_raw"].astype(float) >= config.regime_min_dropped)
    ]
    entities: dict[str, set[str]] = defaultdict(set)
    for poll_id, entity in zip(dropped["poll_id"], dropped["entity_id"], strict=True):
        entities[poll_id].add(entity)
    return {poll_id: REGIME_PREFIX + "+".join(sorted(found)) for poll_id, found in entities.items()}


def campaign_rows(prepared: Prepared, config: MarketConfig | None = None) -> pd.DataFrame:
    """The M-3 input: one row per (eligible poll in the campaign window, compared entity).

    Implements the poll selection of METHODOLOGY M-3.2: eligible polls (M-1.3 OI-3/OI-4,
    M-1.7) with fieldwork ending at most ``campaign_days`` before election day. ``y`` is the
    normalized share in pp; ``var = 100² · s(1-s)/n · deff`` is its sampling variance (M-4.1),
    ``NaN`` when ``n`` is unknown.
    """
    config = config or MarketConfig()
    methodology = prepared.config
    rows = prepared.rows
    in_campaign = rows["days_before"].le(methodology.campaign_days).fillna(False).astype(bool)
    selected = rows[rows["eligible"].astype(bool) & in_campaign].copy()
    share = selected["s"].astype(float)
    selected["y"] = 100.0 * share
    selected["var"] = 1e4 * share * (1.0 - share) / selected["n"].astype(float) * methodology.deff
    selected["days_before"] = selected["days_before"].astype(int)
    regimes = ballot_regimes(prepared.adjustments, config)
    selected["regime"] = selected["poll_id"].map(regimes).fillna(FINAL_BALLOT)
    return selected[list(CAMPAIGN_COLUMNS)].reset_index(drop=True)


# --- Smoother -------------------------------------------------------------------------------


def smoother_weights(
    t: float, t_ref: np.ndarray, config: MarketConfig
) -> tuple[np.ndarray, str] | None:
    """Equivalent-kernel weights of the trend smoother at date ``t`` (M-3.1).

    ``t`` and ``t_ref`` are dates in days (here: minus the days before the election). The
    weights sum to 1, so the smoothed value is ``weights @ values``. Gaussian kernel with
    standard deviation ``bandwidth_days``; local linear when ``t`` lies at most
    ``max_extrapolation_days`` outside the range of ``t_ref`` and the fit has at least two
    distinct dates, local constant otherwise. ``None`` when no date of ``t_ref`` lies within
    ``max_gap_days`` of ``t`` (the smoother is not defined there).
    """
    if t_ref.size == 0 or float(np.min(np.abs(t_ref - t))) > config.max_gap_days:
        return None
    x = t_ref - t
    w = np.exp(-0.5 * (x / config.bandwidth_days) ** 2)
    outside = max(float(t_ref.min()) - t, t - float(t_ref.max()), 0.0)
    s0 = float(w.sum())
    if outside <= config.max_extrapolation_days:
        s1, s2 = float(w @ x), float(w @ (x * x))
        denominator = s0 * s2 - s1 * s1
        if denominator > 1e-9 * s0 * s2:
            return w * (s2 - s1 * x) / denominator, LOCAL_LINEAR
    return w / s0, LOCAL_CONSTANT


@dataclass(frozen=True)
class _Fit:
    """A market fit on one set of polls, as linear operators on the poll values ``y``."""

    t: np.ndarray
    houses: np.ndarray
    adjusted: np.ndarray
    """``Z = I - D·P``: maps ``y`` to the house-adjusted values ``y - δ_house``."""


def _fit(t: np.ndarray, houses: np.ndarray, config: MarketConfig) -> _Fit:
    """House offsets by backfitting with a local constant trend, solved exactly (M-3.1).

    The fixed point of ``f = K(y - Dδ)``, ``δ_h = mean_{i∈h}(y_i - f_i)`` with ``Σ_h δ_h = 0``
    (equal weight per house). ``K`` is the Gaussian kernel mean (local constant) at the fit's
    own dates, ``D`` the house indicator matrix. A local constant trend reproduces no slope, so
    a difference between houses that the polls cannot separate from a trend (e.g. houses with
    one poll each) is attributed to the houses, never to a trend. The offsets are linear in
    ``y``: ``δ = P·y``.
    """
    size = t.size
    kernel = np.exp(-0.5 * ((t[None, :] - t[:, None]) / config.bandwidth_days) ** 2)
    kernel /= kernel.sum(axis=1, keepdims=True)
    house_ids, index = np.unique(houses, return_inverse=True)
    indicator = np.zeros((size, house_ids.size))
    indicator[np.arange(size), index] = 1.0
    means = indicator.T / indicator.sum(axis=0)[:, None]
    lhs = np.vstack(
        [
            np.eye(house_ids.size) - means @ kernel @ indicator,
            np.full((1, house_ids.size), 1.0 / house_ids.size),
        ]
    )
    rhs = np.vstack([means @ (np.eye(size) - kernel), np.zeros((1, size))])
    offsets = np.linalg.lstsq(lhs, rhs, rcond=None)[0]
    return _Fit(t, houses, np.eye(size) - indicator @ offsets)


def _operator(fit: _Fit, t: float, config: MarketConfig) -> tuple[np.ndarray, str] | None:
    """Row ``L`` with ``market(t) = L @ y`` for a fit, and the smoother method; ``None``
    outside the support."""
    found = smoother_weights(t, fit.t, config)
    if found is None:
        return None
    weights, method = found
    return weights @ fit.adjusted, method


def _times(days_before: Iterable[int] | pd.Series) -> np.ndarray:
    return -np.asarray(list(days_before), dtype=float)


def _near_houses(fit: _Fit, t: float, config: MarketConfig) -> list[str]:
    near = np.abs(fit.t - t) <= config.max_gap_days
    return sorted(set(fit.houses[near].tolist()))


# --- Market average (M-3.1) -----------------------------------------------------------------


def market_curve(
    campaign: pd.DataFrame,
    config: MarketConfig | None = None,
    *,
    days_before: Iterable[int] | None = None,
    exclude_house: str | None = None,
) -> pd.DataFrame:
    """The market average per (election, regime, entity), in pp (METHODOLOGY M-3.1).

    ``campaign`` has the :data:`CAMPAIGN_COLUMNS` (see :func:`campaign_rows`). The curve is
    evaluated at every day between the first and the last poll of each group, or at
    ``days_before`` when given, and only where the smoother is defined. ``exclude_house`` fits
    the market without that house's polls (the leave-one-house-out market of M-3.2).
    """
    config = config or MarketConfig()
    records: list[dict[str, object]] = []
    for (election_id, regime, entity_id), group in campaign.groupby(
        ["election_id", "regime", "entity_id"], sort=True
    ):
        reference = group[group["pollster_id"] != exclude_house]
        if reference.empty:
            continue
        fit = _fit(_times(reference["days_before"]), reference["pollster_id"].to_numpy(), config)
        values = reference["y"].to_numpy(dtype=float)
        election_date = pd.Timestamp(group["election_date"].iloc[0])
        grid = (
            list(days_before)
            if days_before is not None
            else range(
                int(reference["days_before"].max()), int(reference["days_before"].min()) - 1, -1
            )
        )
        for day in grid:
            found = _operator(fit, -float(day), config)
            if found is None:
                continue
            row, method = found
            records.append(
                {
                    "election_id": election_id,
                    "regime": regime,
                    "entity_id": entity_id,
                    "date": election_date - pd.Timedelta(days=int(day)),
                    "days_before": int(day),
                    "market": float(row @ values),
                    "method": method,
                    "houses": int(reference["pollster_id"].nunique()),
                    "polls": len(reference),
                }
            )
    return pd.DataFrame.from_records(records, columns=list(MARKET_COLUMNS))


# --- Campaign house effect (M-3.2) ----------------------------------------------------------


def _deviations(
    campaign: pd.DataFrame, config: MarketConfig
) -> tuple[pd.DataFrame, dict[tuple[str, str, str], float]]:
    """Per-poll deviations from the leave-one-house-out market, and for each
    (house, election, entity) the sampling variance of the summed reference markets."""
    records: list[dict[str, object]] = []
    reference_var: dict[tuple[str, str, str], float] = defaultdict(float)
    for (election_id, regime, entity_id), group in campaign.groupby(
        ["election_id", "regime", "entity_id"], sort=True
    ):
        for house, own in group.groupby("pollster_id", sort=True):
            reference = group[group["pollster_id"] != house]
            fit = (
                _fit(_times(reference["days_before"]), reference["pollster_id"].to_numpy(), config)
                if not reference.empty
                else None
            )
            values = reference["y"].to_numpy(dtype=float)
            summed = np.zeros(len(reference))
            for poll in own.itertuples(index=False):
                t = -float(poll.days_before)
                found = _operator(fit, t, config) if fit is not None else None
                record = {
                    "poll_id": poll.poll_id,
                    "pollster_id": house,
                    "election_id": election_id,
                    "regime": regime,
                    "entity_id": entity_id,
                    "fieldwork_end": poll.fieldwork_end,
                    "days_before": int(poll.days_before),
                    "y": float(poll.y),
                    "market_loho": math.nan,
                    "deviation": math.nan,
                    "evaluated": False,
                    "method": None,
                    "ref_houses": "",
                }
                if found is not None and fit is not None:
                    row, method = found
                    market = float(row @ values)
                    summed += row
                    record.update(
                        market_loho=market,
                        deviation=float(poll.y) - market,
                        evaluated=True,
                        method=method,
                        ref_houses=",".join(_near_houses(fit, t, config)),
                    )
                records.append(record)
            if not reference.empty:
                variances = reference["var"].to_numpy(dtype=float)
                reference_var[(str(house), election_id, entity_id)] += float(
                    (summed**2) @ variances
                )
    frame = pd.DataFrame.from_records(records, columns=list(DEVIATION_COLUMNS))
    return frame, reference_var


def house_deviations(campaign: pd.DataFrame, config: MarketConfig | None = None) -> pd.DataFrame:
    """Each campaign poll's deviation from the market of the other houses (METHODOLOGY M-3.2).

    ``market_loho`` is the market average (M-3.1) fitted to the polls of every *other* house
    in the same (election, ballot regime, entity), evaluated at the poll's fieldwork end.
    ``evaluated`` is false where that market is not defined (no other house polled within
    ``max_gap_days``). ``ref_houses`` lists the other houses with a poll within that distance.
    """
    return _deviations(campaign, config or MarketConfig())[0]


def campaign_house_effects(
    campaign: pd.DataFrame, config: MarketConfig | None = None
) -> pd.DataFrame:
    """Campaign house effect per (house, election, entity), in pp (METHODOLOGY M-3.2).

    ``che`` is the unweighted mean of the house's evaluated deviations (:func:`house_deviations`)
    over the whole campaign window and every ballot regime. Its standard error ``se`` is the
    larger of

    - ``se_sampling``: the sampling error of ``che`` as a linear function of all the polls
      involved (the house's polls and the reference polls, with ``var`` from M-4.1), and
    - ``se_spread``: the standard deviation of the deviations divided by ``√m`` (``m ≥ 2``
      evaluated polls), which also captures changes of the deviation over time.

    ``ci90_low``/``ci90_high`` are ``che ± interval_z·se``. ``status`` is ``ok`` with at least
    ``min_polls`` evaluated polls, ``few_polls`` with fewer, and ``no_reference`` when no poll
    of the house could be compared with another house (``che`` is then empty).
    """
    config = config or MarketConfig()
    deviations, reference_var = _deviations(campaign, config)
    poll_var = campaign.set_index(["poll_id", "entity_id"])["var"].astype(float)
    records: list[dict[str, object]] = []
    for (house, election_id, entity_id), group in deviations.groupby(
        ["pollster_id", "election_id", "entity_id"], sort=True
    ):
        evaluated = group[group["evaluated"]]
        m = len(evaluated)
        houses = sorted(
            {name for names in evaluated["ref_houses"] for name in names.split(",") if name}
        )
        record: dict[str, object] = {
            "pollster_id": house,
            "election_id": election_id,
            "entity_id": entity_id,
            "che": math.nan,
            "se": math.nan,
            "ci90_low": math.nan,
            "ci90_high": math.nan,
            "se_sampling": math.nan,
            "se_spread": math.nan,
            "n_polls": len(group),
            "n_evaluated": m,
            "ref_houses": ",".join(houses),
            "status": STATUS_NO_REFERENCE,
        }
        if m:
            deviation = evaluated["deviation"].to_numpy(dtype=float)
            che = float(deviation.mean())
            keys = list(zip(evaluated["poll_id"], evaluated["entity_id"], strict=True))
            own_var = float(poll_var.loc[keys].sum(skipna=False))
            sampling = math.sqrt(
                (own_var + reference_var[(str(house), election_id, entity_id)]) / m**2
            )
            spread = float(deviation.std(ddof=1)) / math.sqrt(m) if m >= 2 else math.nan
            candidates = [value for value in (sampling, spread) if not math.isnan(value)]
            se = max(candidates) if candidates else math.nan
            record.update(
                che=che,
                se=se,
                ci90_low=che - config.interval_z * se,
                ci90_high=che + config.interval_z * se,
                se_sampling=sampling,
                se_spread=spread,
                status=STATUS_OK if m >= config.min_polls else STATUS_FEW_POLLS,
            )
        records.append(record)
    return pd.DataFrame.from_records(records, columns=list(EFFECT_COLUMNS))


def analyze(prepared: Prepared, config: MarketConfig | None = None) -> MarketResult:
    """M-3.1 and M-3.2 on a prepared bundle: campaign rows, market curves, deviations, effects."""
    config = config or MarketConfig()
    campaign = campaign_rows(prepared, config)
    return MarketResult(
        campaign=campaign,
        market=market_curve(campaign, config),
        deviations=house_deviations(campaign, config),
        effects=campaign_house_effects(campaign, config),
        config=config,
    )


# --- Summary and CLI ------------------------------------------------------------------------


def summarize(result: MarketResult) -> str:
    """A plain-text table of the campaign house effects (pp, 90% interval)."""
    effects = result.effects
    out = io.StringIO()
    config = result.config
    out.write(
        "Campaign house effect (METHODOLOGY M-3.2): mean deviation of a house's campaign polls\n"
        "from the market average of the other houses, in pp, with a 90% interval. Positive: the\n"
        f"house shows the entity higher than the other houses. Bandwidth "
        f"{config.bandwidth_days:g} days.\n\n"
    )
    if effects.empty:
        out.write("(no campaign polls)\n")
        return out.getvalue()
    table = effects.assign(
        che=effects["che"].round(1),
        se=effects["se"].round(1),
        ci90=[
            "" if math.isnan(low) else f"[{low:+.1f}, {high:+.1f}]"
            for low, high in zip(effects["ci90_low"], effects["ci90_high"], strict=True)
        ],
        polls=[f"{m}/{n}" for m, n in zip(effects["n_evaluated"], effects["n_polls"], strict=True)],
    )
    columns = ["election_id", "entity_id", "pollster_id", "che", "se", "ci90", "polls"]
    columns += ["ref_houses", "status"]
    for election_id, group in table.groupby("election_id", sort=True):
        out.write(f"{election_id}\n")
        out.write(group[columns[1:]].to_string(index=False, na_rep="-") + "\n\n")
    return out.getvalue()


def register(subparsers: "Subparsers") -> None:
    parser = subparsers.add_parser(
        "market",
        help="Market average and campaign house effect (METHODOLOGY M-3.1, M-3.2).",
        description=(
            "Prepare data/ (METHODOLOGY M-1), fit the market average of every election, ballot "
            "regime and entity (M-3.1), and print each house's campaign house effect with its "
            "90%% interval (M-3.2). With --output, also write campaign.csv, market.csv, "
            "deviations.csv and effects.csv to that directory."
        ),
    )
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data"), help="data directory (default: data)"
    )
    parser.add_argument(
        "--output", type=Path, default=None, help="directory for the CSV outputs (e.g. build/m3)"
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
    result = analyze(prepared)
    out.write(summarize(result))
    if args.output is not None:
        args.output.mkdir(parents=True, exist_ok=True)
        for name, frame in (
            ("campaign", result.campaign),
            ("market", result.market),
            ("deviations", result.deviations),
            ("effects", result.effects),
        ):
            frame.to_csv(args.output / f"{name}.csv", index=False, lineterminator="\n")
        out.write("wrote campaign.csv, market.csv, deviations.csv, effects.csv to ")
        out.write(f"{args.output}\n")
    return 0
