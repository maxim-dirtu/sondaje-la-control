"""Tests for the M-1 data preparation pipeline (sondaje.prep).

Every expected value is computed by hand in the comments, from the synthetic data built in
:func:`synthetic`. All names, dates, and figures are fictitious (dated 2099).
"""

import csv
import math
from pathlib import Path

import pandas as pd
import pytest

from sondaje.cli import main
from sondaje.config import MethodologyConfig
from sondaje.prep import (
    NO_FIELDWORK_END,
    NOT_HEADLINE,
    OTHERS,
    PUBLISHED_AFTER_VOTE,
    Prepared,
    PrepError,
    prepare,
    summarize,
)
from sondaje.schema import TABLES_BY_NAME

REPO_ROOT = Path(__file__).resolve().parents[1]
URL = "https://example.org/source"


class Synth:
    """Writes a minimal, loadable data directory (only the files M-1 reads)."""

    def __init__(self) -> None:
        self.files: dict[str, tuple[str, list[dict[str, str]]]] = {}

    def add(self, rel: str, table: str, **values: object) -> None:
        defaults = {
            "source_url": URL,
            "source_type": "official",
            "retrieved_at": "2099-12-01",
            "verified": "true",
        }
        row = {**defaults, **{k: "" if v is None else str(v) for k, v in values.items()}}
        self.files.setdefault(rel, (table, []))[1].append(row)

    def election(self, election_id: str, election_type: str, round_: int, date: str) -> None:
        body = "chamber_of_deputies" if election_type == "parliamentary" else "president"
        self.add(
            "registry/elections.csv",
            "elections",
            election_id=election_id,
            election_type=election_type,
            body=body,
            round=round_,
            election_date=date,
            name=election_id,
            status="held",
        )

    def entity(self, entity_id: str, entity_type: str) -> None:
        self.add(
            "registry/entities.csv",
            "entities",
            entity_id=entity_id,
            entity_type=entity_type,
            name=entity_id,
            short_name=entity_id,
        )

    def results(self, election_id: str, votes: dict[str, tuple[int, int]]) -> None:
        """``votes``: contestant → (domestic, diaspora); total = domestic + diaspora."""
        rel = f"elections/{election_id}"
        for index, scope in enumerate(("domestic", "diaspora", "total")):
            valid = 0
            for entity, (domestic, diaspora) in votes.items():
                count = (domestic, diaspora, domestic + diaspora)[index]
                valid += count
                self.add(
                    f"{rel}/results.csv",
                    "results",
                    election_id=election_id,
                    scope=scope,
                    entity_id=entity,
                    votes=count,
                )
            self.add(
                f"{rel}/results_totals.csv",
                "results_totals",
                election_id=election_id,
                scope=scope,
                valid_votes=valid,
            )

    def map(self, election_id: str, entity: str, relation: str, target: str = "") -> None:
        self.add(
            f"elections/{election_id}/entity_map.csv",
            "entity_map",
            election_id=election_id,
            poll_entity_id=entity,
            relation=relation,
            result_entity_id=target,
        )

    def support(self, election_id: str, candidate: str, party: str, kind: str) -> None:
        self.add(
            f"elections/{election_id}/candidate_support.csv",
            "candidate_support",
            election_id=election_id,
            candidate_entity_id=candidate,
            party_entity_id=party,
            support_type=kind,
        )

    def poll(
        self,
        poll_id: str,
        election_id: str,
        bases: dict[str, list[tuple[str, str, str, str]]],
        *,
        fieldwork_end: str | None,
        published: str,
        headline: bool = True,
        scenario: str = "",
        sample_size: int | None = 1000,
        sample_size_expressed: int | None = None,
        target_scope: str = "domestic",
        coverage: str = "full",
    ) -> None:
        """``bases``: share base → [(option_type, entity_id, share_raw, share_qualifier)]."""
        pollster = poll_id.split("-")[0]
        rel = f"polls/{pollster}"
        self.add(
            f"{rel}/polls.csv",
            "polls",
            poll_id=poll_id,
            pollster_id=pollster,
            election_id=election_id,
            headline="true" if headline else "false",
            scenario=scenario,
            fieldwork_start=fieldwork_end,
            fieldwork_end=fieldwork_end,
            published_date=published,
            sample_size=sample_size,
            sample_size_expressed=sample_size_expressed,
            target_scope=target_scope,
            sponsor_type="self",
            weighting_published="false",
            moe_published="false",
            topline_coverage=coverage,
            document_id=f"{pollster}-doc-001",
            extraction_method="pdf_text",
            source_type="pollster",
        )
        for base, options in bases.items():
            for order, (option_type, entity, share, qualifier) in enumerate(options, start=1):
                self.add(
                    f"{rel}/poll_results.csv",
                    "poll_results",
                    poll_id=poll_id,
                    share_base=base,
                    option_order=order,
                    option_label=entity or option_type,
                    option_type=option_type,
                    entity_id=entity,
                    share_raw=share,
                    share_qualifier=qualifier,
                    source_type="pollster",
                )

    def write(self, root: Path) -> Path:
        for rel, (table, rows) in self.files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            header = TABLES_BY_NAME[table].header
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(header)
                for row in rows:
                    writer.writerow([row.get(column, "") for column in header])
        return root


def party(entity: str, share: str, qualifier: str = "") -> tuple[str, str, str, str]:
    return ("party", entity, share, qualifier)


def candidate(entity: str, share: str) -> tuple[str, str, str, str]:
    return ("candidate", entity, share, "")


def option(option_type: str, share: str) -> tuple[str, str, str, str]:
    return (option_type, "", share, "")


PARL = "parl-2099-cd"  # election day 2099-06-07
R1 = "pres-2099-r1"  # election day 2099-11-01
R2 = "pres-2099-r2"  # election day 2099-11-15

P1 = "exemplar-parl-2099-cd-20990604"
P1_SCENARIO = "exemplar-parl-2099-cd-20990604-scenario-b"
P_EDGE = "exemplar-parl-2099-cd-20990510"
P_OUT = "exemplar-parl-2099-cd-20990509"
P_AFTER = "exemplar-parl-2099-cd-20990606"
P_NODATE = "exemplar-parl-2099-cd-20990530"
P_TOTAL = "secundar-parl-2099-cd-20990601"
P_PARTIAL = "secundar-parl-2099-cd-20990525"
P_PARTIAL_ALL = "tertiar-parl-2099-cd-20990520"
P_R1 = "exemplar-pres-2099-r1-20991028"
P_R2 = "exemplar-pres-2099-r2-20991112"


def synthetic() -> Synth:
    """The synthetic dataset.

    parl-2099-cd results (domestic, diaspora → total):
      alfa 4000 + 500 = 4500; beta 3000 + 1000 = 4000; gama 2920 + 400 = 3320;
      omega 80 + 100 = 180. Valid votes: domestic 10000, diaspora 2000, total 12000.
      r (domestic): alfa .40, beta .30, gama .292, omega .008 (below 1%).
      r (total): alfa .375, beta 1/3, gama .276667, omega .015 (above 1%).
    entity_map: delta alliance_member gama; eta ran_on_list_of beta; zeta withdrawn.
    """
    synth = Synth()
    synth.election(PARL, "parliamentary", 1, "2099-06-07")
    synth.election(R1, "presidential", 1, "2099-11-01")
    synth.election(R2, "presidential", 2, "2099-11-15")
    for entity in ("alfa", "beta", "delta", "eta", "zeta", "omega"):
        synth.entity(entity, "party")
    synth.entity("gama", "alliance")
    for entity in ("ion", "maria", "ana", "vasile"):
        synth.entity(entity, "candidate")
    synth.results(
        PARL,
        {"alfa": (4000, 500), "beta": (3000, 1000), "gama": (2920, 400), "omega": (80, 100)},
    )
    synth.map(PARL, "delta", "alliance_member", "gama")
    synth.map(PARL, "eta", "ran_on_list_of", "beta")
    synth.map(PARL, "zeta", "withdrawn")

    expressed = [
        party("alfa", "42"),
        party("beta", "28"),
        party("delta", "14"),
        party("eta", "5"),
        party("zeta", "7"),
        party("omega", "1", "lt"),
        option("other", "3"),
    ]
    all_respondents = [
        party("alfa", "30"),
        party("beta", "20"),
        party("delta", "10"),
        party("eta", "4"),
        party("zeta", "5"),
        party("omega", "1"),
        option("other", "2"),
        option("undecided", "20"),
        option("would_not_vote", "8"),
    ]
    simple = {"expressed_option": [party("alfa", "40"), party("beta", "35"), party("gama", "25")]}
    synth.poll(
        P1,
        PARL,
        {"all_respondents": all_respondents, "expressed_option": expressed},
        fieldwork_end="2099-06-04",
        published="2099-06-05",
    )
    synth.poll(
        P1_SCENARIO,
        PARL,
        simple,
        fieldwork_end="2099-06-04",
        published="2099-06-05",
        headline=False,
        scenario="Without zeta",
    )
    synth.poll(P_EDGE, PARL, simple, fieldwork_end="2099-05-10", published="2099-05-12")
    synth.poll(P_OUT, PARL, simple, fieldwork_end="2099-05-09", published="2099-05-11")
    synth.poll(P_AFTER, PARL, simple, fieldwork_end="2099-06-06", published="2099-06-07")
    synth.poll(P_NODATE, PARL, simple, fieldwork_end=None, published="2099-05-30")
    synth.poll(
        P_TOTAL,
        PARL,
        {
            "expressed_option": [
                party("alfa", "40"),
                party("beta", "30"),
                party("gama", "25"),
                party("omega", "2"),
                option("other", "3"),
            ]
        },
        fieldwork_end="2099-06-01",
        published="2099-06-02",
        sample_size_expressed=800,
        target_scope="total",
    )
    synth.poll(
        P_PARTIAL,
        PARL,
        {"expressed_option": [party("alfa", "40"), party("beta", "30"), party("gama", "20")]},
        fieldwork_end="2099-05-25",
        published="2099-05-26",
        coverage="partial",
    )
    synth.poll(
        P_PARTIAL_ALL,
        PARL,
        {
            "all_respondents": [
                party("alfa", "20"),
                party("beta", "15"),
                option("undecided", "10"),
            ]
        },
        fieldwork_end="2099-05-20",
        published="2099-05-21",
        coverage="partial",
    )

    # Presidential rounds. r1 (domestic): ion .40, maria .35, ana .25; r2: ion .52, maria .48.
    synth.results(R1, {"ion": (400, 50), "maria": (350, 50), "ana": (250, 0)})
    synth.results(R2, {"ion": (520, 60), "maria": (480, 40)})
    synth.map(R1, "vasile", "excluded")
    synth.support(R1, "ion", "alfa", "nominated")
    synth.support(R1, "maria", "beta", "nominated")
    synth.support(R1, "maria", "gama", "endorsed")
    synth.support(R2, "ion", "alfa", "nominated")
    synth.poll(
        P_R1,
        R1,
        {
            "expressed_option": [
                candidate("ion", "40"),
                candidate("maria", "30"),
                candidate("vasile", "10"),
                candidate("ana", "20"),
            ]
        },
        fieldwork_end="2099-10-28",
        published="2099-10-29",
    )
    synth.poll(
        P_R2,
        R2,
        {"expressed_option": [candidate("ion", "55"), candidate("maria", "45")]},
        fieldwork_end="2099-11-12",
        published="2099-11-13",
    )
    return synth


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    return synthetic().write(tmp_path / "data")


@pytest.fixture
def prepared(data_dir: Path) -> Prepared:
    return prepare(data_dir)


def shares(prepared: Prepared, poll_id: str, column: str = "s") -> dict[str, float]:
    rows = prepared.rows[prepared.rows["poll_id"] == poll_id]
    return dict(zip(rows["entity_id"], rows[column], strict=True))


def poll(prepared: Prepared, poll_id: str) -> pd.Series:
    return prepared.polls.set_index("poll_id").loc[poll_id]


def adjustments(prepared: Prepared, poll_id: str) -> pd.DataFrame:
    return prepared.adjustments[prepared.adjustments["poll_id"] == poll_id]


# --- M-1.1 normalization, OI-1 share base, OI-2 "<x" values, partial toplines -------------


def test_m11_normalizes_the_expressed_base_with_mappings_and_lt(prepared: Prepared) -> None:
    # expressed_option (OI-1). alfa 42; beta 28 + eta 5 = 33; gama = delta 14;
    # zeta 7 dropped; omega <1 → 0.5 (OI-2), below 1% domestic → others: 3 + 0.5 = 3.5.
    # Total 42 + 33 + 14 + 3.5 = 92.5.
    s = shares(prepared, P1)
    assert s == pytest.approx(
        {"alfa": 42 / 92.5, "beta": 33 / 92.5, "gama": 14 / 92.5, OTHERS: 3.5 / 92.5}
    )
    assert poll(prepared, P1)["share_base"] == "expressed_option"
    assert sum(s.values()) == pytest.approx(1.0)


def test_m11_share_base_priority_is_configurable(data_dir: Path) -> None:
    # all_respondents first: alfa 30; beta 20 + 4 = 24; gama 10; zeta dropped; omega 1 and
    # other 2 → others 3. Non-vote options (undecided 20, would-not-vote 8) removed. Total 67.
    config = MethodologyConfig(share_base_priority=("all_respondents", "expressed_option"))
    s = shares(prepare(data_dir, config), P1)
    assert s == pytest.approx({"alfa": 30 / 67, "beta": 24 / 67, "gama": 10 / 67, OTHERS: 3 / 67})


def test_m11_lt_value_fraction_is_configurable_and_logged(data_dir: Path) -> None:
    # lt_fraction 0: omega enters as 0, so others = 3 and the total is 92.
    prepared = prepare(data_dir, MethodologyConfig(lt_fraction=0.0))
    assert shares(prepared, P1)[OTHERS] == pytest.approx(3 / 92)
    lt = adjustments(prepared, P1).query("kind == 'lt_value'")
    assert list(lt["entity_id"]) == ["omega"]
    assert list(lt["rule"]) == ["M-1.1"]
    assert bool(poll(prepared, P1)["has_lt"]) is True


def test_m11_lt_flag_follows_the_value_into_others(prepared: Prepared) -> None:
    rows = prepared.rows.set_index(["poll_id", "entity_id"])
    assert bool(rows.loc[(P1, OTHERS), "has_lt"]) is True
    assert bool(rows.loc[(P1, "alfa"), "has_lt"]) is False


def test_m11_partial_expressed_topline_puts_the_remainder_in_others(prepared: Prepared) -> None:
    # 40 + 30 + 20 = 90 published; the remaining 10 pp go to others: s = .4, .3, .2, .1.
    assert shares(prepared, P_PARTIAL) == pytest.approx(
        {"alfa": 0.4, "beta": 0.3, "gama": 0.2, OTHERS: 0.1}
    )
    residual = adjustments(prepared, P_PARTIAL).query("kind == 'partial_residual'")
    assert residual["share_raw"].tolist() == pytest.approx([10.0])


def test_m11_partial_all_respondents_topline_is_normalized_as_published(
    prepared: Prepared,
) -> None:
    # all_respondents only: alfa 20, beta 15 (undecided removed) → 20/35, 15/35; no residual.
    # gama and omega are not polled: the result "others" holds them (.292 + .008 = .30).
    s = shares(prepared, P_PARTIAL_ALL)
    assert s == pytest.approx({"alfa": 20 / 35, "beta": 15 / 35, OTHERS: 0.0})
    assert shares(prepared, P_PARTIAL_ALL, "r")[OTHERS] == pytest.approx(0.30)
    assert adjustments(prepared, P_PARTIAL_ALL).empty


# --- OI-5: n -------------------------------------------------------------------------------


def test_oi5_n_from_sample_size_times_expressed_share(prepared: Prepared) -> None:
    # all_respondents vote options: 30 + 20 + 10 + 4 + 5 + 1 + 2 = 72% of 1000 → n = 720.
    assert poll(prepared, P1)["n"] == pytest.approx(720.0)
    assert poll(prepared, P1)["n_method"] == "sample_size_x_expressed_share"


def test_oi5_n_prefers_sample_size_expressed(prepared: Prepared) -> None:
    assert poll(prepared, P_TOTAL)["n"] == pytest.approx(800.0)
    assert poll(prepared, P_TOTAL)["n_method"] == "sample_size_expressed"


def test_oi5_n_falls_back_to_sample_size(prepared: Prepared) -> None:
    # Only an expressed base and no sample_size_expressed: n = sample_size (an upper bound).
    assert poll(prepared, P_EDGE)["n"] == pytest.approx(1000.0)
    assert poll(prepared, P_EDGE)["n_method"] == "sample_size"
    # A partial all_respondents base: 1000 x (20 + 15)% = 350.
    assert poll(prepared, P_PARTIAL_ALL)["n"] == pytest.approx(350.0)


def test_oi5_n_missing_without_sample_size(tmp_path: Path) -> None:
    synth = synthetic()
    synth.poll(
        "quartus-parl-2099-cd-20990601",
        PARL,
        {"expressed_option": [party("alfa", "60"), party("beta", "40")]},
        fieldwork_end="2099-06-01",
        published="2099-06-02",
        sample_size=None,
    )
    prepared = prepare(synth.write(tmp_path / "data"))
    row = poll(prepared, "quartus-parl-2099-cd-20990601")
    assert math.isnan(row["n"])
    assert row["n_method"] == "missing"


# --- M-1.2 comparison set ------------------------------------------------------------------


def test_m12_below_threshold_entities_merge_into_others(prepared: Prepared) -> None:
    # omega: r = 80 / 10000 = .008 < .01 → merged; result others = .008.
    r = shares(prepared, P1, "r")
    assert r == pytest.approx({"alfa": 0.40, "beta": 0.30, "gama": 0.292, OTHERS: 0.008})
    merged = adjustments(prepared, P1).query("kind == 'below_threshold'")
    assert list(merged["entity_id"]) == ["omega"]
    assert list(merged["rule"]) == ["M-1.2"]


def test_m12_threshold_is_configurable(data_dir: Path) -> None:
    # Threshold .005: omega (.008) is compared on its own; others = 3 (poll), 0 (result).
    prepared = prepare(data_dir, MethodologyConfig(small_party_threshold=0.005))
    assert shares(prepared, P1)["omega"] == pytest.approx(0.5 / 92.5)
    assert shares(prepared, P1, "r")[OTHERS] == pytest.approx(0.0)


def test_m12_unpolled_contestants_count_in_result_others(prepared: Prepared) -> None:
    # P_EDGE names alfa, beta, gama only (no "other"): s_others = 0, r_others = omega = .008.
    assert shares(prepared, P_EDGE) == pytest.approx(
        {"alfa": 0.40, "beta": 0.35, "gama": 0.25, OTHERS: 0.0}
    )
    assert shares(prepared, P_EDGE, "r")[OTHERS] == pytest.approx(0.008)
    assert poll(prepared, P_EDGE)["k"] == 4


def test_m12_shares_sum_to_one_per_poll(prepared: Prepared) -> None:
    sums = prepared.rows.groupby("poll_id")[["s", "r"]].sum()
    assert sums["s"].tolist() == pytest.approx([1.0] * len(sums))
    assert sums["r"].tolist() == pytest.approx([1.0] * len(sums))


# --- M-1.3 window, weight, final poll; OI-3 scenarios; OI-4 missing dates -------------------


def test_m13_days_before_and_recency_weight(prepared: Prepared) -> None:
    # 2099-06-07 - 2099-06-04 = 3 days; w = exp(-3/7) = 0.651439.
    row = poll(prepared, P1)
    assert row["days_before"] == 3
    assert row["weight"] == pytest.approx(math.exp(-3 / 7))
    assert row["weight"] == pytest.approx(0.651439, abs=1e-6)


def test_m13_window_boundary_is_inclusive(prepared: Prepared) -> None:
    # 2099-05-10 is 28 days before 2099-06-07 (in); 2099-05-09 is 29 days (out).
    assert poll(prepared, P_EDGE)["days_before"] == 28
    assert bool(poll(prepared, P_EDGE)["in_window"]) is True
    assert poll(prepared, P_OUT)["days_before"] == 29
    assert bool(poll(prepared, P_OUT)["in_window"]) is False
    assert bool(poll(prepared, P_OUT)["eligible"]) is True


def test_m13_window_days_is_configurable(data_dir: Path) -> None:
    prepared = prepare(data_dir, MethodologyConfig(window_days=21))
    assert bool(poll(prepared, P_EDGE)["in_window"]) is False


def test_m13_final_poll_is_the_latest_eligible_poll_in_the_window(prepared: Prepared) -> None:
    # exemplar: P1 (fieldwork end 06-04) beats P_EDGE (05-10); P_AFTER (06-06) is later but
    # published on election day (M-1.7); the scenario shares P1's dates but is not headline.
    finals = prepared.polls[prepared.polls["final_poll"]]
    by_unit = dict(zip(finals["unit_id"], finals["poll_id"], strict=True))
    assert by_unit[f"exemplar:{PARL}"] == P1
    # secundar: P_TOTAL (06-01) beats P_PARTIAL (05-25).
    assert by_unit[f"secundar:{PARL}"] == P_TOTAL
    assert finals.groupby("unit_id").size().max() == 1


def test_oi3_scenarios_are_kept_but_excluded(prepared: Prepared) -> None:
    row = poll(prepared, P1_SCENARIO)
    assert row["exclusion_reason"] == NOT_HEADLINE
    assert not row["eligible"]
    assert not row["in_window"]
    assert not row["final_poll"]
    # Kept for transparency: its rows are still prepared.
    assert shares(prepared, P1_SCENARIO)["alfa"] == pytest.approx(0.40)


def test_oi4_poll_without_fieldwork_end_is_excluded(prepared: Prepared) -> None:
    row = poll(prepared, P_NODATE)
    assert row["exclusion_reason"] == NO_FIELDWORK_END
    assert pd.isna(row["days_before"])
    assert math.isnan(row["weight"])
    assert not row["eligible"]
    assert not row["in_window"]


# --- M-1.4 target scope --------------------------------------------------------------------


def test_m14_total_target_uses_total_results(prepared: Prepared) -> None:
    # Total scope: omega .015 ≥ 1% is compared on its own; nothing else is left → r_others 0.
    r = shares(prepared, P_TOTAL, "r")
    assert r == pytest.approx(
        {"alfa": 0.375, "beta": 4000 / 12000, "gama": 3320 / 12000, "omega": 0.015, OTHERS: 0.0}
    )
    assert shares(prepared, P_TOTAL)[OTHERS] == pytest.approx(0.03)
    assert poll(prepared, P_TOTAL)["target_scope"] == "total"


def test_m14_domestic_target_uses_domestic_results(prepared: Prepared) -> None:
    assert shares(prepared, P_EDGE, "r")["alfa"] == pytest.approx(0.40)
    assert poll(prepared, P_EDGE)["target_scope"] == "domestic"


# --- M-1.5 alliances, lists, withdrawals, rounds, candidate → party --------------------------


def test_m15_mappings_are_applied_and_logged(prepared: Prepared) -> None:
    log = adjustments(prepared, P1).query("rule == 'M-1.5'")
    got = {
        (row.kind, row.entity_id, None if pd.isna(row.target_id) else row.target_id, row.share_raw)
        for row in log.itertuples()
    }
    assert got == {
        ("alliance_member", "delta", "gama", 14.0),
        ("ran_on_list_of", "eta", "beta", 5.0),
        ("withdrawn", "zeta", None, 7.0),
    }
    rows = prepared.rows.set_index(["poll_id", "entity_id"])
    assert bool(rows.loc[(P1, "gama"), "adjusted"]) is True
    assert bool(rows.loc[(P1, "alfa"), "adjusted"]) is False
    assert "zeta" not in shares(prepared, P1)


def test_m15_excluded_candidate_is_dropped_and_rest_renormalized(prepared: Prepared) -> None:
    # vasile (10) excluded: ion 40/90, maria 30/90, ana 20/90.
    assert shares(prepared, P_R1) == pytest.approx({"ion": 4 / 9, "maria": 3 / 9, "ana": 2 / 9})
    log = adjustments(prepared, P_R1)
    assert list(zip(log["kind"], log["entity_id"], strict=True)) == [("excluded", "vasile")]


def test_m15_rounds_are_separate_elections(prepared: Prepared) -> None:
    # r2 results: ion 520/1000, maria 480/1000 (domestic); r1 ion = 400/1000.
    assert shares(prepared, P_R2, "r") == pytest.approx({"ion": 0.52, "maria": 0.48})
    assert shares(prepared, P_R1, "r")["ion"] == pytest.approx(0.40)
    units = set(prepared.polls.loc[prepared.polls["pollster_id"] == "exemplar", "unit_id"])
    assert {f"exemplar:{R1}", f"exemplar:{R2}"} <= units


def test_m15_candidate_lean_attributed_only_to_a_single_supporting_party(
    prepared: Prepared,
) -> None:
    # ion: alfa only → alfa; maria: beta (nominated) + gama (endorsed) → none; ana: none.
    parties = shares(prepared, P_R1, "supporting_party_id")
    assert parties["ion"] == "alfa"
    assert pd.isna(parties["maria"])
    assert pd.isna(parties["ana"])
    # Parliamentary rows carry no attribution.
    parliamentary = prepared.rows[prepared.rows["election_id"] == PARL]
    assert parliamentary["supporting_party_id"].isna().all()


def test_m15_unmapped_entity_is_an_error(tmp_path: Path) -> None:
    synth = synthetic()
    synth.entity("psi", "party")
    synth.poll(
        "quartus-parl-2099-cd-20990601",
        PARL,
        {"expressed_option": [party("alfa", "60"), party("psi", "40")]},
        fieldwork_end="2099-06-01",
        published="2099-06-02",
    )
    with pytest.raises(PrepError, match="psi"):
        prepare(synth.write(tmp_path / "data"))


# --- M-1.6 independence unit ---------------------------------------------------------------


def test_m16_unit_is_house_and_election(prepared: Prepared) -> None:
    polls = prepared.polls
    expected = polls["pollster_id"] + ":" + polls["election_id"]
    assert (polls["unit_id"] == expected).all()
    exemplar_parl = polls[polls["unit_id"] == f"exemplar:{PARL}"]
    assert len(exemplar_parl) == 6  # six polls, one unit
    rows = prepared.rows
    assert (rows["unit_id"] == rows["pollster_id"] + ":" + rows["election_id"]).all()


# --- M-1.7 publication timing --------------------------------------------------------------


def test_m17_poll_published_on_election_day_is_excluded(prepared: Prepared) -> None:
    row = poll(prepared, P_AFTER)
    assert row["exclusion_reason"] == PUBLISHED_AFTER_VOTE
    assert bool(row["published_after_vote"]) is True
    assert row["days_before"] == 1
    assert not row["eligible"]
    assert not row["in_window"]
    assert not row["final_poll"]
    assert shares(prepared, P_AFTER)  # still prepared, so it can be shown


def test_m17_poll_published_the_day_before_is_eligible(prepared: Prepared) -> None:
    # P1: published 2099-06-05 < 2099-06-07.
    assert bool(poll(prepared, P1)["published_after_vote"]) is False
    assert bool(poll(prepared, P1)["eligible"]) is True


# --- Loading, summary, CLI -----------------------------------------------------------------


def test_load_errors_raise(data_dir: Path) -> None:
    (data_dir / "registry" / "elections.csv").write_text("wrong,header\n", encoding="utf-8")
    with pytest.raises(PrepError, match="sondaje validate"):
        prepare(data_dir)


def test_rows_carry_poll_level_columns(prepared: Prepared) -> None:
    row = prepared.rows.set_index(["poll_id", "entity_id"]).loc[(P1, "alfa")]
    assert row["pollster_id"] == "exemplar"
    assert row["n"] == pytest.approx(720.0)
    assert row["days_before"] == 3
    assert row["target_scope"] == "domestic"
    assert bool(row["final_poll"]) is True


def test_summary_and_cli(data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    text = summarize(prepare(data_dir))
    assert "11 polls" in text
    assert P_AFTER in text
    out_dir = tmp_path / "out"
    assert main(["prep", "--data-dir", str(data_dir), "--output", str(out_dir)]) == 0
    assert "Per election and house" in capsys.readouterr().out
    rows = pd.read_csv(out_dir / "rows.csv")
    assert len(rows) == len(prepare(data_dir).rows)
    assert (out_dir / "polls.csv").exists()
    assert (out_dir / "adjustments.csv").exists()


def test_cli_reports_errors(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    assert main(["prep", "--data-dir", str(tmp_path / "missing")]) == 1
    assert "error" in capsys.readouterr().err


# --- Real data (smoke test; generic invariants only) ----------------------------------------


def test_real_data_invariants() -> None:
    data = REPO_ROOT / "data"
    if not any(data.glob("polls/*/polls.csv")):
        pytest.skip("no poll data")
    prepared = prepare(data)
    sums = prepared.rows.groupby("poll_id")[["s", "r"]].sum()
    assert sums["s"].tolist() == pytest.approx([1.0] * len(sums))
    assert sums["r"].tolist() == pytest.approx([1.0] * len(sums))
    polls = prepared.polls
    after = polls["published_date"] >= polls["election_date"]
    assert not polls.loc[after, "eligible"].any()
    assert (polls[polls["final_poll"]].groupby("unit_id").size() == 1).all()
    assert polls.loc[polls["final_poll"], "days_before"].le(28).all()
