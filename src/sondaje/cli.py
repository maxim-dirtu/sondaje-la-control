"""Command-line interface: the ``sondaje`` console script.

Subcommands are plugged in through :data:`COMMANDS`. To add one (e.g.
``validate`` or ``ingest-results``), write a registrar in the module that owns
the feature and append it to :data:`COMMANDS`::

    def register(subparsers: Subparsers) -> None:
        parser = subparsers.add_parser("validate", help="Validate data/ files.")
        parser.add_argument("paths", nargs="*")
        parser.set_defaults(handler=run)


    def run(args: argparse.Namespace) -> int:
        ...
        return 0  # process exit code

Handlers receive the parsed arguments and return the process exit code.
"""

import argparse
from collections.abc import Callable, Sequence

from sondaje import __version__
from sondaje.ingest.archive import register as register_archive
from sondaje.ingest.double_entry import register as register_double_entry_diff
from sondaje.ingest.extract_html import register as register_extract_html
from sondaje.ingest.extract_pdf import register as register_extract_pdf
from sondaje.ingest.results import register as register_ingest_results
from sondaje.metrics.errors import register as register_errors
from sondaje.metrics.market import register as register_market
from sondaje.prep import register as register_prep
from sondaje.validation.command import register as register_validate

type Subparsers = argparse._SubParsersAction[argparse.ArgumentParser]
type Registrar = Callable[[Subparsers], None]
type Handler = Callable[[argparse.Namespace], int]

COMMANDS: list[Registrar] = [
    register_validate,
    register_ingest_results,
    register_archive,
    register_extract_pdf,
    register_extract_html,
    register_double_entry_diff,
    register_prep,
    register_errors,
    register_market,
]
"""Registrars for every subcommand, in the order they appear in ``--help``."""


def build_parser(commands: Sequence[Registrar] | None = None) -> argparse.ArgumentParser:
    """Build the top-level parser and register every subcommand."""
    parser = argparse.ArgumentParser(
        prog="sondaje",
        description="Toolkit for the 'Sondaje la control' pollster case study.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    registrars = COMMANDS if commands is None else commands
    if registrars:
        subparsers = parser.add_subparsers(title="commands", dest="command", metavar="<command>")
        for register in registrars:
            register(subparsers)
    return parser


def main(argv: Sequence[str] | None = None, commands: Sequence[Registrar] | None = None) -> int:
    """Run the CLI and return the process exit code.

    Without a subcommand, the help text is printed and the exit code is 0.
    """
    parser = build_parser(commands)
    args = parser.parse_args(argv)
    handler: Handler | None = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0
    return handler(args)
