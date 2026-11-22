"""Cell-level type checks (DATA_MODEL.md §3.2)."""

import datetime as dt
import re
from decimal import Decimal

from sondaje.schema import Column, ColumnType

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SLUG_MAX_LENGTH = 64
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PARTIAL_DATE_RE = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")
INT_RE = re.compile(r"^(0|[1-9][0-9]*)$")
DECIMAL_RE = re.compile(r"^(0|[1-9][0-9]*)(\.[0-9]+)?$")
URL_RE = re.compile(r"^https?://\S+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
HEX_COLOR_RE = re.compile(r"^#[0-9A-F]{6}$")
RAW_PATH_PREFIX = "data/raw/"


class CellError(ValueError):
    """A cell does not match its column type."""


def parse_date(value: str) -> dt.date:
    if not DATE_RE.match(value):
        raise CellError(f"{value!r} is not a YYYY-MM-DD date")
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise CellError(f"{value!r} is not a real calendar date") from None


def parse_partial_date(value: str) -> tuple[int, ...]:
    match = PARTIAL_DATE_RE.match(value)
    if not match:
        raise CellError(f"{value!r} is not a YYYY[-MM[-DD]] partial date")
    parts = tuple(int(part) for part in match.groups() if part is not None)
    try:
        dt.date(parts[0], parts[1] if len(parts) > 1 else 1, parts[2] if len(parts) > 2 else 1)
    except ValueError:
        raise CellError(f"{value!r} has an invalid month or day") from None
    return parts


def _check_range(column: Column, number: Decimal, value: str) -> None:
    if column.min_value is not None and number < column.min_value:
        raise CellError(f"{value!r} is below the minimum {column.min_value}")
    if column.max_value is not None and number > column.max_value:
        raise CellError(f"{value!r} is above the maximum {column.max_value}")


def _check_enum(column: Column, value: str) -> str:
    if value not in column.values:
        raise CellError(f"{value!r} is not one of: {', '.join(column.values)}")
    return value


def parse_cell(column: Column, value: str) -> object:
    """Return the typed value of a non-empty cell, or raise :class:`CellError`."""
    if value != value.strip():
        raise CellError("leading or trailing whitespace")
    match column.type:
        case ColumnType.SLUG:
            if not SLUG_RE.match(value):
                raise CellError(f"{value!r} is not a slug (lowercase a-z, 0-9, single hyphens)")
            if len(value) > SLUG_MAX_LENGTH:
                raise CellError(f"slug is longer than {SLUG_MAX_LENGTH} characters")
            return value
        case ColumnType.DATE:
            return parse_date(value)
        case ColumnType.PARTIAL_DATE:
            return parse_partial_date(value)
        case ColumnType.INT:
            if not INT_RE.match(value):
                raise CellError(f"{value!r} is not a non-negative integer")
            _check_range(column, Decimal(value), value)
            return int(value)
        case ColumnType.DECIMAL:
            if not DECIMAL_RE.match(value):
                raise CellError(f"{value!r} is not a non-negative decimal with '.' separator")
            number = Decimal(value)
            _check_range(column, number, value)
            return number
        case ColumnType.BOOL:
            if value not in ("true", "false"):
                raise CellError(f"{value!r} is not 'true' or 'false'")
            return value == "true"
        case ColumnType.ENUM:
            return _check_enum(column, value)
        case ColumnType.URL:
            if not URL_RE.match(value):
                raise CellError(f"{value!r} is not an absolute http(s) URL")
            return value
        case ColumnType.SHA256:
            if not SHA256_RE.match(value):
                raise CellError(f"{value!r} is not a lowercase hex SHA-256")
            return value
        case ColumnType.HEX_COLOR:
            if not HEX_COLOR_RE.match(value):
                raise CellError(f"{value!r} is not an uppercase #RRGGBB color")
            return value
        case ColumnType.PATH:
            if "\\" in value or not value.startswith(RAW_PATH_PREFIX):
                raise CellError(f"{value!r} is not a '/'-separated path under {RAW_PATH_PREFIX}")
            if ".." in value.split("/"):
                raise CellError(f"{value!r} contains '..'")
            return value
        case ColumnType.TEXT:
            return value
        case ColumnType.LIST_ENUM:
            items = value.split(";")
            for item in items:
                _check_enum(column, item)
            if len(set(items)) != len(items):
                raise CellError(f"{value!r} has duplicate items")
            return tuple(items)
    raise AssertionError(f"unhandled column type {column.type}")  # pragma: no cover
