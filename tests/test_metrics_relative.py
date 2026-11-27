"""Tests for the comparisons between houses (sondaje.metrics.relative, METHODOLOGY M-2.5,
M-2.6, M-2.8).

Every expected value is computed by hand in the comments. Unit tests use small hand-built
prepared tables with several houses; the integration tests run the full pipeline on the
synthetic 2099 dataset of ``test_prep`` (all names, dates, and figures are fictitious).
"""

import math
from pathlib import Path
from typing import NamedTuple

import pandas as pd
import pytest

from sondaje.cli import main
from sondaje.config import MethodologyConfig
from sondaje.metrics.errors import ErrorMetrics, MetricsInputError, compute_errors
from sondaje.metrics.relative import (
    COMPARISON_SET_COLUMNS,
    HOUSE_EFFECT_COLUMNS,
    NOT_SIGNIFICANCE,
    RELATIVE_ACCURACY_COLUMNS,
    RelativeMetrics,
    common_entity_errors,
    comparison_sets,
    compute_relative,
    house_effects,
    summarize,
)
from sondaje.prep import OTHERS, Prepared, prepare
from test_prep import synthetic

REPO_ROOT = Path(__file__).resolve().parents[1]
ELECTION = "elec-2099"

type Entities = list[tuple[str, float, float]]


class FinalPoll(NamedTuple):
    """The final poll of ``house``: [(entity, s, r)], with its recency weight."""

    house: str
    entities: Entities
    weight: float = 0.5
    election: str = ELECTION


final_poll = FinalPoll


def metrics_of(*polls: FinalPoll) -> ErrorMetrics:
    """T-021 error metrics of hand-built final polls (one per house and election)."""
    poll_rows, entity_rows = [], []
    for house, entities, weight, election in polls:
        info = {
            "poll_id": f"{house}-{election}",
            "pollster_id": house,
            "election_id": election,
            "unit_id": f"{house}:{election}",
            "fieldwork_end": pd.Timestamp("2099-01-01"),
            "days_before": round(-7 * math.log(weight)),
            "weight": weight,
            "in_window": True,
            "final_poll": True,
            "target_scope": "domestic",
            "has_lt": False,
            "n": 1000.0,
            "n_method": "sample_size",
            "eligible": True,
        }
        poll_rows.append({**info, "k": len(entities)})
        for entity, s, r in entities:
            entity_rows.append(
                {
                    **info,
                    "entity_id": entity,
                    "supporting_party_id": None,
                    "share_raw": 100 * s,
                    "s": s,
                    "r": r,
                    "adjusted": False,
                }
            )
    prepared = Prepared(
        pd.DataFrame(entity_rows), pd.DataFrame(poll_rows), pd.DataFrame(), MethodologyConfig()
    )
    return compute_errors(prepared)


def he_of(relative: RelativeMetrics, house: str, election: str = ELECTION) -> dict[str, float]:
    he = relative.house_effects
    rows = he[(he["pollster_id"] == house) & (he["election_id"] == election)]
    return dict(zip(rows["entity_id"], rows["he"], strict=True))


def ra_row(relative: RelativeMetrics, house: str, election: str = ELECTION) -> pd.Series:
    ra = relative.relative_accuracy
    return ra[(ra["pollster_id"] == house) & (ra["election_id"] == election)].iloc[0]


# Result shares used by most unit tests: alfa .40, beta .35, gama .20, others .05.
R = {"alfa": 0.40, "beta": 0.35, "gama": 0.20, OTHERS: 0.05}


def poll(alfa: float, beta: float, gama: float, others: float) -> Entities:
    return [
        ("alfa", alfa, R["alfa"]),
        ("beta", beta, R["beta"]),
        ("gama", gama, R["gama"]),
        (OTHERS, others, R[OTHERS]),
    ]


# --- Output tables --------------------------------------------------------------------------


def test_output_tables_have_the_documented_columns() -> None:
    relative = compute_relative(
        metrics_of(
            final_poll("a", poll(0.42, 0.33, 0.20, 0.05)), final_poll("b", poll(*R.values()))
        )
    )
    assert tuple(relative.comparison_sets.columns) == COMPARISON_SET_COLUMNS
    assert tuple(relative.house_effects.columns) == HOUSE_EFFECT_COLUMNS
    assert tuple(relative.relative_accuracy.columns) == RELATIVE_ACCURACY_COLUMNS
    for column in (*COMPARISON_SET_COLUMNS, *HOUSE_EFFECT_COLUMNS, *RELATIVE_ACCURACY_COLUMNS):
        assert f"``{column}``" in (RelativeMetrics.__doc__ or ""), column


# --- M-2.5 acceptance criteria --------------------------------------------------------------


def test_m25_same_error_for_every_house_gives_zero_house_effects() -> None:
    # Every house: e = +2, -2, +1, -1 (alfa, beta, gama, others), with different weights.
    same = poll(0.42, 0.33, 0.21, 0.04)
    relative = compute_relative(
        metrics_of(
            final_poll("a", same, weight=0.9),
            final_poll("b", same, weight=0.5),
            final_poll("c", same, weight=0.1),
        )
    )
    assert relative.house_effects["he"].tolist() == pytest.approx([0.0] * 12, abs=1e-12)
    assert relative.house_effects["market_e"].abs().gt(0).all()  # an industry-wide miss
    assert relative.relative_accuracy["ra"].tolist() == pytest.approx([0.0] * 3, abs=1e-12)


def test_m25_same_error_with_different_results_gives_zero_house_effects() -> None:
    # House b is compared with another result (say, the total instead of the domestic one),
    # but its errors are the same as a's: e = +2 on x, -2 on y. Its house effect is 0.
    relative = compute_relative(
        metrics_of(
            final_poll("a", [("x", 0.52, 0.50), ("y", 0.48, 0.50)]),
            final_poll("b", [("x", 0.62, 0.60), ("y", 0.38, 0.40)]),
        )
    )
    assert relative.house_effects["he"].tolist() == pytest.approx([0.0] * 4, abs=1e-12)


def test_m25_a_plus_3_pp_offset_is_recovered_exactly() -> None:
    # b and c share the same errors e0 = (+2, -2, +1, -1); d = e0 + (+3 on alfa, -3 on beta).
    # Leave-one-house-out: d's market is e0 whatever the weights, so he_d = (+3, -3, 0, 0).
    base = poll(0.42, 0.33, 0.21, 0.04)
    offset = poll(0.45, 0.30, 0.21, 0.04)
    relative = compute_relative(
        metrics_of(
            final_poll("b", base, weight=0.9),
            final_poll("c", base, weight=0.2),
            final_poll("d", offset, weight=0.05),
        )
    )
    assert he_of(relative, "d") == pytest.approx(
        {"alfa": 3.0, "beta": -3.0, "gama": 0.0, OTHERS: 0.0}, abs=1e-12
    )


def test_m25_offset_from_a_weighted_market_is_recovered_exactly() -> None:
    # alfa errors: b +2 (w .5), c -1 (w .25) → market for d = (.5·2 + .25·(-1)) / .75 = +1.
    # d: +4 → he = +3. The other entities balance the shares (values not checked here).
    relative = compute_relative(
        metrics_of(
            final_poll("b", poll(0.42, 0.33, 0.20, 0.05), weight=0.5),
            final_poll("c", poll(0.39, 0.36, 0.20, 0.05), weight=0.25),
            final_poll("d", poll(0.44, 0.31, 0.20, 0.05), weight=0.125),
        )
    )
    he = relative.house_effects.set_index(["pollster_id", "entity_id"])
    assert he.loc[("d", "alfa"), "market_e"] == pytest.approx(1.0)
    assert he.loc[("d", "alfa"), "he"] == pytest.approx(3.0)
    assert he.loc[("d", "alfa"), "n_ref_houses"] == 2
    # b's market: (.25·(-1) + .125·4) / .375 = 2/3; he_b = 2 - 2/3 = 4/3.
    assert he.loc[("b", "alfa"), "he"] == pytest.approx(4 / 3)


def test_m25_equal_weighting_option() -> None:
    # Same polls as above, equal weights: market for d on alfa = (2 - 1) / 2 = .5; he = 3.5.
    metrics = metrics_of(
        final_poll("b", poll(0.42, 0.33, 0.20, 0.05), weight=0.5),
        final_poll("c", poll(0.39, 0.36, 0.20, 0.05), weight=0.25),
        final_poll("d", poll(0.44, 0.31, 0.20, 0.05), weight=0.125),
    )
    relative = compute_relative(metrics, weighting="equal")
    assert relative.weighting == "equal"
    assert he_of(relative, "d")["alfa"] == pytest.approx(3.5)
    # With equal weights, the house effects of an entity sum to 0 over the houses.
    sums = relative.house_effects.groupby("entity_id")["he"].sum()
    assert sums.tolist() == pytest.approx([0.0] * 4, abs=1e-12)
    with pytest.raises(ValueError, match="weighting"):
        compute_relative(metrics, weighting="median")
    with pytest.raises(ValueError, match="weighting"):
        house_effects(common_entity_errors(metrics), weighting="median")


def test_m25_two_houses_give_mirror_image_house_effects() -> None:
    # e_a = (+2, -2, +1, -1), e_b = (-1, +1, 0, 0): he_a = e_a - e_b = (+3, -3, +1, -1).
    relative = compute_relative(
        metrics_of(
            final_poll("a", poll(0.42, 0.33, 0.21, 0.04), weight=0.9),
            final_poll("b", poll(0.39, 0.36, 0.20, 0.05), weight=0.1),
        )
    )
    he_a, he_b = he_of(relative, "a"), he_of(relative, "b")
    assert he_a == pytest.approx({"alfa": 3.0, "beta": -3.0, "gama": 1.0, OTHERS: -1.0})
    assert he_b == pytest.approx({key: -value for key, value in he_a.items()})
    assert relative.house_effects["n_ref_houses"].eq(1).all()
    # RA: MAE_a = 1.5, MAE_b = .5; each is compared with the other house.
    assert ra_row(relative, "a")[["ref_mae", "ra"]].tolist() == pytest.approx([0.5, 1.0])
    assert ra_row(relative, "b")[["ref_mae", "ra"]].tolist() == pytest.approx([1.5, -1.0])
    assert "mirror images" in summarize(relative)


def test_m25_single_house_has_no_reference() -> None:
    relative = compute_relative(metrics_of(final_poll("a", poll(0.42, 0.33, 0.21, 0.04))))
    assert relative.house_effects["n_ref_houses"].eq(0).all()
    assert relative.house_effects["market_e"].isna().all()
    assert relative.house_effects["he"].isna().all()
    row = ra_row(relative, "a")
    assert row["mae_common"] == pytest.approx(1.5)
    assert math.isnan(row["ref_mae"])
    assert math.isnan(row["ra"])
    assert "only one house" in summarize(relative)


def test_m25_missing_recency_weight_is_an_input_error() -> None:
    metrics = metrics_of(final_poll("a", poll(*R.values())), final_poll("b", poll(*R.values())))
    entities = metrics.entities.copy()
    entities.loc[entities["pollster_id"] == "b", "weight"] = math.nan
    broken = ErrorMetrics(entities, metrics.polls)
    with pytest.raises(MetricsInputError, match="weight"):
        compute_relative(broken)
    assert compute_relative(broken, weighting="equal").house_effects["he"].notna().all()


# --- M-2.8 common comparison set ------------------------------------------------------------


def two_formats() -> ErrorMetrics:
    # Result: alfa .40, beta .35, gama .20, others .05 (gama above the threshold).
    # House a names alfa, beta, gama: e = +2, -2, +1, -1.
    # House b names only alfa and beta; gama sits in its others (s .25 = gama + others):
    #   rows alfa (.41, .40) +1, beta (.34, .35) -1, others (.25, .25) 0.
    return metrics_of(
        final_poll("a", poll(0.42, 0.33, 0.21, 0.04)),
        final_poll("b", [("alfa", 0.41, 0.40), ("beta", 0.34, 0.35), (OTHERS, 0.25, 0.25)]),
    )


def test_m28_comparison_set_is_the_entities_every_house_names() -> None:
    sets = comparison_sets(two_formats())
    assert sets.iloc[0].to_dict() == {
        "election_id": ELECTION,
        "n_houses": 2,
        "houses": "a;b",
        "k_common": 3,
        "common_entities": "alfa;beta",
        "merged_entities": "gama",
    }


def test_m28_merged_entities_enter_a_common_others() -> None:
    common = common_entity_errors(two_formats()).set_index(["pollster_id", "entity_id"])
    # a: others = gama + own others: s .21 + .04 = .25, r .20 + .05 = .25, e = +1 - 1 = 0.
    assert common.loc[("a", OTHERS), ["s", "r", "e"]].tolist() == pytest.approx([0.25, 0.25, 0])
    assert common.loc[("a", "alfa"), "e"] == pytest.approx(2.0)  # unchanged T-021 error
    assert common.loc[("b", OTHERS), ["s", "r", "e"]].tolist() == pytest.approx([0.25, 0.25, 0])
    assert len(common) == 6
    for house in ("a", "b"):
        assert common.loc[house, "s"].sum() == pytest.approx(1.0)
        assert common.loc[house, "r"].sum() == pytest.approx(1.0)
        assert common.loc[house, "e"].sum() == pytest.approx(0.0, abs=1e-12)


def test_m28_relative_accuracy_uses_the_common_set() -> None:
    # Native (T-021) MAE: a (2+2+1+1)/4 = 1.5 over k = 4; b (1+1+0)/3 = 2/3 over k = 3.
    # Common set (alfa, beta, others): a (2+2+0)/3 = 4/3, TE 2; b (1+1+0)/3 = 2/3, TE 1.
    metrics = two_formats()
    native = metrics.final_polls.set_index("pollster_id")["mae"]
    assert native.tolist() == pytest.approx([1.5, 2 / 3])
    relative = compute_relative(metrics)
    a, b = ra_row(relative, "a"), ra_row(relative, "b")
    assert a[["k_common", "mae_common", "te_common"]].tolist() == pytest.approx([3, 4 / 3, 2.0])
    assert b[["k_common", "mae_common", "te_common"]].tolist() == pytest.approx([3, 2 / 3, 1.0])
    assert a["ra"] == pytest.approx(2 / 3)
    assert b["ra"] == pytest.approx(-2 / 3)
    he = relative.house_effects
    assert set(he["entity_id"]) == {"alfa", "beta", OTHERS}  # gama has no house effect


def test_m28_no_others_row_when_nothing_is_outside_the_common_set() -> None:
    # A two-candidate round: e_a = (+3, -3), e_b = (+1, -1); k_common = 2.
    relative = compute_relative(
        metrics_of(
            final_poll("a", [("ion", 0.55, 0.52), ("maria", 0.45, 0.48)]),
            final_poll("b", [("ion", 0.53, 0.52), ("maria", 0.47, 0.48)]),
        )
    )
    assert relative.comparison_sets.loc[0, "k_common"] == 2
    assert set(relative.house_effects["entity_id"]) == {"ion", "maria"}
    assert he_of(relative, "a") == pytest.approx({"ion": 2.0, "maria": -2.0})


def test_m28_others_row_is_kept_when_only_one_house_has_others() -> None:
    # a has no others (s 0) but the result has .05 → the common others row exists for both.
    relative = compute_relative(
        metrics_of(
            final_poll("a", [("x", 0.50, 0.50), ("y", 0.50, 0.45), (OTHERS, 0.0, 0.05)]),
            final_poll("b", [("x", 0.50, 0.50), ("y", 0.45, 0.45), (OTHERS, 0.05, 0.05)]),
        )
    )
    assert relative.comparison_sets.loc[0, "k_common"] == 3
    assert he_of(relative, "a") == pytest.approx({"x": 0.0, "y": 5.0, OTHERS: -5.0})


# --- M-2.6 relative accuracy ----------------------------------------------------------------


def test_m26_median_of_the_other_houses_odd_and_even() -> None:
    # Two-candidate round, |e| = MAE: a 1, b 2, c 4, d 7 (pp).
    def house(name: str, error: float) -> FinalPoll:
        s = 0.5 + error / 100
        return final_poll(name, [("ion", s, 0.5), ("maria", 1 - s, 0.5)])

    four = compute_relative(metrics_of(house("a", 1), house("b", 2), house("c", 4), house("d", 7)))
    # Three other houses: the middle value. a: median(2, 4, 7) = 4 → RA = -3.
    # b: median(1, 4, 7) = 4 → -2; c: median(1, 2, 7) = 2 → +2; d: median(1, 2, 4) = 2 → +5.
    ra = four.relative_accuracy.set_index("pollster_id")
    assert ra["ref_mae"].tolist() == pytest.approx([4.0, 4.0, 2.0, 2.0])
    assert ra["ra"].tolist() == pytest.approx([-3.0, -2.0, 2.0, 5.0])
    assert ra["n_ref_houses"].eq(3).all()
    three = compute_relative(metrics_of(house("a", 1), house("b", 2), house("c", 4)))
    # Two other houses: the mean of the two. a: (2+4)/2 = 3 → -2; b: 2.5 → -.5; c: 1.5 → 2.5.
    ra = three.relative_accuracy.set_index("pollster_id")
    assert ra["ref_mae"].tolist() == pytest.approx([3.0, 2.5, 1.5])
    assert ra["ra"].tolist() == pytest.approx([-2.0, -0.5, 2.5])


def test_m26_house_with_a_final_poll_in_one_election_only() -> None:
    # Like Verifield (ADR-0012): house v has a final poll in r2 only. It is absent from r1,
    # and r1 is compared among the other houses only.
    r1, r2 = "pres-2099-r1", "pres-2099-r2"
    two = [("ion", 0.55, 0.52), ("maria", 0.45, 0.48)]
    relative = compute_relative(
        metrics_of(
            final_poll("a", poll(0.42, 0.33, 0.21, 0.04), election=r1),
            final_poll("b", poll(*R.values()), election=r1),
            final_poll("a", two, election=r2),
            final_poll("b", two, election=r2),
            final_poll("v", [("ion", 0.58, 0.52), ("maria", 0.42, 0.48)], election=r2),
        )
    )
    sets = relative.comparison_sets.set_index("election_id")
    assert sets["houses"].to_dict() == {r1: "a;b", r2: "a;b;v"}
    ra = relative.relative_accuracy
    assert set(ra.loc[ra["election_id"] == r1, "pollster_id"]) == {"a", "b"}
    # r2: v e = +6 vs market +3 → he +3; a and b: (3 + 6)/2 = 4.5 market → he -1.5.
    assert he_of(relative, "v", r2)["ion"] == pytest.approx(3.0)
    assert he_of(relative, "a", r2)["ion"] == pytest.approx(-1.5)
    assert ra_row(relative, "v", r2)["ra"] == pytest.approx(3.0)


def test_duplicate_final_poll_is_an_input_error() -> None:
    metrics = metrics_of(final_poll("a", poll(*R.values())), final_poll("b", poll(*R.values())))
    entities = metrics.entities.copy()
    entities.loc[entities["pollster_id"] == "b", "pollster_id"] = "a"
    with pytest.raises(MetricsInputError, match="more than one final poll"):
        compute_relative(ErrorMetrics(entities, metrics.polls))


# --- Synthetic pipeline, summary, CLI, and real data ----------------------------------------


@pytest.fixture(scope="module")
def pipeline(tmp_path_factory: pytest.TempPathFactory) -> RelativeMetrics:
    data_dir = synthetic().write(tmp_path_factory.mktemp("relative") / "data")
    return compute_relative(compute_errors(prepare(data_dir)))


def test_synthetic_pipeline_invariants(pipeline: RelativeMetrics) -> None:
    sets = pipeline.comparison_sets.set_index("election_id")
    assert sets.loc["parl-2099-cd", "n_houses"] == 3
    assert sets.loc["pres-2099-r1", "n_houses"] == 1
    he = pipeline.house_effects
    # Each house's common-set errors still sum to 0 (both sides sum to 1, M-1.2).
    assert he.groupby("poll_id")["e"].sum().tolist() == pytest.approx(
        [0.0] * he["poll_id"].nunique(), abs=1e-9
    )
    k = pipeline.relative_accuracy.set_index("election_id")["k_common"]
    assert (k.groupby(level=0).nunique() == 1).all()  # one k per election
    assert he.loc[he["election_id"] == "pres-2099-r1", "he"].isna().all()


def test_summary_states_that_there_is_no_significance_yet(pipeline: RelativeMetrics) -> None:
    text = summarize(pipeline)
    assert NOT_SIGNIFICANCE in text
    assert "== parl-2099-cd" in text
    empty = RelativeMetrics(
        pd.DataFrame(columns=list(COMPARISON_SET_COLUMNS)),
        pd.DataFrame(columns=list(HOUSE_EFFECT_COLUMNS)),
        pd.DataFrame(columns=list(RELATIVE_ACCURACY_COLUMNS)),
    )
    assert "No final polls." in summarize(empty)


def test_cli_prints_and_writes_csv(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    data_dir = synthetic().write(tmp_path / "data")
    out_dir = tmp_path / "out"
    argv = ["relative", "--data-dir", str(data_dir), "--output", str(out_dir)]
    assert main([*argv, "--weighting", "equal"]) == 0
    text = capsys.readouterr().out
    assert NOT_SIGNIFICANCE in text
    assert "market weights: equal" in text
    for name, columns in (
        ("comparison_sets.csv", COMPARISON_SET_COLUMNS),
        ("house_effects.csv", HOUSE_EFFECT_COLUMNS),
        ("relative_accuracy.csv", RELATIVE_ACCURACY_COLUMNS),
    ):
        assert tuple(pd.read_csv(out_dir / name).columns) == columns


def test_cli_reports_errors(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    assert main(["relative", "--data-dir", str(tmp_path / "missing")]) == 1
    assert "error" in capsys.readouterr().err


def test_real_data_invariants() -> None:
    data = REPO_ROOT / "data"
    if not any(data.glob("polls/*/polls.csv")):
        pytest.skip("no poll data")
    relative = compute_relative(compute_errors(prepare(data)))
    he = relative.house_effects
    assert he.groupby("poll_id")["e"].sum().tolist() == pytest.approx(
        [0.0] * he["poll_id"].nunique(), abs=1e-9
    )
    ra = relative.relative_accuracy
    assert ra["unit_id"].is_unique
    assert ra["mae_common"].ge(0).all()
    compared = relative.comparison_sets["n_houses"] >= 2
    assert ra["ra"].notna().sum() == relative.comparison_sets.loc[compared, "n_houses"].sum()
