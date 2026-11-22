"""Shared helpers for the validation tests: copies of the fixture data directories."""

import csv
import datetime as dt
import io
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from sondaje.validation import Issue, ValidationConfig, validate

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
FIXTURE_REFERENCE_DATE = dt.date(2099, 12, 31)
"""The fictitious fixtures are dated 2099 (DATA_MODEL.md §10); R-11 needs a later 'today'."""


class DataDir:
    """A writable copy of a fixture data directory, with small CSV editing helpers.

    Row positions are file line numbers, as in validation messages (header = 1).
    """

    def __init__(self, root: Path) -> None:
        self.root = root

    def path(self, rel: str) -> Path:
        return self.root / rel

    def read_bytes(self, rel: str) -> bytes:
        return self.path(rel).read_bytes()

    def write_bytes(self, rel: str, content: bytes) -> None:
        self.path(rel).parent.mkdir(parents=True, exist_ok=True)
        self.path(rel).write_bytes(content)

    def remove(self, rel: str) -> None:
        self.path(rel).unlink()

    def read(self, rel: str) -> tuple[list[str], list[list[str]]]:
        text = self.read_bytes(rel).decode("utf-8")
        records = list(csv.reader(io.StringIO(text, newline="")))
        return records[0], records[1:]

    def write(self, rel: str, header: list[str], rows: list[list[str]]) -> None:
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
        self.write_bytes(rel, buffer.getvalue().encode("utf-8"))

    def update(self, rel: str, line: int, **changes: str) -> None:
        header, rows = self.read(rel)
        row = rows[line - 2]
        for column, value in changes.items():
            row[header.index(column)] = value
        self.write(rel, header, rows)

    def append_copy(self, rel: str, line: int, **changes: str) -> None:
        header, rows = self.read(rel)
        row = list(rows[line - 2])
        for column, value in changes.items():
            row[header.index(column)] = value
        self.write(rel, header, [*rows, row])

    def delete(self, rel: str, *lines: int) -> None:
        header, rows = self.read(rel)
        drop = {line - 2 for line in lines}
        self.write(rel, header, [row for i, row in enumerate(rows) if i not in drop])

    def replace_value(self, rel: str, column: str, old: str, new: str) -> None:
        header, rows = self.read(rel)
        index = header.index(column)
        for row in rows:
            if row[index] == old:
                row[index] = new
        self.write(rel, header, rows)

    def issues(self, reference_date: dt.date = FIXTURE_REFERENCE_DATE) -> list[Issue]:
        return validate(self.root, ValidationConfig(reference_date=reference_date))


type DataDirFactory = Callable[[str], DataDir]


@pytest.fixture
def fixture_copy(tmp_path: Path) -> DataDirFactory:
    """Return a factory that copies ``tests/fixtures/<name>/`` into a temporary directory."""

    def make(name: str) -> DataDir:
        target = tmp_path / name
        shutil.copytree(FIXTURES / name, target)
        return DataDir(target)

    return make
