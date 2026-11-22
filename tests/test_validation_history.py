"""R-34: append-only files compared with a git reference (``sondaje validate --against``)."""

import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import FIXTURE_REFERENCE_DATE, FIXTURES, DataDir
from sondaje.validation import Issue, ValidationConfig, validate

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")

ENTITIES = "registry/entities.csv"
ENTITY_MAP = "elections/parl-2099-cd/entity_map.csv"


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.org",
            "-c",
            "core.autocrlf=false",
            *args,
        ],
        cwd=repo,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def repo(tmp_path: Path) -> DataDir:
    """A git repository whose ``main`` holds the §10 example under ``data/``."""
    shutil.copytree(FIXTURES / "example", tmp_path / "data")
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "fixture")
    return DataDir(tmp_path / "data")


def r34(data: DataDir, ref: str = "main") -> list[Issue]:
    issues = validate(data.root, ValidationConfig(FIXTURE_REFERENCE_DATE), against=ref)
    return [issue for issue in issues if issue.rule == "R-34"]


def test_unchanged(repo: DataDir) -> None:
    assert r34(repo) == []


def test_appended_row_passes(repo: DataDir) -> None:
    repo.append_copy(ENTITIES, 8, entity_id="sigma")
    assert r34(repo) == []


def test_corrected_non_key_field_passes(repo: DataDir) -> None:
    repo.update(ENTITIES, 3, name="Partidul Beta Nou", notes="Renamed in 2099.")
    assert r34(repo) == []


def test_removed_row_fails(repo: DataDir) -> None:
    repo.delete(ENTITIES, 3)
    [issue] = r34(repo)
    assert issue.path.endswith(ENTITIES)
    assert issue.row == 3


def test_removed_last_row_fails(repo: DataDir) -> None:
    repo.delete(ENTITY_MAP, 4)
    [issue] = r34(repo)
    assert issue.path.endswith(ENTITY_MAP)
    assert "removed" in issue.message


def test_reordered_rows_fail(repo: DataDir) -> None:
    header, rows = repo.read(ENTITIES)
    repo.write(ENTITIES, header, [rows[1], rows[0], *rows[2:]])
    assert len(r34(repo)) == 1


def test_changed_id_fails(repo: DataDir) -> None:
    repo.update(ENTITIES, 8, entity_id="omega-2")
    [issue] = r34(repo)
    assert issue.row == 8


def test_deleted_file_fails(repo: DataDir) -> None:
    repo.remove(ENTITY_MAP)
    [issue] = r34(repo)
    assert "deleted" in issue.message


def test_owned_files_are_not_checked(repo: DataDir) -> None:
    repo.delete("elections/parl-2099-cd/results.csv", 2)
    assert r34(repo) == []


def test_unknown_reference_is_an_error(repo: DataDir) -> None:
    [issue] = r34(repo, ref="no-such-branch")
    assert "cannot compare" in issue.message
