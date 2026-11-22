"""Date rules R-80…R-86 on ``polls.csv``."""

from sondaje.schema import ELECTIONS, POLLS
from sondaje.validation.model import Dataset, Reporter, ValidationConfig
from sondaje.validation.rules_registries import previous_round_id


def run(dataset: Dataset, config: ValidationConfig, reporter: Reporter) -> None:
    elections = dataset.registry_index(ELECTIONS.name, "election_id")
    for files in dataset.polls.values():
        polls_file = files.get(POLLS.name)
        if polls_file is None:
            continue
        shown = polls_file.display_path
        for row in polls_file.rows:
            line = row.line
            start, end = row.get_date("fieldwork_start"), row.get_date("fieldwork_end")
            published = row.get_date("published_date")
            if start is not None and end is not None and start > end:
                reporter.error(
                    shown, line, "R-80", f"fieldwork_start {start} is after fieldwork_end {end}"
                )
            if published is not None and end is not None and published < end:
                reporter.error(
                    shown, line, "R-82", f"published_date {published} is before fieldwork_end {end}"
                )
            if row.is_empty("fieldwork_start") and row.is_empty("fieldwork_end"):
                reporter.warning(
                    shown, line, "R-86", "no fieldwork dates; the poll cannot enter M-1.3 windows"
                )
            election_id = row.get_str("election_id")
            election = elections.get(election_id) if election_id else None
            election_date = election.get_date("election_date") if election else None
            if election is None or election_date is None:
                continue
            last_day = end or start
            if last_day is not None and last_day >= election_date:
                reporter.error(
                    shown,
                    line,
                    "R-81",
                    f"fieldwork ends {last_day}, not before election day {election_date} "
                    "(exit polls are out of scope)",
                )
            if published is not None and published >= election_date:
                reporter.warning(
                    shown,
                    line,
                    "R-83",
                    f"published_date {published} is on or after election day {election_date}",
                )
            reference_day = end or published
            if (
                reference_day is not None
                and (election_date - reference_day).days > config.max_poll_age_days
            ):
                reporter.warning(
                    shown,
                    line,
                    "R-85",
                    f"{reference_day} is more than {config.max_poll_age_days} days before "
                    f"election day {election_date}",
                )
            round_ = election.get_int("round")
            previous_id = previous_round_id(election_id) if election_id else None
            previous = (
                elections.get(previous_id) if previous_id and round_ and round_ >= 2 else None
            )
            previous_date = previous.get_date("election_date") if previous else None
            first_day = start or end or published
            if previous_date is not None and first_day is not None and first_day <= previous_date:
                reporter.error(
                    shown,
                    line,
                    "R-84",
                    f"poll for round {round_} starts {first_day}, not after round {round_ - 1} "
                    f"({previous_date})",
                )
