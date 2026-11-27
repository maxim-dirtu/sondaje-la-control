"""``sondaje double-entry-diff``: every difference between two transcription passes.

Acceptance criterion of T-011: a deliberately introduced mismatch is detected. The passes
are copies of the worked example of DATA_MODEL.md §10 (tests/fixtures/example).
"""

import shutil
from pathlib import Path

import pytest

from conftest import FIXTURES, DataDir
from sondaje.cli import main
from sondaje.ingest.double_entry import compare, load_pass

EXAMPLE = FIXTURES / "example" / "polls" / "exemplar"
POLL = "exemplar-parl-2099-cd-20990524"


def make_pass(tmp_path: Path, name: str) -> DataDir:
    target = tmp_path / name
    target.mkdir()
    for filename in ("polls.csv", "poll_results.csv"):
        shutil.copy(EXAMPLE / filename, target / filename)
    return DataDir(target)


@pytest.fixture
def passes(tmp_path: Path) -> tuple[DataDir, DataDir]:
    return make_pass(tmp_path, "pass-a"), make_pass(tmp_path, "pass-b")


def diff(a: DataDir, b: DataDir) -> list[str]:
    return [m.format() for m in compare(load_pass(a.root), load_pass(b.root))]


def test_identical_passes_agree(passes: tuple[DataDir, DataDir]) -> None:
    a, b = passes
    assert diff(a, b) == []


def test_ignored_columns_do_not_count(passes: tuple[DataDir, DataDir]) -> None:
    a, b = passes
    b.update("polls.csv", 2, notes="Typed by pass B.", retrieved_at="2099-05-28")
    b.update("poll_results.csv", 3, notes="Checked twice.")
    assert diff(a, b) == []


def test_deliberate_value_mismatch_is_detected(
    passes: tuple[DataDir, DataDir], capsys: pytest.CaptureFixture[str]
) -> None:
    """The acceptance test: one share typed differently in pass B."""
    a, b = passes
    b.update("poll_results.csv", 3, share_raw="23")
    assert diff(a, b) == [
        f"poll_results.csv: poll {POLL}, base all_respondents: "
        "option 'Partidul Beta': share_raw: A='22' B='23'"
    ]
    assert main(["double-entry-diff", str(a.root), str(b.root)]) == 1
    out = capsys.readouterr().out
    assert "share_raw: A='22' B='23'" in out
    assert out.strip().endswith("log it in the task file")


def test_missing_and_extra_options_are_detected(passes: tuple[DataDir, DataDir]) -> None:
    a, b = passes
    b.delete("poll_results.csv", 7)
    b.update("poll_results.csv", 2, option_label="Partidul  Alfa")
    found = diff(a, b)
    where = f"poll_results.csv: poll {POLL}, base all_respondents: "
    assert where + "option 'Alt partid' only in pass A (order 6, share_raw 4)" in found
    assert where + "option 'Partidul Alfa' only in pass A (order 1, share_raw 28)" in found
    assert where + "option 'Partidul  Alfa' only in pass B (order 1, share_raw 28)" in found


def test_metadata_mismatches_are_detected(passes: tuple[DataDir, DataDir]) -> None:
    a, b = passes
    b.update("polls.csv", 2, sample_size="1000", population_geo="residents_and_diaspora")
    b.update("poll_results.csv", 10, share_qualifier="lt")
    found = diff(a, b)
    assert f"polls.csv: poll {POLL}: sample_size: A='1100' B='1000'" in found
    assert f"polls.csv: poll {POLL}: population_geo: A='residents' B='residents_and_diaspora'" in (
        found
    )
    expressed = f"poll_results.csv: poll {POLL}, base expressed_option: option 'Partidul Alfa': "
    assert expressed + "share_qualifier: A='' B='lt'" in found


def test_a_different_date_is_reported_as_a_date_not_as_two_polls(
    passes: tuple[DataDir, DataDir],
) -> None:
    a, b = passes
    other = "exemplar-parl-2099-cd-20990523"
    b.update("polls.csv", 2, poll_id=other, fieldwork_end="2099-05-23")
    b.replace_value("poll_results.csv", "poll_id", POLL, other)
    assert diff(a, b) == [
        f"polls.csv: poll {POLL} (B: {other}): poll_id: A='{POLL}' B='{other}'",
        f"polls.csv: poll {POLL} (B: {other}): fieldwork_end: A='2099-05-24' B='2099-05-23'",
    ]


def test_missing_base_poll_and_file(passes: tuple[DataDir, DataDir], tmp_path: Path) -> None:
    a, b = passes
    b.delete("poll_results.csv", *range(10, 16))
    assert diff(a, b) == [
        f"poll_results.csv: poll {POLL}, base expressed_option: base only in pass A (6 options)"
    ]
    b.remove("polls.csv")
    assert "polls.csv: file: present in pass A only" in diff(a, b)
    header, rows = a.read("polls.csv")
    a.write("polls.csv", header, [*rows, list(rows[0])])
    a.update("polls.csv", 3, poll_id=POLL + "-2")
    assert any("only in pass A" in line for line in diff(a, make_pass(tmp_path, "pass-c")))


def test_single_files_can_be_compared(passes: tuple[DataDir, DataDir]) -> None:
    a, b = passes
    b.update("poll_results.csv", 5, share_raw="30")
    found = [
        m.format()
        for m in compare(
            load_pass(a.path("poll_results.csv")), load_pass(b.path("poll_results.csv"))
        )
    ]
    assert len(found) == 1 and "share_raw: A='6' B='30'" in found[0]


def test_unreadable_inputs_exit_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("a,b\n1,2\n", encoding="utf-8")
    assert main(["double-entry-diff", str(bad), str(bad)]) == 2
    assert main(["double-entry-diff", str(tmp_path / "nope"), str(bad)]) == 2
    empty = tmp_path / "empty"
    empty.mkdir()
    assert main(["double-entry-diff", str(empty), str(empty)]) == 2
    assert "double-entry-diff: error:" in capsys.readouterr().err


def test_cli_agreement_exits_0(
    passes: tuple[DataDir, DataDir], capsys: pytest.CaptureFixture[str]
) -> None:
    a, b = passes
    assert main(["double-entry-diff", str(a.root), str(b.root)]) == 0
    assert "0 mismatches" in capsys.readouterr().out
