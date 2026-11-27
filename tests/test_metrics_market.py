"""Tests for the market average and the campaign house effect (sondaje.metrics.market, M-3).

The synthetic campaigns are built directly as M-3 input tables (:data:`CAMPAIGN_COLUMNS`); the
integration tests at the end go through :func:`sondaje.prep.prepare` with fictitious data
(dated 2099), and the last test runs on the real data with generic invariants only.
"""

import math
from collections.abc import Callable, Iterable
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from sondaje.cli import main
from sondaje.config import MethodologyConfig
from sondaje.metrics.market import (
    CAMPAIGN_COLUMNS,
    FINAL_BALLOT,
    LOCAL_CONSTANT,
    LOCAL_LINEAR,
    STATUS_FEW_POLLS,
    STATUS_NO_REFERENCE,
    STATUS_OK,
    MarketConfig,
    analyze,
    ballot_regimes,
    campaign_house_effects,
    campaign_rows,
    house_deviations,
    market_curve,
    smoother_weights,
)
from sondaje.prep import prepare
from test_prep import Synth, candidate

REPO_ROOT = Path(__file__).resolve().parents[1]
ELECTION = "pres-2099-r1"
ELECTION_DATE = pd.Timestamp("2099-11-01")
DEFF = 1.5

type Trend = Callable[[float], float]


def campaign(
    polls: Iterable[tuple[str, int, dict[str, float]]],
    *,
    election_id: str = ELECTION,
    regime: str = FINAL_BALLOT,
    n: int = 1000,
) -> pd.DataFrame:
    """An M-3 input table from (house, days before election, {entity: share in pp})."""
    records = []
    for house, days, shares in polls:
        poll_id = f"{house}-{election_id}-d{days:03d}-{regime}"
        for entity, y in shares.items():
            s = y / 100.0
            records.append(
                {
                    "poll_id": poll_id,
                    "pollster_id": house,
                    "election_id": election_id,
                    "regime": regime,
                    "entity_id": entity,
                    "fieldwork_end": ELECTION_DATE - pd.Timedelta(days=days),
                    "election_date": ELECTION_DATE,
                    "days_before": days,
                    "y": y,
                    "var": 1e4 * s * (1 - s) / n * DEFF,
                }
            )
    return pd.DataFrame.from_records(records, columns=list(CAMPAIGN_COLUMNS))


OFFSETS = {"alfa": 3.0, "beta": 1.0, "gama": -1.0, "delta": 0.0}
"""House offsets in pp: ``alfa`` is the house under test; the others average to zero."""


def schedule(every: int = 6) -> list[tuple[str, int]]:
    """Each house polls every ``every`` days over 120 days, at staggered dates."""
    return [
        (house, days)
        for start, house in zip(range(len(OFFSETS)), OFFSETS, strict=True)
        for days in range(118 - start, 0, -every)
    ]


def offset_campaign(trend: Trend, noise: np.random.Generator | None = None) -> pd.DataFrame:
    polls = []
    for house, days in schedule():
        y = trend(days) + OFFSETS[house]
        if noise is not None:
            y += noise.normal(0.0, math.sqrt(1e4 * y / 100 * (1 - y / 100) / 3000 * DEFF))
        polls.append((house, days, {"x": y}))
    return campaign(polls, n=3000)


def linear_trend(days: float) -> float:
    return 25.0 + 0.08 * (120 - days)  # +9.6 pp over the campaign


def curved_trend(days: float) -> float:
    return 25.0 + 0.06 * (120 - days) + 2.0 * math.sin(2 * math.pi * (120 - days) / 120)


def effect(effects: pd.DataFrame, house: str, entity: str = "x") -> pd.Series:
    found = effects[(effects["pollster_id"] == house) & (effects["entity_id"] == entity)]
    assert len(found) == 1
    return found.iloc[0]


# --- Smoother -------------------------------------------------------------------------------


def test_smoother_weights_sum_to_one_and_reproduce_a_line() -> None:
    t_ref = np.array([-60.0, -50.0, -41.0, -30.0, -12.0])
    weights, method = smoother_weights(-45.0, t_ref, MarketConfig())
    assert method == LOCAL_LINEAR
    assert weights.sum() == pytest.approx(1.0)
    assert weights @ (3.0 + 0.5 * t_ref) == pytest.approx(3.0 + 0.5 * -45.0)


def test_smoother_extrapolates_a_line_only_a_short_distance() -> None:
    t_ref = np.array([-40.0, -30.0, -20.0])
    config = MarketConfig()  # max_extrapolation_days 7
    weights, method = smoother_weights(-13.0, t_ref, config)
    assert method == LOCAL_LINEAR
    assert weights @ t_ref == pytest.approx(-13.0)
    weights, method = smoother_weights(-12.0, t_ref, config)
    assert method == LOCAL_CONSTANT
    assert (weights > 0).all()
    assert weights.sum() == pytest.approx(1.0)


def test_smoother_is_local_constant_with_a_single_date() -> None:
    weights, method = smoother_weights(-10.0, np.array([-12.0, -12.0]), MarketConfig())
    assert method == LOCAL_CONSTANT
    assert weights.tolist() == pytest.approx([0.5, 0.5])


def test_smoother_is_undefined_beyond_the_maximum_gap() -> None:
    t_ref = np.array([-100.0, -90.0])
    assert smoother_weights(-62.0, t_ref, MarketConfig()) is not None  # 28 days: inside
    assert smoother_weights(-61.0, t_ref, MarketConfig()) is None
    assert smoother_weights(-61.0, np.array([]), MarketConfig()) is None


def test_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="bandwidth_days"):
        MarketConfig(bandwidth_days=0)
    with pytest.raises(ValueError, match="min_polls"):
        MarketConfig(min_polls=0)


# --- Acceptance: a constant offset over a moving trend --------------------------------------


def test_constant_offset_over_a_linear_trend_is_recovered() -> None:
    effects = campaign_house_effects(offset_campaign(linear_trend))
    alfa = effect(effects, "alfa")
    # The reference houses beta, gama, delta have offsets +1, -1, 0 (mean 0).
    assert alfa["che"] == pytest.approx(3.0, abs=0.01)
    assert alfa["status"] == STATUS_OK
    assert alfa["n_evaluated"] == alfa["n_polls"] == 20
    # Each house is measured against the average of the *other* three.
    assert effect(effects, "beta")["che"] == pytest.approx(1.0 - (3.0 - 1.0 + 0.0) / 3, abs=0.01)


def test_constant_offset_over_a_curved_trend_is_recovered_within_half_a_point() -> None:
    alfa = effect(campaign_house_effects(offset_campaign(curved_trend)), "alfa")
    assert abs(alfa["che"] - 3.0) <= 0.5


def test_constant_offset_with_sampling_noise_is_recovered_within_half_a_point() -> None:
    noisy = offset_campaign(curved_trend, np.random.default_rng(2099))
    alfa = effect(campaign_house_effects(noisy), "alfa")
    assert abs(alfa["che"] - 3.0) <= 0.5
    assert alfa["ci90_low"] < 3.0 < alfa["ci90_high"]
    assert alfa["se"] == max(alfa["se_sampling"], alfa["se_spread"])


def test_market_average_follows_the_trend_at_the_level_of_the_average_house() -> None:
    market = market_curve(offset_campaign(linear_trend), days_before=[100, 60, 20])
    # All four houses: offsets 3, 1, -1, 0 average to +0.75.
    expected = [linear_trend(d) + 0.75 for d in (100, 60, 20)]
    assert market["market"].tolist() == pytest.approx(expected, abs=0.01)
    assert set(market["houses"]) == {4}


def test_market_average_is_not_dominated_by_the_most_frequent_house() -> None:
    # Flat trend at 30; beta polls 20 times at +4, gama and delta twice each at 0 and -1.
    polls = [("beta", d, {"x": 34.0}) for d in range(100, 0, -5)]
    polls += [("gama", d, {"x": 30.0}) for d in (80, 30)]
    polls += [("delta", d, {"x": 29.0}) for d in (70, 20)]
    market = market_curve(campaign(polls), days_before=[50])
    assert market["market"].iloc[0] == pytest.approx(30.0 + (4.0 + 0.0 - 1.0) / 3)


# --- Leave-one-house-out --------------------------------------------------------------------


def test_leave_one_house_out_market_is_the_market_without_that_house() -> None:
    data = offset_campaign(curved_trend, np.random.default_rng(7))
    deviations = house_deviations(data)
    alfa = deviations[deviations["pollster_id"] == "alfa"].sort_values("days_before")
    days = alfa["days_before"].tolist()
    without = market_curve(data[data["pollster_id"] != "alfa"], days_before=days)
    excluded = market_curve(data, days_before=days, exclude_house="alfa")
    assert without["days_before"].tolist() == days
    assert alfa["market_loho"].tolist() == pytest.approx(without["market"].tolist())
    assert excluded["market"].tolist() == pytest.approx(without["market"].tolist())
    che = effect(campaign_house_effects(data), "alfa")["che"]
    assert che == pytest.approx((alfa["y"].to_numpy() - without["market"].to_numpy()).mean())


def test_a_house_own_polls_never_move_its_reference_market() -> None:
    data = offset_campaign(curved_trend, np.random.default_rng(11))
    shifted = data.copy()
    is_alfa = shifted["pollster_id"] == "alfa"
    shifted.loc[is_alfa, "y"] += 20.0
    before, after = house_deviations(data), house_deviations(shifted)
    own = before["pollster_id"] == "alfa"
    assert after.loc[own, "market_loho"].tolist() == pytest.approx(
        before.loc[own, "market_loho"].tolist()
    )
    assert effect(campaign_house_effects(shifted), "alfa")["che"] == pytest.approx(
        effect(campaign_house_effects(data), "alfa")["che"] + 20.0
    )
    # alfa is part of every other house's reference.
    others = ~own
    assert not np.allclose(after.loc[others, "market_loho"], before.loc[others, "market_loho"])


# --- Uncertainty ----------------------------------------------------------------------------


def test_sampling_error_is_that_of_a_linear_function_of_all_polls() -> None:
    data = campaign(
        [
            ("alfa", 40, {"x": 33.0}),
            ("alfa", 20, {"x": 36.0}),
            ("beta", 45, {"x": 30.0}),
            ("beta", 25, {"x": 31.0}),
            ("gama", 35, {"x": 29.0}),
            ("gama", 15, {"x": 32.0}),
        ]
    )
    base = effect(campaign_house_effects(data), "alfa")
    # che is linear in the poll values: its gradient is found by moving one poll at a time.
    variance = 0.0
    for index in data.index:
        moved = data.copy()
        moved.loc[index, "y"] += 1.0
        gradient = effect(campaign_house_effects(moved), "alfa")["che"] - base["che"]
        variance += gradient**2 * data.loc[index, "var"]
    assert base["se_sampling"] == pytest.approx(math.sqrt(variance))
    deviations = house_deviations(data)
    spread = deviations[deviations["pollster_id"] == "alfa"]["deviation"].std(ddof=1)
    assert base["se_spread"] == pytest.approx(spread / math.sqrt(2))
    assert base["se"] == pytest.approx(max(base["se_sampling"], base["se_spread"]))
    assert base["ci90_high"] - base["che"] == pytest.approx(1.645 * base["se"])


# --- Edge cases -----------------------------------------------------------------------------


def test_polls_with_no_other_house_nearby_are_not_evaluated() -> None:
    # alfa is the only house polling 110 to 90 days out; beta and gama start 30 days out.
    polls = [("alfa", d, {"x": 30.0}) for d in (110, 100, 90, 20, 10)]
    polls += [("beta", d, {"x": 28.0}) for d in (30, 18, 6)]
    polls += [("gama", d, {"x": 29.0}) for d in (25, 12, 3)]
    data = campaign(polls)
    deviations = house_deviations(data)
    alfa = deviations[deviations["pollster_id"] == "alfa"].set_index("days_before")
    assert alfa["evaluated"].to_dict() == {110: False, 100: False, 90: False, 20: True, 10: True}
    assert alfa.loc[110, "market_loho"] != alfa.loc[110, "market_loho"]  # NaN
    result = effect(campaign_house_effects(data), "alfa")
    assert (result["n_polls"], result["n_evaluated"]) == (5, 2)
    assert result["status"] == STATUS_FEW_POLLS
    assert result["ref_houses"] == "beta,gama"
    # The market is not defined where only the excluded house polled.
    assert market_curve(data, days_before=[100], exclude_house="alfa").empty


def test_a_house_alone_in_its_period_or_on_its_entity_has_no_reference() -> None:
    polls = [("alfa", d, {"x": 30.0, "solo": 4.0}) for d in (110, 100)]
    polls += [("beta", d, {"x": 28.0}) for d in (40, 20)]
    effects = campaign_house_effects(campaign(polls))
    for entity in ("x", "solo"):
        alfa = effect(effects, "alfa", entity)
        assert alfa["status"] == STATUS_NO_REFERENCE
        assert alfa["n_evaluated"] == 0
        assert math.isnan(alfa["che"])
        assert math.isnan(alfa["se"])


def test_election_with_very_few_polls() -> None:
    # Like parl-2024-cd: three houses, one poll each, all near the end of the campaign.
    data = campaign(
        [
            ("alfa", 3, {"x": 22.0, "y": 21.0}),
            ("beta", 9, {"x": 20.0, "y": 30.0}),
            ("gama", 26, {"x": 15.0, "y": 32.0}),
        ]
    )
    effects = campaign_house_effects(data)
    assert set(effects["status"]) == {STATUS_FEW_POLLS}
    assert effects["n_evaluated"].tolist() == [1] * 6
    assert effects["che"].notna().all()
    assert (effects["se"] > 0).all()
    assert effects["se_spread"].isna().all()
    assert (effects["se"] == effects["se_sampling"]).all()
    alfa = effect(effects, "alfa")
    # Reference beta and gama, one poll each: their offsets absorb their own values, the trend
    # through them is flat, so the market is their mean.
    assert alfa["che"] == pytest.approx(22.0 - (20.0 + 15.0) / 2)


def test_round_two_head_to_head_effects_are_mirror_images() -> None:
    rng = np.random.default_rng(5)
    plan = {
        "alfa": (2.0, (13, 6, 3)),
        "beta": (-1.0, (9, 4)),
        "gama": (0.5, (7,)),
        "delta": (0.0, (12, 5, 2)),
    }
    polls = []
    for house, (offset, days_list) in plan.items():
        for days in days_list:
            ion = 50.0 + 0.2 * (14 - days) + offset + rng.normal(0.0, 1.0)
            polls.append((house, days, {"ion": ion, "maria": 100.0 - ion}))
    data = campaign(polls, election_id="pres-2099-r2")
    effects = campaign_house_effects(data).set_index(["pollster_id", "entity_id"])
    for house in ("alfa", "beta", "gama", "delta"):
        ion, maria = effects.loc[(house, "ion")], effects.loc[(house, "maria")]
        assert ion["che"] == pytest.approx(-maria["che"])
        assert ion["se"] == pytest.approx(maria["se"])
    market = market_curve(data).pivot_table(
        index="days_before", columns="entity_id", values="market"
    )
    assert (market["ion"] + market["maria"]).tolist() == pytest.approx([100.0] * len(market))


def test_ballot_regimes_come_from_large_exclusions_and_withdrawals() -> None:
    adjustments = pd.DataFrame(
        {
            "poll_id": ["p1", "p1", "p2", "p3", "p4", "p5"],
            "rule": ["M-1.5", "M-1.5", "M-1.5", "M-1.5", "M-1.5", "M-1.2"],
            "kind": [
                "excluded",
                "withdrawn",
                "excluded",
                "not_registered",
                "excluded",
                "below_threshold",
            ],
            "entity_id": ["vasile", "dan", "vasile", "petre", "vasile", "omega"],
            "target_id": [None] * 6,
            "share_raw": [30.0, 12.0, 9.9, 40.0, 10.0, 15.0],
            "detail": [""] * 6,
        }
    )
    assert ballot_regimes(adjustments) == {"p1": "with:dan+vasile", "p4": "with:vasile"}
    assert ballot_regimes(adjustments, MarketConfig(regime_min_dropped=5.0))["p2"] == "with:vasile"


def test_the_market_never_mixes_ballot_regimes() -> None:
    before = campaign(
        [("alfa", d, {"x": 10.0}) for d in (80, 70)] + [("beta", d, {"x": 12.0}) for d in (75, 65)],
        regime="with:vasile",
    )
    after = campaign(
        [("alfa", d, {"x": 30.0}) for d in (55, 40)] + [("beta", d, {"x": 31.0}) for d in (50, 45)]
    )
    data = pd.concat([before, after], ignore_index=True)
    deviations = house_deviations(data).set_index(["pollster_id", "days_before"])
    # alfa's poll 55 days out is 10 days from beta's pre-change poll, but only after-change
    # polls are its reference.
    assert deviations.loc[("alfa", 55), "market_loho"] == pytest.approx(31.0)
    assert deviations.loc[("alfa", 70), "market_loho"] == pytest.approx(12.0)
    alfa = effect(campaign_house_effects(data), "alfa")
    assert alfa["che"] == pytest.approx(((10 - 12) * 2 + (30 - 31) * 2) / 4)
    assert alfa["n_evaluated"] == 4


# --- Through sondaje.prep -------------------------------------------------------------------


def presidential_campaign() -> Synth:
    """Round 1 on 2099-11-01 (ion .40, maria .35, ana .25 domestic); vasile is excluded.

    Houses exemplar, secundar, tertiar poll from 150 to 3 days out; vasile is asked about
    until 60 days out (with a large share, so those polls form their own ballot regime).
    """
    synth = Synth()
    synth.election(ELECTION, "presidential", 1, "2099-11-01")
    for entity in ("ion", "maria", "ana", "vasile"):
        synth.entity(entity, "candidate")
    synth.results(ELECTION, {"ion": (400, 50), "maria": (350, 50), "ana": (250, 0)})
    synth.map(ELECTION, "vasile", "excluded")
    plan = {
        "exemplar": [(150, 40), (90, 42), (70, 41), (40, 44), (20, 45), (5, 44)],
        "secundar": [(85, 38), (65, 37), (35, 40), (15, 41), (3, 40)],
        "tertiar": [(80, 39), (60, 38), (30, 39), (10, 40)],
    }
    for house, polls in plan.items():
        for days, ion in polls:
            options = [candidate("ion", str(ion)), candidate("maria", "30")]
            options.append(candidate("ana", str(100 - ion - 30 - (20 if days > 60 else 0))))
            if days > 60:
                options.append(candidate("vasile", "20"))
            date = synthetic_date(days)
            synth.poll(
                synthetic_poll_id(house, days),
                ELECTION,
                {"expressed_option": options},
                fieldwork_end=date,
                published=date,
            )
    synth.poll(
        synthetic_poll_id("exemplar", 1),
        ELECTION,
        {"expressed_option": [candidate("ion", "60"), candidate("maria", "40")]},
        fieldwork_end=synthetic_date(1),
        published="2099-11-01",
    )
    return synth


def synthetic_date(days: int) -> str:
    return (ELECTION_DATE - pd.Timedelta(days=days)).date().isoformat()


def synthetic_poll_id(house: str, days: int) -> str:
    return f"{house}-{ELECTION}-{synthetic_date(days).replace('-', '')}"


@pytest.fixture
def prepared_campaign(tmp_path: Path):
    return prepare(presidential_campaign().write(tmp_path / "data"))


def test_campaign_rows_select_eligible_polls_inside_the_campaign_window(
    prepared_campaign,
) -> None:
    rows = campaign_rows(prepared_campaign)
    assert list(rows.columns) == list(CAMPAIGN_COLUMNS)
    polls = set(rows["poll_id"])
    assert synthetic_poll_id("exemplar", 150) not in polls  # outside the 120-day campaign
    assert synthetic_poll_id("exemplar", 1) not in polls  # published on election day (M-1.7)
    assert len(polls) == 14
    assert rows["days_before"].max() <= prepared_campaign.config.campaign_days
    prepared_rows = prepared_campaign.rows.set_index(["poll_id", "entity_id"])
    for row in rows.itertuples(index=False):
        s = prepared_rows.loc[(row.poll_id, row.entity_id), "s"]
        n = prepared_rows.loc[(row.poll_id, row.entity_id), "n"]
        assert row.y == pytest.approx(100 * s)
        assert row.var == pytest.approx(1e4 * s * (1 - s) / n * 1.5)
    regimes = rows.groupby("poll_id")["regime"].first()
    early = rows.groupby("poll_id")["days_before"].first() > 60
    assert set(regimes[early]) == {"with:vasile"}
    assert set(regimes[~early]) == {FINAL_BALLOT}


def test_campaign_window_follows_the_methodology_config(tmp_path: Path) -> None:
    data_dir = presidential_campaign().write(tmp_path / "data")
    narrow = prepare(data_dir, MethodologyConfig(campaign_days=30))
    assert campaign_rows(narrow)["days_before"].max() == 30


def test_analyze_on_prepared_data(prepared_campaign) -> None:
    result = analyze(prepared_campaign)
    effects = result.effects
    assert set(effects["pollster_id"]) == {"exemplar", "secundar", "tertiar"}
    assert set(effects["entity_id"]) == {"ion", "maria", "ana"}
    exemplar = effects[(effects["pollster_id"] == "exemplar") & (effects["entity_id"] == "ion")]
    assert exemplar["che"].iloc[0] > 0  # exemplar shows ion higher than the other two houses
    assert set(result.market["regime"]) == {FINAL_BALLOT, "with:vasile"}
    assert set(result.deviations["regime"]) == {FINAL_BALLOT, "with:vasile"}


def test_cli_writes_the_tables(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    data_dir = presidential_campaign().write(tmp_path / "data")
    out_dir = tmp_path / "out"
    assert main(["market", "--data-dir", str(data_dir), "--output", str(out_dir)]) == 0
    assert "Campaign house effect" in capsys.readouterr().out
    for name in ("campaign", "market", "deviations", "effects"):
        assert (out_dir / f"{name}.csv").exists()
    assert len(pd.read_csv(out_dir / "effects.csv")) == 9


def test_cli_reports_errors(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    assert main(["market", "--data-dir", str(tmp_path / "missing")]) == 1
    assert "error" in capsys.readouterr().err


# --- Real data (smoke test; generic invariants only) ----------------------------------------


def test_real_data_invariants() -> None:
    data = REPO_ROOT / "data"
    if not any(data.glob("polls/*/polls.csv")):
        pytest.skip("no poll data")
    result = analyze(prepare(data))
    effects = result.effects
    assert not effects.empty
    assert set(effects["status"]) <= {STATUS_OK, STATUS_FEW_POLLS, STATUS_NO_REFERENCE}
    evaluated = effects[effects["status"] != STATUS_NO_REFERENCE]
    assert evaluated["che"].notna().all()
    assert (evaluated["se"] > 0).all()
    assert (evaluated["ci90_low"] < evaluated["che"]).all()
    assert result.deviations["poll_id"].isin(result.campaign["poll_id"]).all()
    # Two-candidate rounds: a house's effects on the two candidates mirror each other.
    for (_, election_id), group in effects.groupby(["pollster_id", "election_id"]):
        if group["entity_id"].nunique() == 2 and election_id.endswith("-r2"):
            assert group["che"].sum() == pytest.approx(0.0, abs=1e-9)
