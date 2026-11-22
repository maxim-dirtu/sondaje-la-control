"""Provenance rules R-11…R-15 (R-10 is checked while parsing, in the loader)."""

from sondaje.schema import POLLS, RESULTS, RESULTS_TOTALS
from sondaje.validation.model import Dataset, Reporter, ValidationConfig

INDEX_SOURCE_TYPES = ("wikipedia", "aggregator")


def run(dataset: Dataset, config: ValidationConfig, reporter: Reporter) -> None:
    for data_file in dataset.files():
        name = data_file.table.name
        has_verified = "verified" in data_file.table.header
        for row in data_file.rows:
            shown, line = data_file.display_path, row.line
            retrieved_at = row.get_date("retrieved_at")
            source_type = row.get_str("source_type")
            if retrieved_at is not None and retrieved_at > config.reference_date:
                reporter.error(
                    shown,
                    line,
                    "R-11",
                    f"retrieved_at {retrieved_at} is after the reference date "
                    f"{config.reference_date}",
                )
            if name == POLLS.name:
                published = row.get_date("published_date")
                if retrieved_at is not None and published is not None and retrieved_at < published:
                    reporter.error(
                        shown,
                        line,
                        "R-12",
                        f"retrieved_at {retrieved_at} is before published_date {published}",
                    )
            if source_type == "other" and row.is_empty("notes"):
                reporter.warning(
                    shown, line, "R-13", "source_type 'other' needs an explanation in notes"
                )
            if (
                has_verified
                and row.get_bool("verified") is True
                and source_type in INDEX_SOURCE_TYPES
            ):
                reporter.error(
                    shown,
                    line,
                    "R-14",
                    f"verified = true is not allowed for source_type {source_type!r} "
                    "(an index, not a source)",
                )
            if name in (RESULTS.name, RESULTS_TOTALS.name) and source_type not in (
                None,
                "official",
            ):
                reporter.warning(
                    shown, line, "R-15", f"official results with source_type {source_type!r}"
                )
