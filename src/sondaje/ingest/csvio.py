"""Read and write the CSV files of DATA_MODEL.md §3.1 (UTF-8, LF, minimal quoting)."""

import csv
import io
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from sondaje.schema import Table


class CsvFormatError(Exception):
    """A file does not have the header of its table."""


def read_rows(path: Path, table: Table) -> list[dict[str, str]]:
    """Rows of ``path`` as dicts; a missing file has no rows. The header must match ``table``."""
    if not path.is_file():
        return []
    text = path.read_bytes().decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text, newline=""))
    header = next(reader, None)
    if header is None:
        return []
    if tuple(header) != table.header:
        raise CsvFormatError(
            f"{path.as_posix()}: header does not match DATA_MODEL.md §{table.section}"
        )
    return [dict(zip(header, record, strict=True)) for record in reader if record]


def csv_text(header: Sequence[str], rows: Iterable[Mapping[str, object]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow(["" if row.get(c) is None else str(row.get(c)) for c in header])
    return buffer.getvalue()


def write_rows(path: Path, table: Table, rows: Iterable[Mapping[str, object]]) -> None:
    """Write ``rows`` under the header of ``table`` (UTF-8 without BOM, LF line endings)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(csv_text(table.header, rows).encode("utf-8"))
