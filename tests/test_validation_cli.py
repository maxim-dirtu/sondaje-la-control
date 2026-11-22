"""The ``sondaje validate`` subcommand."""

import re

import pytest

from conftest import FIXTURES, REPO_ROOT, DataDirFactory
from sondaje.cli import main

EXAMPLE = str(FIXTURES / "example")
FUTURE = ["--reference-date", "2099-12-31"]
ISSUE_LINE = re.compile(r"^\S+\.csv:\d+: \[R-\d{2}\] (error|warning): .+$")


def test_valid_data_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", "--data-dir", EXAMPLE, *FUTURE]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[-1] == "0 error(s), 2 warning(s)"
    assert all(ISSUE_LINE.match(line) for line in lines[:-1])
    assert all("[R-33] warning" in line for line in lines[:-1])


def test_strict_fails_on_warnings(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", "--data-dir", EXAMPLE, *FUTURE, "--strict"]) == 1


def test_quiet_hides_warnings(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", "--data-dir", EXAMPLE, *FUTURE, "--quiet"]) == 0
    assert capsys.readouterr().out.splitlines() == ["0 error(s), 2 warning(s)"]


def test_errors_exit_non_zero(
    fixture_copy: DataDirFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    data = fixture_copy("example")
    data.update("polls/exemplar/polls.csv", 2, fieldwork_start="2099-05-25")
    assert main(["validate", "--data-dir", str(data.root), *FUTURE]) == 1
    out = capsys.readouterr().out
    [line] = [line for line in out.splitlines() if "[R-80]" in line]
    assert ISSUE_LINE.match(line)
    assert "polls/exemplar/polls.csv:2: [R-80] error: " in line


def test_reference_date_defaults_to_today(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", "--data-dir", EXAMPLE]) == 1
    assert "[R-11] error" in capsys.readouterr().out


def test_invalid_reference_date_is_rejected() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["validate", "--reference-date", "31.12.2099"])
    assert exc.value.code == 2


def test_default_data_dir_is_the_repository_data(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    assert main(["validate"]) == 0
    assert capsys.readouterr().out.splitlines() == ["0 error(s), 0 warning(s)"]


def test_help_lists_validate(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["--help"])
    assert "validate" in capsys.readouterr().out
