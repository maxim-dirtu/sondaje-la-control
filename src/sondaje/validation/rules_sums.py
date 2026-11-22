"""Sum and duplicate rules R-90…R-94."""

from collections import defaultdict
from decimal import Decimal

from sondaje.schema import NON_VOTE_OPTION_TYPES, POLL_RESULTS, POLLS
from sondaje.validation.model import DataFile, Dataset, Reporter, Row, ValidationConfig

HUNDRED = Decimal(100)


def check_shares(
    polls_file: DataFile | None,
    results_file: DataFile,
    config: ValidationConfig,
    reporter: Reporter,
) -> None:
    """R-90, R-91, R-92.

    When ``low`` exceeds ``100 + tol``, only R-91 is reported (it covers both toplines).
    """
    shown = results_file.display_path
    tol = config.share_sum_tolerance_pp
    coverage = {
        poll_id: row.get_str("topline_coverage")
        for row in (polls_file.rows if polls_file else [])
        if (poll_id := row.get_str("poll_id")) is not None
    }
    groups: dict[tuple[str, str], list[Row]] = defaultdict(list)
    for row in results_file.rows:
        poll_id, base = row.get_str("poll_id"), row.get_str("share_base")
        if poll_id is not None and base is not None:
            groups[poll_id, base].append(row)
        if base == "expressed_option" and row.get_str("option_type") in NON_VOTE_OPTION_TYPES:
            reporter.warning(
                shown,
                row.line,
                "R-92",
                f"non-vote option {row.raw['option_type']!r} in the expressed_option base",
            )
    for (poll_id, base), rows in groups.items():
        shares = [row.get_decimal("share_raw") for row in rows]
        if any(share is None for share in shares):
            continue
        low = sum(
            (s for row, s in zip(rows, shares, strict=True) if row.is_empty("share_qualifier")),
            Decimal(0),
        )
        high = low + sum(
            (
                s
                for row, s in zip(rows, shares, strict=True)
                if row.get_str("share_qualifier") == "lt"
            ),
            Decimal(0),
        )
        where = f"poll {poll_id!r}, base {base!r}"
        if low > HUNDRED + tol:
            reporter.error(
                shown, rows[0].line, "R-91", f"{where}: exact shares sum to {low} > 100 + {tol}"
            )
        elif coverage.get(poll_id) == "full" and (low - tol > HUNDRED or high + tol < HUNDRED):
            reporter.error(
                shown,
                rows[0].line,
                "R-90",
                f"{where}: full topline sums to {low}"
                + (f"-{high}" if high != low else "")
                + f", outside 100 ± {tol}",
            )


def check_duplicates(dataset: Dataset, reporter: Reporter) -> None:
    """R-93 (duplicate headline polls) and R-94 (possible duplicates without fieldwork dates)."""
    dated: dict[tuple[str, ...], tuple[str, int]] = {}
    undated: dict[tuple[str, ...], tuple[str, int]] = {}
    for files in dataset.polls.values():
        polls_file = files.get(POLLS.name)
        if polls_file is None:
            continue
        for row in polls_file.rows:
            if row.get_bool("headline") is not True:
                continue
            pollster, election = row.raw["pollster_id"], row.raw["election_id"]
            start, end = row.raw["fieldwork_start"], row.raw["fieldwork_end"]
            if start and end:
                key = (pollster, election, start, end)
                first = dated.setdefault(key, (polls_file.display_path, row.line))
                if first[1] != row.line or first[0] != polls_file.display_path:
                    reporter.error(
                        polls_file.display_path,
                        row.line,
                        "R-93",
                        f"duplicate poll: another headline poll of {pollster!r} for {election!r} "
                        f"has fieldwork {start}..{end} ({first[0]}:{first[1]})",
                    )
            elif not start and not end:
                key = (pollster, election, row.raw["published_date"])
                first = undated.setdefault(key, (polls_file.display_path, row.line))
                if first[1] != row.line or first[0] != polls_file.display_path:
                    reporter.warning(
                        polls_file.display_path,
                        row.line,
                        "R-94",
                        f"possible duplicate: another undated headline poll of {pollster!r} for "
                        f"{election!r} was published on {key[2]} ({first[0]}:{first[1]})",
                    )


def run(dataset: Dataset, config: ValidationConfig, reporter: Reporter) -> None:
    for files in dataset.polls.values():
        results_file = files.get(POLL_RESULTS.name)
        if results_file is not None:
            check_shares(files.get(POLLS.name), results_file, config, reporter)
    check_duplicates(dataset, reporter)
