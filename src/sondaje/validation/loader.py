"""Locate the files under ``data/`` and parse them (R-01, R-02, R-03, R-05, R-10)."""

import csv
import io
import os
from pathlib import Path

from sondaje.schema import (
    PROVENANCE_COLUMNS,
    RESERVED_FILES,
    Location,
    Required,
    Table,
    tables_at,
)
from sondaje.validation.cells import CellError, parse_cell
from sondaje.validation.model import DataFile, Dataset, Reporter, Row

UTF8_BOM = b"\xef\xbb\xbf"
IGNORED_FILE_NAMES = (".gitkeep",)
RAW_DIRECTORY = "raw"
README = "README.md"


def display_path(path: Path) -> str:
    """Path as shown in messages: relative to the working directory when possible, '/'-separated."""
    try:
        return Path(os.path.relpath(path)).as_posix()
    except ValueError:  # another drive on Windows
        return path.as_posix()


def discover(root: Path, reporter: Reporter) -> Dataset:
    """Find every file under ``root`` and attach it to its table (file part of R-05)."""
    dataset = Dataset(root=root)
    if not root.is_dir():
        reporter.error(display_path(root), None, "R-05", "data directory not found")
        return dataset
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        parts = path.relative_to(root).parts
        if parts[0] == RAW_DIRECTORY or parts == (README,) or path.name in IGNORED_FILE_NAMES:
            continue
        shown = display_path(path)
        if len(parts) == 2 and parts[0] == Location.REGISTRY:
            table = tables_at(Location.REGISTRY).get(parts[1])
            if table is not None:
                dataset.registry[table.name] = DataFile(table, Location.REGISTRY, None, shown, path)
                continue
        elif len(parts) == 3 and parts[0] in (Location.ELECTION, Location.POLL):
            location = Location(parts[0])
            directory_id, filename = parts[1], parts[2]
            group = dataset.elections if location is Location.ELECTION else dataset.polls
            files = group.setdefault(directory_id, {})
            table = tables_at(location).get(filename)
            if table is not None:
                files[table.name] = DataFile(table, location, directory_id, shown, path)
                continue
            if filename in RESERVED_FILES.get(location, ()):
                reporter.warning(
                    shown, None, "R-05", "reserved file (DATA_MODEL.md §6.13); not validated"
                )
                continue
        reporter.error(shown, None, "R-05", "unexpected file (not listed in DATA_MODEL.md §2.1)")
    # Directories that hold only ignored files (e.g. a lone .gitkeep) still count as directories.
    for location, group in ((Location.ELECTION, dataset.elections), (Location.POLL, dataset.polls)):
        base = root / location
        if base.is_dir():
            for child in sorted(base.iterdir()):
                if child.is_dir():
                    group.setdefault(child.name, {})
    return dataset


def _header_message(table: Table, header: list[str]) -> str:
    expected = list(table.header)
    missing = [name for name in expected if name not in header]
    extra = [name for name in header if name not in expected]
    parts = []
    if missing:
        parts.append(f"missing {', '.join(missing)}")
    if extra:
        parts.append(f"unexpected {', '.join(extra)}")
    if len(set(header)) != len(header):
        parts.append("duplicate column names")
    if not parts:
        parts.append("columns are out of order")
    return (
        f"header does not match DATA_MODEL.md §{table.section} ({'; '.join(parts)}); "
        f"expected: {','.join(expected)}"
    )


def _parse_row(data_file: DataFile, line: int, record: list[str], reporter: Reporter) -> Row:
    raw = dict(zip(data_file.table.header, record, strict=True))
    typed: dict[str, object] = {}
    for column, value in zip(data_file.table.columns, record, strict=True):
        typed[column.name] = None
        if value == "":
            if column.required is Required.YES:
                rule = "R-10" if column.name in PROVENANCE_COLUMNS else "R-03"
                reporter.error(
                    data_file.display_path, line, rule, f"{column.name} is required but empty"
                )
            continue
        try:
            typed[column.name] = parse_cell(column, value)
        except CellError as exc:
            reporter.error(data_file.display_path, line, "R-03", f"{column.name}: {exc}")
    return Row(line=line, raw=raw, typed=typed)


def read(data_file: DataFile, reporter: Reporter) -> None:
    """Parse one file into ``data_file.rows`` (R-01, R-02, R-03, R-10)."""
    shown = data_file.display_path
    content = data_file.path.read_bytes()
    if content.startswith(UTF8_BOM):
        reporter.error(shown, 1, "R-01", "file starts with a UTF-8 BOM")
        content = content[len(UTF8_BOM) :]
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        line = content[: exc.start].count(b"\n") + 1
        reporter.error(shown, line, "R-01", f"not valid UTF-8 ({exc.reason})")
        return
    if "\r" in text:
        line = text[: text.index("\r")].count("\n") + 1
        reporter.error(shown, line, "R-01", "CR line ending found; use LF line endings")
    if text == "":
        reporter.error(shown, 1, "R-02", "file is empty; the header line is required")
        return
    if not text.endswith(("\n", "\r")):
        reporter.error(shown, text.count("\n") + 1, "R-01", "file does not end with a newline")

    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        header = next(reader)
        if header != list(data_file.table.header):
            reporter.error(shown, 1, "R-02", _header_message(data_file.table, header))
            return
        previous_line = reader.line_num
        for record in reader:
            line = previous_line + 1
            previous_line = reader.line_num
            if any("\n" in field or "\r" in field for field in record):
                reporter.error(shown, line, "R-01", "line break inside a field")
                continue
            if len(record) != len(header):
                reporter.error(
                    shown, line, "R-03", f"row has {len(record)} fields; expected {len(header)}"
                )
                continue
            data_file.rows.append(_parse_row(data_file, line, record, reporter))
    except csv.Error as exc:
        reporter.error(shown, reader.line_num, "R-01", f"malformed CSV: {exc}")


def load(root: Path, reporter: Reporter) -> Dataset:
    """Discover and parse every data file under ``root``."""
    dataset = discover(root, reporter)
    for data_file in dataset.files():
        read(data_file, reporter)
    return dataset
