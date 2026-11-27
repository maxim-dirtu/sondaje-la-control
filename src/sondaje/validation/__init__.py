"""Validation of the CSV files under ``data/`` against docs/DATA_MODEL.md.

Implements the integrity rules of DATA_MODEL.md §7 (R-01…R-94). The schema itself is
in :mod:`sondaje.schema`. Entry points: :func:`validate` and the ``sondaje validate``
subcommand (:mod:`sondaje.validation.command`).
"""

from pathlib import Path

from sondaje.validation import (
    loader,
    rules_dates,
    rules_elections,
    rules_files,
    rules_inventory,
    rules_polls,
    rules_provenance,
    rules_registries,
    rules_sums,
)
from sondaje.validation.history import check_against
from sondaje.validation.model import (
    MAX_POLL_AGE_DAYS,
    SHARE_SUM_TOLERANCE_PP,
    Issue,
    Reporter,
    Severity,
    ValidationConfig,
)

__all__ = [
    "MAX_POLL_AGE_DAYS",
    "SHARE_SUM_TOLERANCE_PP",
    "Issue",
    "Severity",
    "ValidationConfig",
    "validate",
]


def validate(data_dir: Path, config: ValidationConfig, against: str | None = None) -> list[Issue]:
    """Validate every file under ``data_dir`` and return the issues, sorted by location.

    ``against`` is a git reference (e.g. ``main``) for the append-only check R-34; it is
    skipped when ``None``.
    """
    reporter = Reporter()
    dataset = loader.load(data_dir, reporter)
    rules_files.run(dataset, reporter)
    rules_provenance.run(dataset, config, reporter)
    rules_registries.run(dataset, reporter)
    rules_elections.run(dataset, reporter)
    rules_polls.run(dataset, reporter)
    rules_inventory.run(dataset, reporter)
    rules_dates.run(dataset, config, reporter)
    rules_sums.run(dataset, config, reporter)
    if against is not None:
        check_against(data_dir, against, reporter)
    return sorted(
        set(reporter.issues), key=lambda i: (i.path, i.row or 0, i.rule, i.severity, i.message)
    )
