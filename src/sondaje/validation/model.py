"""Data structures shared by the validation rules."""

import datetime as dt
from collections.abc import Iterator
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from pathlib import Path

from sondaje.schema import Location, Table

SHARE_SUM_TOLERANCE_PP = Decimal("2.0")
"""DATA_MODEL.md §7 parameter ``share_sum_tolerance_pp`` (R-90, R-91)."""

MAX_POLL_AGE_DAYS = 365
"""DATA_MODEL.md §7 parameter ``max_poll_age_days`` (R-85)."""


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, order=True)
class Issue:
    """One finding, reported as ``path:row: [rule] severity: message``."""

    path: str
    row: int | None
    rule: str
    severity: Severity
    message: str

    def format(self) -> str:
        location = self.path if self.row is None else f"{self.path}:{self.row}"
        return f"{location}: [{self.rule}] {self.severity}: {self.message}"


@dataclass(frozen=True)
class ValidationConfig:
    """Parameters of DATA_MODEL.md §7."""

    reference_date: dt.date
    share_sum_tolerance_pp: Decimal = SHARE_SUM_TOLERANCE_PP
    max_poll_age_days: int = MAX_POLL_AGE_DAYS


@dataclass
class Row:
    """One data row: raw cells plus typed values (``None`` when empty or invalid)."""

    line: int
    raw: dict[str, str]
    typed: dict[str, object]

    def get_str(self, column: str) -> str | None:
        value = self.typed.get(column)
        return value if isinstance(value, str) else None

    def get_date(self, column: str) -> dt.date | None:
        value = self.typed.get(column)
        return value if isinstance(value, dt.date) else None

    def get_int(self, column: str) -> int | None:
        value = self.typed.get(column)
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    def get_decimal(self, column: str) -> Decimal | None:
        value = self.typed.get(column)
        return value if isinstance(value, Decimal) else None

    def get_bool(self, column: str) -> bool | None:
        value = self.typed.get(column)
        return value if isinstance(value, bool) else None

    def get_partial_date(self, column: str) -> tuple[int, ...] | None:
        value = self.typed.get(column)
        return value if isinstance(value, tuple) else None

    def is_empty(self, column: str) -> bool:
        return self.raw.get(column, "") == ""


@dataclass
class DataFile:
    """A CSV file under ``data/``, located and (if its header is valid) parsed."""

    table: Table
    location: Location
    directory_id: str | None
    display_path: str
    path: Path
    rows: list[Row] = field(default_factory=list)

    @property
    def has_rows(self) -> bool:
        return bool(self.rows)


@dataclass
class Dataset:
    """Every recognised data file, grouped by location."""

    root: Path
    registry: dict[str, DataFile] = field(default_factory=dict)
    elections: dict[str, dict[str, DataFile]] = field(default_factory=dict)
    polls: dict[str, dict[str, DataFile]] = field(default_factory=dict)

    def files(self) -> Iterator[DataFile]:
        yield from self.registry.values()
        for group in (self.elections, self.polls):
            for files in group.values():
                yield from files.values()

    def registry_rows(self, table: str) -> list[Row]:
        data_file = self.registry.get(table)
        return data_file.rows if data_file else []

    def election_file(self, election_id: str, table: str) -> DataFile | None:
        return self.elections.get(election_id, {}).get(table)

    def election_rows(self, election_id: str, table: str) -> list[Row]:
        data_file = self.election_file(election_id, table)
        return data_file.rows if data_file else []

    def registry_index(self, table: str, column: str) -> dict[str, Row]:
        """First row per value of ``column`` in a registry (later duplicates are R-30)."""
        index: dict[str, Row] = {}
        for row in self.registry_rows(table):
            value = row.get_str(column)
            if value is not None:
                index.setdefault(value, row)
        return index


@dataclass
class Reporter:
    """Collects issues."""

    issues: list[Issue] = field(default_factory=list)

    def error(self, path: str, row: int | None, rule: str, message: str) -> None:
        self.issues.append(Issue(path, row, rule, Severity.ERROR, message))

    def warning(self, path: str, row: int | None, rule: str, message: str) -> None:
        self.issues.append(Issue(path, row, rule, Severity.WARNING, message))
