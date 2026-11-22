"""The ``sondaje validate`` subcommand."""

import argparse
import datetime as dt
import io
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from sondaje.validation import validate
from sondaje.validation.model import Severity, ValidationConfig

if TYPE_CHECKING:
    from sondaje.cli import Subparsers


def _iso_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a YYYY-MM-DD date: {value!r}") from None


def register(subparsers: "Subparsers") -> None:
    parser = subparsers.add_parser(
        "validate",
        help="Validate the CSV files under data/ (DATA_MODEL.md section 7).",
        description=(
            "Check every file under the data directory against docs/DATA_MODEL.md: format, "
            "header, types, keys, references, provenance, and the integrity rules R-01...R-94. "
            "Issues are printed as 'path:row: [rule] severity: message'. The exit code is 1 "
            "if there is an error (or, with --strict, a warning), else 0."
        ),
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="data directory to validate (default: data)",
    )
    parser.add_argument(
        "--reference-date",
        type=_iso_date,
        default=None,
        metavar="YYYY-MM-DD",
        help="date used as 'today' by R-11 (default: today)",
    )
    parser.add_argument(
        "--against",
        metavar="REF",
        default=None,
        help="also check the append-only files against a git reference, e.g. main (R-34)",
    )
    parser.add_argument("--strict", action="store_true", help="fail on warnings too")
    parser.add_argument("--quiet", action="store_true", help="print errors only, not warnings")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    config = ValidationConfig(reference_date=args.reference_date or dt.date.today())
    issues = validate(args.data_dir, config, against=args.against)
    errors = sum(1 for issue in issues if issue.severity is Severity.ERROR)
    warnings = len(issues) - errors
    out = sys.stdout
    if isinstance(out, io.TextIOWrapper):
        out.reconfigure(errors="backslashreplace")
    for issue in issues:
        if args.quiet and issue.severity is Severity.WARNING:
            continue
        out.write(issue.format() + "\n")
    out.write(f"{errors} error(s), {warnings} warning(s)\n")
    return 1 if errors or (args.strict and warnings) else 0
