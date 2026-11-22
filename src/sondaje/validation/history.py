"""R-34: append-only files keep every row of a git reference (e.g. ``main``) in place."""

import csv
import io
import subprocess
from pathlib import Path

from sondaje.schema import TABLES, Location, Table
from sondaje.validation.loader import display_path
from sondaje.validation.model import Reporter

APPEND_ONLY = tuple(table for table in TABLES if table.append_only)


class GitError(RuntimeError):
    """A git command failed."""


def _git(cwd: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            check=False,
            timeout=60,
        )
    except OSError as exc:
        raise GitError(f"cannot run git: {exc}") from exc
    if result.returncode != 0:
        raise GitError(result.stderr.decode("utf-8", "replace").strip() or "git failed")
    return result.stdout.decode("utf-8")


def _append_only_table(relative: tuple[str, ...]) -> Table | None:
    """The append-only table of a path relative to the data directory, if any."""
    for table in APPEND_ONLY:
        if Location.REGISTRY in table.locations and relative == (Location.REGISTRY, table.filename):
            return table
        if (
            Location.ELECTION in table.locations
            and len(relative) == 3
            and relative[0] == Location.ELECTION
            and relative[2] == table.filename
        ):
            return table
    return None


def _keys(text: str, table: Table) -> list[tuple[int, tuple[str, ...]]]:
    """(line, key) of every data row; rows that do not parse are skipped."""
    reader = csv.reader(io.StringIO(text, newline=""))
    rows: list[tuple[int, tuple[str, ...]]] = []
    header = next(reader, None)
    if header is None:
        return rows
    positions = [header.index(column) for column in table.key if column in header]
    if len(positions) != len(table.key):
        return rows
    previous_line = reader.line_num
    for record in reader:
        line, previous_line = previous_line + 1, reader.line_num
        if len(record) == len(header):
            rows.append((line, tuple(record[p] for p in positions)))
    return rows


def check_against(data_dir: Path, ref: str, reporter: Reporter) -> None:
    """Compare every append-only file under ``data_dir`` with its version at ``ref``.

    Each row present at ``ref`` must still be at the same position with the same key
    (DATA_MODEL.md §2.2). Non-key fields may change. One error is reported per file, at the
    first row that differs.
    """
    shown_dir = display_path(data_dir)
    try:
        top = Path(_git(data_dir, "rev-parse", "--show-toplevel").strip())
        prefix = data_dir.resolve().relative_to(top.resolve()).as_posix()
        _git(top, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
        listing = _git(top, "ls-tree", "-r", "--name-only", ref, "--", prefix)
    except (GitError, ValueError) as exc:
        reporter.error(shown_dir, None, "R-34", f"cannot compare with {ref!r}: {exc}")
        return
    for repo_path in sorted(filter(None, listing.splitlines())):
        relative = tuple(Path(repo_path).relative_to(prefix).parts)
        table = _append_only_table(relative)
        if table is None:
            continue
        current_path = data_dir.joinpath(*relative)
        shown = display_path(current_path)
        old_rows = _keys(_git(top, "show", f"{ref}:{repo_path}"), table)
        if not current_path.is_file():
            if old_rows:
                reporter.error(
                    shown, None, "R-34", f"append-only file with rows on {ref} was deleted"
                )
            continue
        new_rows = _keys(current_path.read_bytes().decode("utf-8", "replace"), table)
        for index, (old_line, old_key) in enumerate(old_rows):
            if index >= len(new_rows):
                reporter.error(
                    shown,
                    None,
                    "R-34",
                    f"row {old_line} on {ref} ({', '.join(old_key)}) was removed",
                )
                break
            new_line, new_key = new_rows[index]
            if new_key != old_key:
                reporter.error(
                    shown,
                    new_line,
                    "R-34",
                    f"expected the row of line {old_line} on {ref} "
                    f"({', '.join(table.key)}) = ({', '.join(old_key)}); "
                    "rows of an append-only file are never removed, reordered, or re-keyed",
                )
                break
