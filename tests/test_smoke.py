"""Smoke tests: the package imports and the CLI starts."""

import shutil
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import pytest

import sondaje
from sondaje.cli import Subparsers, main


def test_version_matches_installed_metadata() -> None:
    assert sondaje.__version__ == version("sondaje")


def test_help_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "usage: sondaje" in capsys.readouterr().out


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"sondaje {sondaje.__version__}"


def test_no_command_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "usage: sondaje" in capsys.readouterr().out


def test_unknown_command_is_rejected() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["no-such-command"])
    assert exc.value.code == 2


def test_registered_command_is_dispatched() -> None:
    def register(subparsers: Subparsers) -> None:
        parser = subparsers.add_parser("echo", help="Return the given exit code.")
        parser.add_argument("code", type=int)
        parser.set_defaults(handler=lambda args: args.code)

    assert main(["echo", "3"], commands=[register]) == 3


@pytest.mark.parametrize(
    "command",
    [
        pytest.param([sys.executable, "-m", "sondaje"], id="python-m"),
        pytest.param(
            [shutil.which("sondaje", path=str(Path(sys.executable).parent)) or "sondaje"],
            id="console-script",
        ),
    ],
)
def test_cli_help_in_subprocess(command: list[str]) -> None:
    result = subprocess.run(
        [*command, "--help"], capture_output=True, text=True, check=False, timeout=60
    )
    assert result.returncode == 0, result.stderr
    assert "usage: sondaje" in result.stdout
