"""Tests for the error metrics (sondaje.metrics.errors, METHODOLOGY M-2.1 … M-2.4).

Every expected value is computed by hand in the comments. Unit tests use small hand-built
prepared tables; the integration tests run :func:`sondaje.prep.prepare` on the synthetic 2099
dataset of ``test_prep`` (all names, dates, and figures are fictitious).
"""

import math
from pathlib import Path

import pandas as pd
import pytest

from sondaje.cli import main
from sondaje.config import MethodologyConfig
from sondaje.metrics.errors import (
    ErrorMetrics,
    MetricsInputError,
    compute_errors,
    entity_errors,
    log_odds_error,
    mean_absolute_error,
    poll_errors,
    signed_error,
    summarize,
    total_error,
)
from sondaje.prep import OTHERS, Prepared, prepare
from test_prep import (
    P1,
    P1_SCENARIO,
    P_AFTER,
    P_EDGE,
    P_NODATE,
    P_OUT,
    P_R2,
    P_TOTAL,
    synthetic,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def fake_prepared(polls: dict[str, list[tuple[str, float, float]]], **flags: object) -> Prepared:
    """A hand-built :class:`Prepared`: poll id → [(entity, s, r)], one house and one election."""
    poll_rows, entity_rows = [], []
    for poll_id, entities in polls.items():
        info = {
            "poll_id": poll_id,
            "pollster_id": "casa",
            "election_id": "elec-2099",
            "unit_id": "casa:elec-2099",
            "fieldwork_end": pd.Timestamp("2099-01-01"),
            "days_before": 3,
            "weight": 0.5,
            "in_window": True,
            "final_poll": True,
            "target_scope": "domestic",
            "has_lt": False,
            "n": 1000.0,
            "n_method": "sample_size",
            "eligible": True,
            **flags,
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
    return Prepared(
        pd.DataFrame(entity_rows), pd.DataFrame(poll_rows), pd.DataFrame(), MethodologyConfig()
    )


# Poll A. Shares sum to 1 on both sides; the poll publishes no "others".
#   entity  s     r     e = 100(s-r)
#   alfa    .40   .30   +10
#   beta    .35   .40   -5
#   gama    .25   .25   0
#   others  0     .05   -5
POLL_A = [
    ("alfa", 0.40, 0.30),
    ("beta", 0.35, 0.40),
    ("gama", 0.25, 0.25),
    (OTHERS, 0.0, 0.05),
]
# Poll B, a two-candidate round: s = (.6, .4), r = (.5, .5); e = +10, -10.
POLL_B = [("ion", 0.6, 0.5), ("maria", 0.4, 0.5)]


# --- M-2.1 signed error ---------------------------------------------------------------------


def test_m21_signed_error_is_in_pp_and_positive_for_overestimates() -> None:
    e = signed_error(pd.Series([0.40, 0.35, 0.25, 0.0]), pd.Series([0.30, 0.40, 0.25, 0.05]))
    assert e.tolist() == pytest.approx([10.0, -5.0, 0.0, -5.0])


def test_m21_entity_errors_of_a_poll() -> None:
    entities = entity_errors(fake_prepared({"a": POLL_A}))
    assert entities["entity_id"].tolist() == ["alfa", "beta", "gama", OTHERS]
    assert entities["e"].tolist() == pytest.approx([10.0, -5.0, 0.0, -5.0])
    assert entities["abs_e"].tolist() == pytest.approx([10.0, 5.0, 0.0, 5.0])


# --- M-2.2 MAE and M-2.3 total error --------------------------------------------------------


def test_m22_mae_is_the_mean_of_absolute_errors() -> None:
    # (10 + 5 + 0 + 5) / 4 = 5, with the "others" row counted in k.
    assert mean_absolute_error(pd.Series([10.0, -5.0, 0.0, -5.0])) == pytest.approx(5.0)


def test_m23_total_error_is_half_the_sum_of_absolute_errors() -> None:
    # (10 + 5 + 0 + 5) / 2 = 10: the overestimates sum to 10, the underestimates to -10.
    assert total_error(pd.Series([10.0, -5.0, 0.0, -5.0])) == pytest.approx(10.0)


def test_m22_m23_empty_input_is_nan() -> None:
    assert math.isnan(mean_absolute_error(pd.Series([], dtype=float)))
    assert math.isnan(total_error(pd.Series([], dtype=float)))


def test_m22_m23_per_poll() -> None:
    polls = poll_errors(fake_prepared({"a": POLL_A, "b": POLL_B}))
    by_id = polls.set_index("poll_id")
    assert by_id.loc["a", ["k", "mae", "te"]].tolist() == pytest.approx([4, 5.0, 10.0])
    # Poll B: |+10| and |-10| → MAE 10, TE 10.
    assert by_id.loc["b", ["k", "mae", "te"]].tolist() == pytest.approx([2, 10.0, 10.0])


# --- M-2.4 log-odds accuracy ----------------------------------------------------------------


def test_m24_log_odds_error() -> None:
    # alfa: (.4/.6)/(.3/.7) = (2/3)/(3/7) = 14/9. beta: (.35/.65)/(.4/.6) = (7/13)/(2/3) = 21/26.
    # gama: s = r, so the odds ratio is 1 and A' = 0.
    a = log_odds_error(pd.Series([0.40, 0.35, 0.25]), pd.Series([0.30, 0.40, 0.25]))
    assert a.tolist() == pytest.approx([math.log(14 / 9), math.log(21 / 26), 0.0])
    assert a.iloc[0] > 0 > a.iloc[1]  # overestimate → positive, underestimate → negative


def test_m24_log_odds_error_is_symmetric_in_the_odds() -> None:
    # Poll B: s = .6 vs r = .5 → ln(1.5); s = .4 vs r = .5 → -ln(1.5).
    a = log_odds_error(pd.Series([0.6, 0.4]), pd.Series([0.5, 0.5]))
    assert a.tolist() == pytest.approx([math.log(1.5), -math.log(1.5)])


def test_m24_b_is_the_mean_absolute_log_odds_error() -> None:
    by_id = poll_errors(fake_prepared({"a": POLL_A, "b": POLL_B})).set_index("poll_id")
    # Poll B: (ln 1.5 + ln 1.5) / 2 = ln 1.5.
    assert by_id.loc["b", "b"] == pytest.approx(math.log(1.5))
    assert by_id.loc["b", "b_terms"] == 2
    assert by_id.loc["b", "b_undefined"] == 0


def test_m24_zero_poll_share_is_left_out_of_b_and_counted() -> None:
    # Poll A: the "others" term has s = 0, so A' is undefined (M-2.7). B is the mean over the
    # three defined terms: (ln(14/9) + |ln(21/26)| + 0) / 3 = (0.441833 + 0.213574 + 0) / 3.
    prepared = fake_prepared({"a": POLL_A})
    entities = entity_errors(prepared)
    assert entities["a_prime"].isna().tolist() == [False, False, False, True]
    row = poll_errors(prepared, entities).iloc[0]
    assert row["b"] == pytest.approx((math.log(14 / 9) + math.log(26 / 21) + 0.0) / 3)
    assert (row["b_terms"], row["b_undefined"]) == (3, 1)
    # The undefined term still counts in k, MAE and TE (it is a real, finite error of 5 pp).
    assert row["k"] == 4
    assert row["mae"] == pytest.approx(5.0)


def test_m24_zero_floor_clips_shares_so_no_term_is_undefined() -> None:
    # Floor .01: others s = 0 → .01 against r = .05. A' = ln[(.01/.99)/(.05/.95)] = ln(19/99).
    # Terms inside [.01, .99] are unchanged, so B = (0.441833 + 0.213574 + 0 + 1.650681) / 4.
    prepared = fake_prepared({"a": POLL_A})
    entities = entity_errors(prepared, zero_floor=0.01)
    assert entities["a_prime"].iloc[3] == pytest.approx(math.log(19 / 99))
    row = poll_errors(prepared, entities).iloc[0]
    expected = (math.log(14 / 9) + math.log(26 / 21) + 0.0 + math.log(99 / 19)) / 4
    assert row["b"] == pytest.approx(expected)
    assert (row["b_terms"], row["b_undefined"]) == (4, 0)


def test_m24_zero_floor_must_be_a_small_positive_share() -> None:
    for bad in (0.0, 0.5, -0.1):
        with pytest.raises(ValueError, match="zero_floor"):
            log_odds_error(pd.Series([0.5]), pd.Series([0.5]), bad)


def test_m24_b_is_nan_when_no_term_is_defined() -> None:
    # One entity holding all the votes on both sides: e = 0, but s = r = 1 has no log-odds.
    row = poll_errors(fake_prepared({"x": [("solo", 1.0, 1.0)]})).iloc[0]
    assert math.isnan(row["b"])
    assert (row["k"], row["b_terms"], row["b_undefined"]) == (1, 0, 1)
    assert row["mae"] == 0.0
    assert row["te"] == 0.0


def test_m24_named_party_shown_at_zero_is_also_undefined() -> None:
    # The rule is about the share, not the "others" bucket: alfa at 0 against r = .2.
    prepared = fake_prepared({"z": [("alfa", 0.0, 0.2), ("beta", 1.0, 0.8)]})
    entities = entity_errors(prepared)
    assert entities["a_prime"].isna().tolist() == [True, True]  # beta: s = 1 is undefined too
    assert entities["e"].tolist() == pytest.approx([-20.0, 20.0])


# --- Eligibility and the final poll ---------------------------------------------------------


def test_excluded_polls_have_no_metrics() -> None:
    prepared = fake_prepared({"a": POLL_A})
    extra = fake_prepared({"x": POLL_B}, eligible=False, final_poll=False, in_window=False)
    combined = Prepared(
        pd.concat([prepared.rows, extra.rows], ignore_index=True),
        pd.concat([prepared.polls, extra.polls], ignore_index=True),
        prepared.adjustments,
        prepared.config,
    )
    metrics = compute_errors(combined)
    assert metrics.polls["poll_id"].tolist() == ["a"]
    assert set(metrics.entities["poll_id"]) == {"a"}


def test_no_eligible_polls_gives_empty_tables_with_the_columns() -> None:
    metrics = compute_errors(fake_prepared({"x": POLL_B}, eligible=False))
    assert metrics.polls.empty
    assert metrics.entities.empty
    assert metrics.final_polls.empty
    assert "mae" in metrics.polls.columns
    assert "a_prime" in metrics.entities.columns


def test_a_missing_share_is_an_error_not_a_fill() -> None:
    prepared = fake_prepared({"a": POLL_A})
    prepared.rows.loc[0, "s"] = float("nan")
    with pytest.raises(MetricsInputError, match="no poll share"):
        entity_errors(prepared)


def test_a_missing_column_is_an_error() -> None:
    prepared = fake_prepared({"a": POLL_A})
    broken = Prepared(
        prepared.rows.drop(columns=["r"]), prepared.polls, prepared.adjustments, prepared.config
    )
    with pytest.raises(MetricsInputError, match="lacks column"):
        entity_errors(broken)


# --- Integration with the M-1 pipeline (synthetic 2099 data) --------------------------------


@pytest.fixture(scope="module")
def prepared(tmp_path_factory: pytest.TempPathFactory) -> Prepared:
    return prepare(synthetic().write(tmp_path_factory.mktemp("data")))


@pytest.fixture(scope="module")
def metrics(prepared: Prepared) -> ErrorMetrics:
    return compute_errors(prepared)


def poll_row(metrics: ErrorMetrics, poll_id: str) -> pd.Series:
    return metrics.polls.set_index("poll_id").loc[poll_id]


def errors_of(metrics: ErrorMetrics, poll_id: str) -> dict[str, float]:
    rows = metrics.entities[metrics.entities["poll_id"] == poll_id]
    return dict(zip(rows["entity_id"], rows["e"], strict=True))


def test_missing_entity_enters_through_others(metrics: ErrorMetrics) -> None:
    # P_EDGE names alfa .40, beta .35, gama .25 and no "others"; omega (r = .008, below 1%) is
    # not compared on its own. Domestic r: alfa .4, beta .3, gama .292, others .008.
    # e: alfa 0, beta +5, gama 25 - 29.2 = -4.2, others 0 - 0.8 = -0.8.
    assert errors_of(metrics, P_EDGE) == pytest.approx(
        {"alfa": 0.0, "beta": 5.0, "gama": -4.2, OTHERS: -0.8}
    )
    row = poll_row(metrics, P_EDGE)
    # MAE = (0 + 5 + 4.2 + 0.8) / 4 = 2.5; TE = 10 / 2 = 5.
    assert (row["k"], row["mae"], row["te"]) == pytest.approx((4, 2.5, 5.0))
    # B over alfa (0), beta ln[(7/13)/(3/7)] = ln(49/39), gama ln[(1/3)/(.292/.708)] = ln(59/73);
    # others has s = 0, so it is undefined and left out (M-2.7).
    expected = (0.0 + math.log(49 / 39) + math.log(73 / 59)) / 3
    assert row["b"] == pytest.approx(expected)
    assert (row["b_terms"], row["b_undefined"]) == (3, 1)


def test_final_poll_errors_with_mappings_and_others(metrics: ErrorMetrics) -> None:
    # P1: s = alfa 42/92.5, beta 33/92.5, gama 14/92.5, others 3.5/92.5 (see test_prep).
    # e: alfa 45.4054 - 40 = +5.4054, beta 35.6757 - 30 = +5.6757, gama 15.1351 - 29.2 = -14.0649,
    # others 3.7838 - 0.8 = +2.9838.
    e = errors_of(metrics, P1)
    assert e == pytest.approx(
        {
            "alfa": 4200 / 92.5 - 40,
            "beta": 3300 / 92.5 - 30,
            "gama": 1400 / 92.5 - 29.2,
            OTHERS: 350 / 92.5 - 0.8,
        }
    )
    assert sum(e.values()) == pytest.approx(0.0)
    row = poll_row(metrics, P1)
    # MAE = 28.12973 / 4 = 7.03243; TE = the underestimate of gama, 14.06486.
    assert row["mae"] == pytest.approx(7.032432, abs=1e-6)
    assert row["te"] == pytest.approx(14.064865, abs=1e-6)
    assert (row["b_terms"], row["b_undefined"]) == (4, 0)
    assert bool(row["has_lt"]) is True  # the "<1" value of omega sits in the others bucket


def test_two_candidate_round(metrics: ErrorMetrics) -> None:
    # P_R2: ion 55 vs .52 → +3; maria 45 vs .48 → -3. MAE = TE = 3.
    # A' = ln[(.55/.45)/(.52/.48)] = ln(44/39) for ion, and -ln(44/39) for maria.
    row = poll_row(metrics, P_R2)
    assert (row["mae"], row["te"]) == pytest.approx((3.0, 3.0))
    assert row["b"] == pytest.approx(math.log(44 / 39))


def test_total_scope_poll_uses_the_total_result(metrics: ErrorMetrics) -> None:
    # P_TOTAL (target scope total): r = alfa .375, beta 1/3, gama .276667, omega .015 (kept);
    # s = .40, .30, .25, .02, others .03 (total 1.00). Others: result has none left → r = 0.
    e = errors_of(metrics, P_TOTAL)
    assert e["alfa"] == pytest.approx(2.5)
    assert e["beta"] == pytest.approx(100 * (0.30 - 1 / 3))
    assert e["omega"] == pytest.approx(100 * (0.02 - 0.015))
    assert e[OTHERS] == pytest.approx(3.0)


def test_excluded_polls_are_absent_and_out_of_window_polls_are_flagged(
    metrics: ErrorMetrics,
) -> None:
    ids = set(metrics.polls["poll_id"])
    assert not ids & {P1_SCENARIO, P_AFTER, P_NODATE}  # not headline, after the vote, no date
    assert P_OUT in ids
    assert bool(poll_row(metrics, P_OUT)["in_window"]) is False  # 29 days before election day
    assert bool(poll_row(metrics, P_EDGE)["in_window"]) is True  # exactly 28 days


def test_final_polls_are_one_per_house_and_election(metrics: ErrorMetrics) -> None:
    finals = metrics.final_polls
    assert finals["unit_id"].is_unique
    assert set(finals["unit_id"]) == {
        "exemplar:parl-2099-cd",
        "secundar:parl-2099-cd",
        "tertiar:parl-2099-cd",
        "exemplar:pres-2099-r1",
        "exemplar:pres-2099-r2",
    }
    by_unit = finals.set_index("unit_id")
    assert by_unit.loc["exemplar:parl-2099-cd", "poll_id"] == P1
    assert by_unit.loc["secundar:parl-2099-cd", "poll_id"] == P_TOTAL
    assert finals["in_window"].all()
    assert set(metrics.final_entities["poll_id"]) == set(finals["poll_id"])


def test_te_is_the_sum_of_overestimates_for_every_poll(metrics: ErrorMetrics) -> None:
    # Both sides sum to 1 (M-1.2), so the signed errors sum to 0 and TE = Σ max(e, 0).
    grouped = metrics.entities.groupby("poll_id")
    assert grouped["e"].sum().tolist() == pytest.approx([0.0] * grouped.ngroups, abs=1e-9)
    over = grouped["e"].apply(lambda e: e.clip(lower=0).sum())
    te = metrics.polls.set_index("poll_id")["te"]
    assert te.loc[over.index].tolist() == pytest.approx(over.tolist())


def test_zero_floor_option_changes_only_the_undefined_terms(prepared: Prepared) -> None:
    # P_EDGE with floor .001: others s -> .001 against r = .008:
    # A' = ln[(.001/.999)/(.008/.992)] = ln(124/999), so B has 4 terms.
    row = poll_row(compute_errors(prepared, zero_floor=0.001), P_EDGE)
    assert (row["b_terms"], row["b_undefined"]) == (4, 0)
    expected = (0.0 + math.log(49 / 39) + math.log(73 / 59) + math.log(999 / 124)) / 4
    assert row["b"] == pytest.approx(expected, rel=1e-3)


def test_entity_errors_carry_the_prepared_flags(metrics: ErrorMetrics) -> None:
    entities = metrics.entities[metrics.entities["poll_id"] == P1].set_index("entity_id")
    assert bool(entities.loc[OTHERS, "has_lt"]) is True
    assert bool(entities.loc["alfa", "final_poll"]) is True
    assert entities.loc["alfa", "days_before"] == 3


# --- Summary, CLI, and real data ------------------------------------------------------------


def test_summary_lists_the_final_polls(metrics: ErrorMetrics) -> None:
    text = summarize(metrics)
    assert "5 final polls" in text
    assert P1 in text


def test_cli_prints_the_table_and_writes_csv(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    data_dir = synthetic().write(tmp_path / "data")
    out_dir = tmp_path / "out"
    assert main(["errors", "--data-dir", str(data_dir), "--output", str(out_dir)]) == 0
    assert "Final poll of each (election, house)" in capsys.readouterr().out
    assert len(pd.read_csv(out_dir / "final_polls.csv")) == 5
    assert (out_dir / "entity_errors.csv").exists()
    assert (out_dir / "poll_errors.csv").exists()


def test_cli_reports_errors(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    assert main(["errors", "--data-dir", str(tmp_path / "missing")]) == 1
    assert "error" in capsys.readouterr().err
    data_dir = synthetic().write(tmp_path / "data")
    assert main(["errors", "--data-dir", str(data_dir), "--zero-floor", "0.7"]) == 1
    assert "zero_floor" in capsys.readouterr().err


def test_real_data_invariants() -> None:
    data = REPO_ROOT / "data"
    if not any(data.glob("polls/*/polls.csv")):
        pytest.skip("no poll data")
    metrics = compute_errors(prepare(data))
    assert metrics.final_polls["unit_id"].is_unique
    assert metrics.polls["mae"].ge(0).all()
    assert metrics.polls["te"].ge(0).all()
    assert (metrics.polls["te"] <= 100).all()
    assert metrics.entities.groupby("poll_id")["e"].sum().tolist() == pytest.approx(
        [0.0] * metrics.entities["poll_id"].nunique(), abs=1e-9
    )
