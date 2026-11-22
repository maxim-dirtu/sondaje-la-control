"""The schema in code (sondaje.schema) agrees with docs/DATA_MODEL.md and with data/."""

import re

import pytest

from conftest import FIXTURES, REPO_ROOT
from sondaje.schema import (
    MANIFEST_PROVENANCE,
    MODES,
    OPTION_TYPES,
    PROVENANCE,
    SOURCE_TYPES,
    TABLES,
    ColumnType,
    Location,
    Table,
    tables_at,
)

DOC = (REPO_ROOT / "docs" / "DATA_MODEL.md").read_text(encoding="utf-8")
CELL_SPLIT = re.compile(r"(?<!\\)\|")
BACKTICKED = re.compile(r"`([^`]+)`")


def section(number: str) -> str:
    """The text of the ``### <number> ...`` section, up to the next heading."""
    match = re.search(rf"^###? {re.escape(number)}[ .].*?$(.*?)(?=^#)", DOC, flags=re.M | re.S)
    assert match, f"section {number} not found"
    return match.group(1)


def table_rows(text: str) -> list[list[str]]:
    """Rows of the first markdown table in ``text`` (header and separator skipped)."""
    lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("|"):
            lines.append(line)
        elif lines:
            break
    rows = [[cell.strip() for cell in CELL_SPLIT.split(line)[1:-1]] for line in lines]
    return rows[2:]


def documented_columns(table: Table) -> list[list[str]]:
    """Column rows (name, type, req, allowed, ...) of a §6 table, provenance block expanded."""
    rows = []
    for row in table_rows(section(table.section)):
        if row[0] == "provenance block":
            rows.extend(table_rows(section("5.1")))
        else:
            rows.append(row)
    return rows


def documented_values(cell: str) -> set[str]:
    if cell == "see below":
        return {row[0].strip("`") for row in table_rows(DOC.split("`option_type` values:")[1])}
    if cell == "§5.1":
        return set(SOURCE_TYPES)
    if "`mode` enum" in cell:
        return set(MODES)
    return set(BACKTICKED.findall(cell))


@pytest.mark.parametrize("table", TABLES, ids=lambda t: t.name)
def test_columns_match_data_model(table: Table) -> None:
    rows = documented_columns(table)
    assert [row[0].strip("`") for row in rows] == list(table.header)
    for row, column in zip(rows, table.columns, strict=True):
        name, type_, required, allowed = row[0].strip("`"), row[1], row[2], row[3]
        assert (name, type_, required) == (name, column.type.value, column.required.value)
        if column.type in (ColumnType.ENUM, ColumnType.LIST_ENUM):
            assert documented_values(allowed) == set(column.values), name
        assert ("FK →" in allowed) == (column.references is not None), name
        if column.references is not None:
            assert f"`{column.references.split('.')[0]}" in allowed, name


def test_option_types_match_data_model() -> None:
    assert documented_values("see below") == set(OPTION_TYPES)


def test_every_table_ends_with_the_provenance_block() -> None:
    for table in TABLES:
        block = MANIFEST_PROVENANCE if table.name == "archive_manifest" else PROVENANCE
        assert table.columns[-len(block) :] == block, table.name


def header_reference() -> dict[str, str]:
    """File name → header line, from the §6.14 copy-paste block."""
    block = re.search(r"```text\n(.*?)```", section("6.14"), flags=re.S)
    assert block
    reference = {}
    for group in block.group(1).strip().split("\n\n"):
        label, header = group.splitlines()
        reference[label.split()[0].rsplit("/", 1)[-1]] = header
    return reference


def test_header_reference_matches_schema() -> None:
    reference = header_reference()
    assert reference == {table.filename: ",".join(table.header) for table in TABLES}


def test_committed_data_headers_match_schema() -> None:
    data = REPO_ROOT / "data"
    checked = 0
    for path in sorted(data.rglob("*.csv")):
        relative = path.relative_to(data).parts
        if relative[0] == "raw":
            continue
        table = tables_at(Location(relative[0]))[path.name]
        first_line = path.read_bytes().decode("utf-8").split("\n", 1)[0]
        assert first_line == ",".join(table.header), path
        checked += 1
    assert checked > 0


def test_example_fixture_is_the_data_model_example() -> None:
    """tests/fixtures/example is DATA_MODEL.md §10, byte for byte."""
    example = DOC[DOC.index("## 10. Worked example") :]
    blocks = re.findall(r"^`data/([^`]+\.csv)`\n```csv\n(.*?)```", example, flags=re.M | re.S)
    assert blocks
    fixture = FIXTURES / "example"
    expected = dict(blocks)
    actual = {
        path.relative_to(fixture).as_posix(): path.read_bytes().decode("utf-8")
        for path in fixture.rglob("*.csv")
    }
    assert actual == expected
