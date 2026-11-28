"""Tests for the significance tests (sondaje.stats.significance, METHODOLOGY M-4.1 … M-4.3).

Unit tests use small hand-built prepared tables (fictitious houses, elections, and shares) and
compare every statistic with SciPy reference values (``scipy.stats.binomtest``,
``scipy.stats.ttest_1samp``) or with values computed by hand in the comments.
"""

import math
from pathlib import Path
from typing import NamedTuple

import pandas as pd
import pytest
from scipy import stats

from sondaje.cli import main
from sondaje.config import MethodologyConfig
from sondaje.metrics.errors import ErrorMetrics, MetricsInputError, compute_errors
from sondaje.metrics.relative import compute_relative
from sondaje.prep import OTHERS, Prepared
from sondaje.stats.significance import (
    LEAN_UNIT_COLUMNS,
    NOTE,
    STATUS_INSUFFICIENT,
    STATUS_TESTED,
    TEST_COLUMNS,
    Z_DEGENERATE_RESULT,
    Z_NO_SAMPLE_SIZE,
    Z_OK,
    Z_SCORE_COLUMNS,
    Significance,
    compute_significance,
    cross_election_tests,
    lean_units,
    poll_z_scores,
    sampling_se,
    sign_test,
    summarize,
    t_test,
)
from test_prep import synthetic

type Entities = list[tuple[str, float, float]]


class Poll(NamedTuple):
    """A poll of ``house`` at ``election``: [(entity, s, r)]."""

    house: str
    election: str
    entities: Entities
    final: bool = True
    tag: str = ""
    weight: float = 0.5
    n: float | None = 1000.0
    n_method: str = "sample_size"
    parties: tuple[tuple[str, str], ...] = ()
    """(entity, supporting party) pairs."""


def metrics_of(*polls: Poll) -> ErrorMetrics:
    """T-021 error metrics of hand-built eligible, in-window polls."""
    poll_rows, entity_rows = [], []
    for poll in polls:
        info = {
            "poll_id": f"{poll.house}-{poll.election}{poll.tag}",
            "pollster_id": poll.house,
            "election_id": poll.election,
            "unit_id": f"{poll.house}:{poll.election}",
            "fieldwork_end": pd.Timestamp("2099-01-01"),
            "days_before": round(-7 * math.log(poll.weight)),
            "weight": poll.weight,
            "in_window": True,
            "final_poll": poll.final,
            "target_scope": "domestic",
            "has_lt": False,
            "n": math.nan if poll.n is None else poll.n,
            "n_method": "missing" if poll.n is None else poll.n_method,
            "eligible": True,
        }
        poll_rows.append({**info, "k": len(poll.entities)})
        parties = dict(poll.parties)
        for entity, s, r in poll.entities:
            entity_rows.append(
                {
                    **info,
                    "entity_id": entity,
                    "supporting_party_id": parties.get(entity),
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


def two(alfa: float, r_alfa: float = 0.40) -> Entities:
    """A two-entity comparison: alfa and beta, both sides summing to 1."""
    return [("alfa", alfa, r_alfa), ("beta", 1.0 - alfa, 1.0 - r_alfa)]


ELECTIONS = ("e1", "e2", "e3")
# House a overestimates alfa by +3, +1, +2 pp; b and c are exact. With equal weights the
# market of a is the mean of b and c (0), so he_a(alfa) = +3, +1, +2.
A_ALFA = {"e1": 0.43, "e2": 0.41, "e3": 0.42}


def three_elections(*extra: Poll) -> ErrorMetrics:
    polls = [Poll("a", election, two(A_ALFA[election])) for election in ELECTIONS]
    polls += [Poll(house, election, two(0.40)) for house in "bc" for election in ELECTIONS]
    return metrics_of(*polls, *extra)


def row_of(result: Significance, house: str, lean_id: str) -> pd.Series:
    tests = result.tests
    return tests[(tests["pollster_id"] == house) & (tests["lean_id"] == lean_id)].iloc[0]


# --- Output tables --------------------------------------------------------------------------


def test_output_tables_have_the_documented_columns() -> None:
    result = compute_significance(three_elections())
    assert tuple(result.z_scores.columns) == Z_SCORE_COLUMNS
    assert tuple(result.lean_units.columns) == LEAN_UNIT_COLUMNS
    assert tuple(result.tests.columns) == TEST_COLUMNS
    for column in (*Z_SCORE_COLUMNS, *LEAN_UNIT_COLUMNS, *TEST_COLUMNS):
        assert f"``{column}``" in (Significance.__doc__ or ""), column


# --- M-4.1 single-poll sampling error -------------------------------------------------------


def test_m41_z_score_by_hand() -> None:
    # alfa: s .45, r .40, n 1000, deff 1.5:
    # SE = 100 * sqrt(.4 * .6 / 1000) * sqrt(1.5) = 1.8973666 pp; e = +5 pp; z = 2.6352314.
    z = poll_z_scores(metrics_of(Poll("a", "e1", two(0.45))))
    alfa = z[z["entity_id"] == "alfa"].iloc[0]
    assert alfa["se"] == pytest.approx(100 * math.sqrt(0.4 * 0.6 / 1000) * math.sqrt(1.5))
    assert alfa["se"] == pytest.approx(1.8973666)
    assert alfa["z"] == pytest.approx(2.6352314)
    assert alfa["z"] == pytest.approx((0.45 - 0.40) / math.sqrt(0.4 * 0.6 / 1000 * 1.5))
    # beta: same SE (r .6), e = -5 pp.
    beta = z[z["entity_id"] == "beta"].iloc[0]
    assert beta["z"] == pytest.approx(-2.6352314)
    assert set(z["z_status"]) == {Z_OK}


def test_m41_deff_is_the_methodology_parameter() -> None:
    metrics = metrics_of(Poll("a", "e1", two(0.45)))
    default = poll_z_scores(metrics)
    assert (default["deff"] == MethodologyConfig().deff).all()
    doubled = poll_z_scores(metrics, MethodologyConfig(deff=3.0))
    # SE grows with sqrt(deff): sqrt(3 / 1.5) = sqrt(2).
    ratio = doubled["se"] / default["se"]
    assert ratio.to_list() == pytest.approx([math.sqrt(2)] * 2)
    assert compute_significance(metrics).deff == MethodologyConfig().deff


def test_m41_effective_n_and_n_method_are_carried_through() -> None:
    metrics = metrics_of(
        Poll("a", "e1", two(0.45), n=800.0, n_method="sample_size_expressed"),
        Poll("b", "e1", two(0.40), n=1234.5, n_method="sample_size_x_expressed_share"),
    )
    z = poll_z_scores(metrics)
    by_house = z.groupby("pollster_id")[["n", "n_method"]].first()
    assert by_house.loc["a"].to_list() == [800.0, "sample_size_expressed"]
    assert by_house.loc["b"].to_list() == [1234.5, "sample_size_x_expressed_share"]
    a = z[(z["pollster_id"] == "a") & (z["entity_id"] == "alfa")].iloc[0]
    assert a["se"] == pytest.approx(100 * math.sqrt(0.24 / 800 * 1.5))


def test_m41_poll_without_n_is_kept_and_marked() -> None:
    metrics = metrics_of(Poll("a", "e1", two(0.45), n=None), Poll("b", "e1", two(0.41)))
    z = poll_z_scores(metrics)
    assert len(z) == 4
    missing = z[z["pollster_id"] == "a"]
    assert (missing["z_status"] == Z_NO_SAMPLE_SIZE).all()
    assert missing["se"].isna().all()
    assert missing["z"].isna().all()
    assert (missing["n_method"] == "missing").all()
    assert missing["e"].notna().all()
    assert (z.loc[z["pollster_id"] == "b", "z_status"] == Z_OK).all()


def test_m41_result_share_zero_has_no_z() -> None:
    entities = [("alfa", 0.60, 0.60), ("beta", 0.38, 0.40), (OTHERS, 0.02, 0.0)]
    z = poll_z_scores(metrics_of(Poll("a", "e1", entities)))
    others = z[z["entity_id"] == OTHERS].iloc[0]
    assert others["z_status"] == Z_DEGENERATE_RESULT
    assert pd.isna(others["se"])
    assert pd.isna(others["z"])
    assert z.loc[z["entity_id"] == "alfa", "z"].iloc[0] == pytest.approx(0.0)


def test_m41_sampling_se_rejects_bad_deff() -> None:
    with pytest.raises(ValueError, match="deff"):
        sampling_se(pd.Series([0.5]), pd.Series([1000.0]), 0.0)


# --- M-4.2 sign test ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("he", "alternative"),
    [
        ([3.0, 1.0, 2.0], "two-sided"),
        ([3.0, -1.0, 2.0], "two-sided"),
        ([3.0, -1.0, 2.0, 0.5, 4.0], "two-sided"),
        ([3.0, -1.0, 2.0, 0.5, 4.0], "greater"),
        ([3.0, -1.0, 2.0, 0.5, 4.0], "less"),
        ([-3.0, -1.0, -2.0, -0.5, -4.0, -0.1, 1.0], "two-sided"),
    ],
)
def test_m42_sign_test_matches_scipy(he: list[float], alternative: str) -> None:
    result = sign_test(he, alternative)
    positive = sum(value > 0 for value in he)
    expected = stats.binomtest(positive, len(he), 0.5, alternative=alternative).pvalue
    assert result.n_positive == positive
    assert result.n_negative == len(he) - positive
    assert result.n_ties == 0
    assert result.p == pytest.approx(expected)
    best = stats.binomtest(len(he), len(he), 0.5, alternative="greater").pvalue
    best = min(1.0, 2 * best) if alternative == "two-sided" else best
    assert result.p_min == pytest.approx(best)


def test_m42_three_elections_cannot_go_below_a_quarter() -> None:
    # All 3 positive: two-sided p = 2 * 0.5^3 = 0.25, the smallest possible value.
    result = sign_test([3.0, 1.0, 2.0])
    assert result.p == pytest.approx(0.25)
    assert result.p_min == pytest.approx(0.25)
    assert stats.binomtest(3, 3, 0.5).pvalue == pytest.approx(0.25)
    # One-sided: 0.5^3 = 0.125.
    assert sign_test([3.0, 1.0, 2.0], "greater").p == pytest.approx(0.125)


def test_m42_ties_are_left_out() -> None:
    # 0 and 1e-12 are ties: the test runs on the 3 other values, 2 positive and 1 negative.
    result = sign_test([0.0, 2.0, 1e-12, 1.0, -1.0])
    assert (result.n_positive, result.n_negative, result.n_ties) == (2, 1, 2)
    assert result.p == pytest.approx(stats.binomtest(2, 3, 0.5).pvalue)
    assert result.p == pytest.approx(1.0)
    all_ties = sign_test([0.0, 0.0, 0.0])
    assert all_ties.n_ties == 3
    assert math.isnan(all_ties.p)
    assert math.isnan(all_ties.p_min)


def test_m42_rejects_unknown_alternative() -> None:
    with pytest.raises(ValueError, match="alternative"):
        sign_test([1.0, 2.0, 3.0], "bigger")


# --- M-4.3 t-test ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("he", "alternative"),
    [
        ([3.0, 1.0, 2.0], "two-sided"),
        ([3.0, -1.0, 2.0], "two-sided"),
        ([3.0, -1.0, 2.0, 0.5, 4.0], "greater"),
        ([3.0, -1.0, 2.0, 0.5, 4.0], "less"),
        ([0.0, 2.5, -1.25, 3.0], "two-sided"),
    ],
)
def test_m43_t_test_matches_scipy(he: list[float], alternative: str) -> None:
    result = t_test(he, alternative)
    expected = stats.ttest_1samp(he, 0.0, alternative=alternative)
    assert result.statistic == pytest.approx(expected.statistic)
    assert result.p == pytest.approx(expected.pvalue)
    assert result.df == len(he) - 1


def test_m43_t_statistic_by_hand() -> None:
    # he = 3, 1, 2: mean 2, sd 1, t = 2 / (1 / sqrt(3)) = 3.4641016, df 2.
    result = t_test([3.0, 1.0, 2.0])
    assert result.statistic == pytest.approx(2 * math.sqrt(3))
    assert result.p == pytest.approx(2 * stats.t.sf(2 * math.sqrt(3), 2))


def test_m43_constant_values_have_no_statistic() -> None:
    result = t_test([2.0, 2.0, 2.0])
    assert math.isnan(result.statistic)
    assert math.isnan(result.p)
    assert result.df == 2


# --- Across elections: unit, threshold, attribution -----------------------------------------


def test_cross_election_tests_match_scipy() -> None:
    result = compute_significance(three_elections())
    a = row_of(result, "a", "alfa")
    he = result.lean_units.query("pollster_id == 'a' and lean_id == 'alfa'")["he"].to_list()
    assert he == pytest.approx([3.0, 1.0, 2.0])
    assert a["status"] == STATUS_TESTED
    assert a["n_elections"] == 3
    assert a["elections"] == "e1;e2;e3"
    assert a["mean_he"] == pytest.approx(2.0)
    assert a["sd_he"] == pytest.approx(1.0)
    assert (a["n_positive"], a["n_negative"], a["n_ties"]) == (3, 0, 0)
    assert a["sign_p"] == pytest.approx(stats.binomtest(3, 3, 0.5).pvalue)
    assert a["sign_p_min"] == pytest.approx(0.25)
    reference = stats.ttest_1samp(he, 0.0)
    assert a["t_stat"] == pytest.approx(reference.statistic)
    assert a["t_p"] == pytest.approx(reference.pvalue)
    assert a["t_df"] == 2
    assert a["alternative"] == "two-sided"
    assert bool(a["preliminary"])
    # beta mirrors alfa (two entities summing to 1): he = -3, -1, -2.
    beta = row_of(result, "a", "beta")
    assert beta["t_stat"] == pytest.approx(-reference.statistic)
    assert (beta["n_positive"], beta["n_negative"]) == (0, 3)


def test_one_sided_alternative_reaches_both_tests() -> None:
    result = compute_significance(three_elections(), alternative="greater")
    a = row_of(result, "a", "alfa")
    he = [3.0, 1.0, 2.0]
    assert a["sign_p"] == pytest.approx(stats.binomtest(3, 3, 0.5, alternative="greater").pvalue)
    assert a["t_p"] == pytest.approx(stats.ttest_1samp(he, 0.0, alternative="greater").pvalue)
    assert a["sign_p_min"] == pytest.approx(0.125)
    assert a["alternative"] == "greater"


def test_m16_extra_polls_of_a_unit_do_not_change_the_test() -> None:
    base = compute_significance(three_elections())
    # Two more (non-final) polls of house a in e1 and one of b in e2, far from the result.
    extra = compute_significance(
        three_elections(
            Poll("a", "e1", two(0.55), final=False, tag="-early"),
            Poll("a", "e1", two(0.30), final=False, tag="-mid"),
            Poll("b", "e2", two(0.50), final=False, tag="-early"),
        )
    )
    # The extra polls are there (M-4.1 has a z for each of them) ...
    assert extra.z_scores["poll_id"].nunique() == base.z_scores["poll_id"].nunique() + 3
    # ... but each (house, election) still gives one value, so n and every statistic hold.
    assert extra.lean_units.groupby(["pollster_id", "lean_id", "election_id"]).size().max() == 1
    pd.testing.assert_frame_equal(extra.lean_units, base.lean_units)
    pd.testing.assert_frame_equal(extra.tests, base.tests)
    assert row_of(extra, "a", "alfa")["n_elections"] == 3


def test_m16_two_values_for_one_unit_are_rejected() -> None:
    he = compute_relative(three_elections()).house_effects
    duplicated = pd.concat([he, he.iloc[[0]]], ignore_index=True)
    with pytest.raises(MetricsInputError, match=r"M-1\.6"):
        lean_units(duplicated)
    units = lean_units(he)
    with pytest.raises(MetricsInputError, match="unit"):
        cross_election_tests(pd.concat([units, units.iloc[[0]]], ignore_index=True))


def test_fewer_than_three_elections_are_flagged_not_tested() -> None:
    # House d polls e1 and e2 only.
    result = compute_significance(
        three_elections(Poll("d", "e1", two(0.44)), Poll("d", "e2", two(0.45)))
    )
    d = row_of(result, "d", "alfa")
    assert d["n_elections"] == 2
    assert d["status"] == STATUS_INSUFFICIENT == "insufficient (< 3 elections)"
    for column in ("sign_p", "sign_p_min", "t_stat", "t_df", "t_p"):
        assert pd.isna(d[column]), column
    # The descriptive columns are kept.
    assert d["elections"] == "e1;e2"
    assert (d["n_positive"], d["n_negative"]) == (2, 0)
    assert row_of(result, "a", "alfa")["status"] == STATUS_TESTED
    assert set(result.tests["status"]) == {STATUS_TESTED, STATUS_INSUFFICIENT}


def test_elections_without_a_reference_house_do_not_count() -> None:
    # e4 has house a only: no other house, so he is empty and e4 is not a unit of the test.
    result = compute_significance(three_elections(Poll("a", "e4", two(0.50))))
    assert "e4" not in set(result.lean_units["election_id"])
    assert row_of(result, "a", "alfa")["n_elections"] == 3


def test_others_are_left_out_of_the_cross_election_tests() -> None:
    entities = [("alfa", 0.43, 0.40), ("beta", 0.50, 0.50), (OTHERS, 0.07, 0.10)]
    exact = [("alfa", 0.40, 0.40), ("beta", 0.50, 0.50), (OTHERS, 0.10, 0.10)]
    polls = [Poll("a", e, entities) for e in ELECTIONS]
    polls += [Poll(h, e, exact) for h in "bc" for e in ELECTIONS]
    result = compute_significance(metrics_of(*polls))
    assert OTHERS not in set(result.lean_units["lean_id"])
    assert OTHERS in set(result.z_scores["entity_id"])


def test_party_attribution_follows_the_supporting_party() -> None:
    # e1 parliamentary (party alfa); e2 and e3 presidential, with candidate ion supported by
    # alfa. As a party, alfa has 3 elections; as entities, alfa has 1 and ion 2.
    def cand(s: float) -> Entities:
        return [("ion", s, 0.40), ("vasile", 1.0 - s, 0.60)]

    support = (("ion", "alfa"),)
    polls = [Poll("a", "e1", two(0.43))]
    polls += [Poll("a", e, cand(s), parties=support) for e, s in (("e2", 0.41), ("e3", 0.42))]
    polls += [Poll(h, "e1", two(0.40)) for h in "bc"]
    polls += [Poll(h, e, cand(0.40), parties=support) for h in "bc" for e in ("e2", "e3")]
    metrics = metrics_of(*polls)
    by_party = compute_significance(metrics)
    alfa = row_of(by_party, "a", "alfa")
    assert alfa["n_elections"] == 3
    assert alfa["entities"] == "alfa;ion"
    assert alfa["status"] == STATUS_TESTED
    by_entity = compute_significance(metrics, attribution="entity")
    assert row_of(by_entity, "a", "alfa")["n_elections"] == 1
    assert row_of(by_entity, "a", "ion")["n_elections"] == 2
    assert set(by_entity.tests["status"]) == {STATUS_INSUFFICIENT}


def test_party_attribution_falls_back_when_two_rows_share_a_party() -> None:
    # Candidates ion and ana are both supported by alfa in e1: each keeps its own entity.
    entities = [("ion", 0.33, 0.30), ("ana", 0.30, 0.30), ("vasile", 0.37, 0.40)]
    exact = [("ion", 0.30, 0.30), ("ana", 0.30, 0.30), ("vasile", 0.40, 0.40)]
    support = (("ion", "alfa"), ("ana", "alfa"))
    polls = [Poll("a", "e1", entities, parties=support)]
    polls += [Poll(h, "e1", exact, parties=support) for h in "bc"]
    units = compute_significance(metrics_of(*polls)).lean_units
    assert set(units["lean_id"]) == {"ion", "ana", "vasile"}


def test_rejects_unknown_options() -> None:
    metrics = three_elections()
    with pytest.raises(ValueError, match="attribution"):
        compute_significance(metrics, attribution="house")
    with pytest.raises(ValueError, match="weighting"):
        compute_significance(metrics, weighting="median")
    with pytest.raises(ValueError, match="alternative"):
        compute_significance(metrics, alternative="bigger")


# --- Wording, summary and CLI ---------------------------------------------------------------


def test_summary_states_the_limits_in_neutral_words() -> None:
    text = summarize(compute_significance(three_elections()))
    assert NOTE in text
    assert "cannot give a p-value below 0.25" in text
    assert "consistent with sampling noise" in text
    assert STATUS_TESTED in text
    lowered = text.lower()
    for word in ("manipulat", "rigged", "fake", "intentional", "on purpose"):
        assert word not in lowered


def test_cli_writes_the_tables(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    data_dir = synthetic().write(tmp_path / "data")
    out_dir = tmp_path / "out"
    argv = ["significance", "--data-dir", str(data_dir), "--output", str(out_dir)]
    assert main([*argv, "--attribution", "entity", "--alternative", "greater"]) == 0
    text = capsys.readouterr().out
    assert NOTE in text
    assert "greater" in text
    for name, columns in (
        ("z_scores.csv", Z_SCORE_COLUMNS),
        ("lean_units.csv", LEAN_UNIT_COLUMNS),
        ("tests.csv", TEST_COLUMNS),
    ):
        assert tuple(pd.read_csv(out_dir / name).columns) == columns


def test_cli_reports_errors(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    assert main(["significance", "--data-dir", str(tmp_path / "missing")]) == 1
    assert "error" in capsys.readouterr().err
