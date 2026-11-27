"""Double-entry comparison: ``sondaje double-entry-diff <pass-a> <pass-b>`` (T-011).

Implements the comparison step of the manual double-entry protocol (docs/POLL_INGESTION.md,
DATA_MODEL.md §5.2 ``manual_double_entry``). Two people (or agents) transcribe the same
archived publication independently, each into the final file format: a ``polls.csv`` and a
``poll_results.csv`` (DATA_MODEL.md §6.11, §6.12) in a directory of their own. This command
reports **every** difference between the two passes:

* a poll present in one pass only, and every differing ``polls.csv`` cell (dates, ``n``,
  population, sponsor, wording, ...);
* a share base present in one pass only;
* an option (matched by its verbatim ``option_label``) present in one pass only, i.e. a
  missing or extra option or a label typed differently;
* every differing cell of an option present in both (``share_raw``, ``share_qualifier``,
  ``option_order``, ``option_type``, ``entity_id``, provenance).

``retrieved_at`` and ``notes`` are not compared (they legitimately differ between passes).
The exit code is 0 when the passes agree, 1 when there is any mismatch, and 2 when an input
cannot be read. Mismatches are resolved against the archived original, never by choosing a
pass, and logged in the task file.
"""

import argparse
import io
import sys
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from sondaje.ingest.csvio import CsvFormatError, read_rows
from sondaje.schema import POLL_RESULTS, POLLS, Table

if TYPE_CHECKING:
    from sondaje.cli import Subparsers

IGNORED_COLUMNS = frozenset({"retrieved_at", "notes"})
"""Columns that may differ between two passes without being a transcription mismatch."""


class DiffInputError(Exception):
    """An input is missing or does not have a polls / poll_results header."""


@dataclass(frozen=True)
class Mismatch:
    file: str
    where: str
    message: str

    def format(self) -> str:
        return f"{self.file}: {self.where}: {self.message}"


@dataclass
class Pass:
    """One transcription pass: its polls and poll_results rows (either may be absent)."""

    path: Path
    polls: list[dict[str, str]] | None = None
    results: list[dict[str, str]] | None = None


def _table_of(path: Path) -> Table:
    first_line = path.read_bytes().decode("utf-8-sig").split("\n", 1)[0].strip("\r")
    for table in (POLLS, POLL_RESULTS):
        if first_line == ",".join(table.header):
            return table
    raise DiffInputError(
        f"{path.as_posix()}: not a polls.csv or poll_results.csv (header of DATA_MODEL.md "
        "§6.11 or §6.12 expected)"
    )


def load_pass(path: Path) -> Pass:
    """Read a pass: a directory with polls.csv and/or poll_results.csv, or one such file."""
    loaded = Pass(path)
    if path.is_dir():
        files = [path / POLLS.filename, path / POLL_RESULTS.filename]
        files = [f for f in files if f.is_file()]
        if not files:
            raise DiffInputError(f"{path.as_posix()}: no polls.csv or poll_results.csv")
    elif path.is_file():
        files = [path]
    else:
        raise DiffInputError(f"{path.as_posix()}: not found")
    for file in files:
        table = _table_of(file)
        try:
            rows = read_rows(file, table)
        except (CsvFormatError, ValueError) as exc:
            raise DiffInputError(f"{file.as_posix()}: {exc}") from exc
        if table is POLLS:
            loaded.polls = rows
        else:
            loaded.results = rows
    return loaded


def _cells(a: dict[str, str], b: dict[str, str], columns: Sequence[str]) -> list[str]:
    return [
        f"{column}: A={a.get(column, '')!r} B={b.get(column, '')!r}"
        for column in columns
        if column not in IGNORED_COLUMNS and a.get(column, "") != b.get(column, "")
    ]


def pair_ids(
    ids_a: Sequence[str], ids_b: Sequence[str]
) -> tuple[dict[str, str], list[str], list[str]]:
    """Pair poll IDs: equal IDs first; if the leftovers are equally many, pair them in order
    (a differing ``poll_id`` usually means a differing date, which is then reported as such).
    Returns (A → B, only in A, only in B)."""
    common = [i for i in ids_a if i in set(ids_b)]
    pairs = {i: i for i in common}
    left_a = [i for i in ids_a if i not in pairs]
    left_b = [i for i in ids_b if i not in set(common)]
    if left_a and len(left_a) == len(left_b):
        pairs.update(zip(left_a, left_b, strict=True))
        return pairs, [], []
    return pairs, left_a, left_b


def _unique(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(values))


def compare_polls(
    rows_a: list[dict[str, str]], rows_b: list[dict[str, str]]
) -> tuple[list[Mismatch], dict[str, str], set[str]]:
    """Mismatches, the A → B poll pairing, and the poll IDs found in one pass only."""
    file = POLLS.filename
    by_a = {row["poll_id"]: row for row in rows_a}
    by_b = {row["poll_id"]: row for row in rows_b}
    mismatches = [
        Mismatch(file, f"poll {poll_id}", "listed twice in one pass")
        for rows in (rows_a, rows_b)
        for poll_id, count in Counter(row["poll_id"] for row in rows).items()
        if count > 1
    ]
    pairs, only_a, only_b = pair_ids(list(by_a), list(by_b))
    mismatches += [Mismatch(file, f"poll {i}", "only in pass A") for i in only_a]
    mismatches += [Mismatch(file, f"poll {i}", "only in pass B") for i in only_b]
    for id_a, id_b in pairs.items():
        where = f"poll {id_a}" if id_a == id_b else f"poll {id_a} (B: {id_b})"
        for message in _cells(by_a[id_a], by_b[id_b], POLLS.header):
            mismatches.append(Mismatch(file, where, message))
    return mismatches, pairs, {*only_a, *only_b}


def _options(
    rows: list[dict[str, str]],
) -> dict[tuple[str, str], dict[tuple[str, int], dict[str, str]]]:
    """(poll_id, share_base) → (option_label, occurrence) → row."""
    groups: dict[tuple[str, str], dict[tuple[str, int], dict[str, str]]] = defaultdict(dict)
    for row in rows:
        group = groups[row["poll_id"], row["share_base"]]
        occurrence = sum(1 for label, _ in group if label == row["option_label"])
        group[row["option_label"], occurrence] = row
    return groups


def _describe(row: dict[str, str]) -> str:
    value = ("<" if row.get("share_qualifier") == "lt" else "") + row.get("share_raw", "")
    return f"order {row.get('option_order', '')}, share_raw {value}"


def compare_results(
    rows_a: list[dict[str, str]],
    rows_b: list[dict[str, str]],
    pairs: dict[str, str] | None = None,
    reported: set[str] | frozenset[str] = frozenset(),
) -> list[Mismatch]:
    """Mismatches between two ``poll_results`` passes. ``pairs`` maps A's poll IDs to B's
    (from :func:`compare_polls`); without it the IDs are paired here. Polls in ``reported``
    were already reported as present in one pass only and are skipped."""
    file = POLL_RESULTS.filename
    mismatches: list[Mismatch] = []
    if pairs is None:
        pairs, only_a, only_b = pair_ids(
            _unique([r["poll_id"] for r in rows_a]), _unique([r["poll_id"] for r in rows_b])
        )
        mismatches += [Mismatch(file, f"poll {i}", "only in pass A") for i in only_a]
        mismatches += [Mismatch(file, f"poll {i}", "only in pass B") for i in only_b]
        reported = {*only_a, *only_b}
    to_a = {b: a for a, b in pairs.items()}
    groups_a = _options(rows_a)
    groups_b = {
        (to_a.get(poll_id, poll_id), base): options
        for (poll_id, base), options in _options(rows_b).items()
    }
    for key in sorted(set(groups_a) | set(groups_b)):
        poll_id, base = key
        if poll_id in reported:
            continue
        where = f"poll {poll_id}, base {base}"
        if key not in groups_b:
            mismatches.append(
                Mismatch(file, where, f"base only in pass A ({len(groups_a[key])} options)")
            )
            continue
        if key not in groups_a:
            mismatches.append(
                Mismatch(file, where, f"base only in pass B ({len(groups_b[key])} options)")
            )
            continue
        options_a, options_b = groups_a[key], groups_b[key]
        for option in options_a:
            label = option[0] + (f" (#{option[1] + 1})" if option[1] else "")
            if option not in options_b:
                text = f"option {label!r} only in pass A ({_describe(options_a[option])})"
                mismatches.append(Mismatch(file, where, text))
                continue
            columns = [c for c in POLL_RESULTS.header if c != "poll_id"]
            for message in _cells(options_a[option], options_b[option], columns):
                mismatches.append(Mismatch(file, where, f"option {label!r}: {message}"))
        for option in options_b:
            if option not in options_a:
                label = option[0] + (f" (#{option[1] + 1})" if option[1] else "")
                text = f"option {label!r} only in pass B ({_describe(options_b[option])})"
                mismatches.append(Mismatch(file, where, text))
    return mismatches


def compare(pass_a: Pass, pass_b: Pass) -> list[Mismatch]:
    """Every mismatch between two passes (see the module docstring)."""
    mismatches: list[Mismatch] = []
    pairs: dict[str, str] | None = None
    reported: set[str] = set()
    for name, a, b in (
        (POLLS.filename, pass_a.polls, pass_b.polls),
        (POLL_RESULTS.filename, pass_a.results, pass_b.results),
    ):
        if (a is None) != (b is None):
            side = "A" if a is not None else "B"
            mismatches.append(Mismatch(name, "file", f"present in pass {side} only"))
    if pass_a.polls is not None and pass_b.polls is not None:
        found, pairs, reported = compare_polls(pass_a.polls, pass_b.polls)
        mismatches += found
    if pass_a.results is not None and pass_b.results is not None:
        mismatches += compare_results(pass_a.results, pass_b.results, pairs, reported)
    return mismatches


# --- CLI ------------------------------------------------------------------------------------------


def register(subparsers: "Subparsers") -> None:
    parser = subparsers.add_parser(
        "double-entry-diff",
        help="Compare two independent transcriptions of a poll; exit 1 on any mismatch.",
        description=(
            "Compare two independent transcription passes of the same publication. Each pass "
            "is a directory with polls.csv and/or poll_results.csv (DATA_MODEL.md §6.11, §6.12), "
            "or a single such file. Every missing or extra poll, base, or option and every "
            "differing cell is reported (retrieved_at and notes are ignored). Exit code: 0 = the "
            "passes agree, 1 = mismatches, 2 = unreadable input."
        ),
    )
    parser.add_argument("pass_a", type=Path, help="pass A (directory or CSV file)")
    parser.add_argument("pass_b", type=Path, help="pass B (directory or CSV file)")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    out = sys.stdout
    if isinstance(out, io.TextIOWrapper):
        out.reconfigure(errors="backslashreplace")
    try:
        mismatches = compare(load_pass(args.pass_a), load_pass(args.pass_b))
    except (DiffInputError, OSError, UnicodeDecodeError) as exc:
        sys.stderr.write(f"double-entry-diff: error: {exc}\n")
        return 2
    for mismatch in mismatches:
        out.write(mismatch.format() + "\n")
    if mismatches:
        out.write(
            f"{len(mismatches)} mismatch(es): resolve each one against the archived original "
            "and log it in the task file\n"
        )
        return 1
    out.write("0 mismatches: the two passes agree\n")
    return 0
