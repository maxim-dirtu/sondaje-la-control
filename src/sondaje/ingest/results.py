"""Official results ingestion: ``sondaje ingest-results <election_id>`` (T-010).

Implements METHODOLOGY M-1.4 (domestic, diaspora, and total results kept separate).

Sources (all published by the Permanent Electoral Authority, AEP, on prezenta.roaep.ro, and by
the Central Electoral Bureau, BEC):

* ``pv.json`` (SICPV): the final reports ("procese-verbale", PVs) of the BEC (national
  totalization) and of every constituency bureau, in machine-readable form. **The committed
  values come from these PVs**: ``total`` = the BEC national PV; ``diaspora`` = the PV of
  constituency 43 (polling stations abroad and postal votes); ``domestic`` = the sum of the
  in-country constituency PVs. The pipeline stops if domestic + diaspora differs from the
  national PV for any contestant or for the valid votes.
* The BEC national PV as a PDF with a text layer. Every contestant's votes and every totals
  field used are compared with it; any difference stops the pipeline. The BEC final report is
  the control total (T-010).
* The per-polling-station PVs (CSV, polling stations and postal votes). They are aggregated to
  the three scopes as an independent **cross-check** and the differences are reported. They are
  never written to the committed files: where they differ, the BEC/constituency PVs win.

Raw downloads go to ``data/raw/elections/<election_id>/`` (git-ignored). The committed
``archive_manifest.csv`` records each source URL with the SHA-256 of the downloaded bytes. A
downloaded file whose hash equals the manifest's keeps the manifest's ``retrieved_at``, so
re-running the command reproduces the committed files byte for byte.

URL patterns and file formats were learned from github.com/gov2-ro/prezenta.roaep.ro (no
license, so no code was reused) and from the files themselves.
"""

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import re
import sys
import urllib.request
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from sondaje.schema import ARCHIVE_MANIFEST, RESULTS, RESULTS_TOTALS, SCOPES
from sondaje.validation.rules_elections import CONTESTANT_TYPES

if TYPE_CHECKING:
    from sondaje.cli import Subparsers

USER_AGENT = "sondaje-la-control/0.1"
"""prezenta.roaep.ro refuses some generic clients (e.g. curl's default user agent)."""

TOTALS_COLUMNS = ("registered_voters", "voters", "valid_votes", "invalid_votes")
DIASPORA_CODE = "SR"
"""``county_code`` of constituency 43 (abroad, including postal votes) in ``pv.json``."""
DIASPORA_PRECINCT_COUNTY = "43"
"""``precinct_county_nce`` of polling stations abroad in the station CSV files."""
MUNICIPALITY_CODE = "B"
SECTOR_CODES = frozenset({"S1", "S2", "S3", "S4", "S5", "S6"})
"""Bucharest sector PVs: top-level when no Bucharest-wide PV exists (presidential elections),
sub-totals of the Bucharest constituency PV (``B``) otherwise (parliamentary elections)."""
VOTES_SUFFIX = "-voturi"
INDEPENDENT_SUFFIX = "-CANDIDAT INDEPENDENT"
RAW_PREFIX = "data/raw/elections"

PV_JSON = "pv_json"
BEC_PDF = "bec_pdf"
BEC_REPORT = "bec_report"
STATIONS = "stations"
STATIONS_POSTAL = "stations_postal"


class IngestError(Exception):
    """The sources are inconsistent or cannot be read; nothing is written."""


# --- Configuration -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Document:
    """One source file, archived in ``archive_manifest.csv``."""

    key: str
    url: str
    format: str
    title: str = ""
    published_date: str = ""
    notes: str = ""

    @property
    def filename(self) -> str:
        return self.url.rsplit("/", 1)[-1]


@dataclass(frozen=True)
class PvFields:
    """PV field letters that hold each ``results_totals`` column (same letters in every PV)."""

    registered_voters: str
    voters: str
    valid_votes: str
    invalid_votes: str
    blank_votes: str | None = None
    description: str = ""

    def letter(self, column: str) -> str:
        return getattr(self, column)


@dataclass(frozen=True)
class StationFields:
    """Field letters in a station CSV file."""

    valid_votes: str
    voters: str = "b"


@dataclass(frozen=True)
class ElectionSource:
    """Where and how to read the official results of one election."""

    election_id: str
    category: str
    """SICPV category code in ``pv.json`` (``CD``, ``PRSD``)."""
    pv_fields: PvFields
    station_fields: StationFields
    postal_fields: StationFields
    documents: tuple[Document, ...]

    def document(self, key: str) -> Document:
        for document in self.documents:
            if document.key == key:
                return document
        raise KeyError(key)


def _documents(
    site: str,
    pv_pdf: str,
    pv_pdf_title: str,
    pv_pdf_date: str,
    bec_report: str,
    bec_report_date: str,
    category: str,
) -> tuple[Document, ...]:
    base = f"https://prezenta.roaep.ro/{site}"
    suffix = category.lower()
    return (
        Document(
            PV_JSON,
            f"{base}/data/json/sicpv/pv/pv.json",
            "json",
            notes=(
                "SICPV final reports (PVs) of the BEC (national totalization) and of every "
                "constituency bureau, published by AEP in machine-readable form. Source of the "
                "committed results and totals."
            ),
        ),
        Document(
            BEC_PDF,
            f"{base}/data/shared/sicpv/partial/CNTRY/{category}_BEC/{pv_pdf}",
            "pdf_text",
            title=pv_pdf_title,
            published_date=pv_pdf_date,
            notes=(
                "BEC national PV generated by SICPV (text layer). ingest-results checks every "
                "contestant's votes and the totals fields against it."
            ),
        ),
        Document(
            BEC_REPORT,
            bec_report,
            "pdf_image",
            title=pv_pdf_title,
            published_date=bec_report_date,
            notes=(
                "BEC final report as published on the BEC website (signed scan, no text layer). "
                "Checked manually against the committed totals; see the T-010 Log."
            ),
        ),
        Document(
            STATIONS,
            f"{base}/data/csv/sicpv/pv_part_cntry_{suffix}.csv",
            "csv",
            notes=(
                "Per-polling-station PVs, latest version (stations in Romania and abroad). "
                "Aggregated as a cross-check only; see the T-010 Log."
            ),
        ),
        Document(
            STATIONS_POSTAL,
            f"{base}/data/csv/sicpv/pv_part_cntry_{suffix}_c.csv",
            "csv",
            notes=(
                "Per-bureau PVs of the postal vote, latest version. Aggregated as a cross-check "
                "only; see the T-010 Log."
            ),
        ),
    )


PARLIAMENTARY_PV_FIELDS = PvFields(
    registered_voters="a1",
    voters="b",
    valid_votes="e",
    invalid_votes="f",
    blank_votes="g",
    description=(
        "PV fields: registered_voters = a1 (permanent electoral lists; excludes supplementary "
        "lists, special ballot box extracts, and postal-vote lists), voters = b, "
        "valid_votes = e, invalid_votes = f (null votes)."
    ),
)
PRESIDENTIAL_PV_FIELDS = PvFields(
    registered_voters="a",
    voters="b",
    valid_votes="c",
    invalid_votes="d",
    description=(
        "PV fields: registered_voters = a (permanent electoral lists in Romania, abroad, and for "
        "postal voting), voters = b, valid_votes = c, invalid_votes = d (null votes)."
    ),
)
_PRES_TITLE_R1 = (
    "Proces-verbal privind rezultatul votării la alegerile pentru Președintele României"
)
_PRES_TITLE_R2 = (
    "Proces-verbal privind rezultatul alegerilor pentru Președintele României "
    "în cadrul celui de-al doilea tur de scrutin"
)

SOURCES: dict[str, ElectionSource] = {
    "parl-2024-cd": ElectionSource(
        election_id="parl-2024-cd",
        category="CD",
        pv_fields=PARLIAMENTARY_PV_FIELDS,
        station_fields=StationFields(valid_votes="e"),
        postal_fields=StationFields(valid_votes="d1"),
        documents=_documents(
            site="parlamentare01122024",
            pv_pdf="pv_cd_bec_gnrtd_1733319167.pdf",
            pv_pdf_title=(
                "Proces-verbal privind totalizarea voturilor la nivel național pentru alegerea "
                "Camerei Deputaților"
            ),
            pv_pdf_date="2024-12-04",
            bec_report="https://parlamentare2024.bec.ro/wp-content/uploads/2024/12/RFCD_1.pdf",
            bec_report_date="2024-12-04",
            category="CD",
        ),
    ),
    "pres-2025-r1": ElectionSource(
        election_id="pres-2025-r1",
        category="PRSD",
        pv_fields=PRESIDENTIAL_PV_FIELDS,
        station_fields=StationFields(valid_votes="c"),
        postal_fields=StationFields(valid_votes="d1"),
        documents=_documents(
            site="prezidentiale04052025",
            pv_pdf="pv_prsd_bec_gnrtd_1746537345.pdf",
            pv_pdf_title=_PRES_TITLE_R1,
            pv_pdf_date="2025-05-06",
            bec_report="https://prezidentiale2025.bec.ro/wp-content/uploads/2025/05/RFT1.pdf",
            bec_report_date="2025-05-06",
            category="PRSD",
        ),
    ),
    "pres-2025-r2": ElectionSource(
        election_id="pres-2025-r2",
        category="PRSD",
        pv_fields=PRESIDENTIAL_PV_FIELDS,
        station_fields=StationFields(valid_votes="c"),
        postal_fields=StationFields(valid_votes="d1"),
        documents=_documents(
            site="prezidentiale18052025",
            pv_pdf="pv_prsd_bec_gnrtd_1747754304.pdf",
            pv_pdf_title=_PRES_TITLE_R2,
            pv_pdf_date="2025-05-20",
            bec_report="https://prezidentiale2025.bec.ro/wp-content/uploads/2025/05/RFT1_2.pdf",
            bec_report_date="2025-05-20",
            category="PRSD",
        ),
    ),
}
"""The elections this command can ingest, keyed by ``election_id``."""


# --- Names and entities ------------------------------------------------------------------------

_CEDILLA_TO_COMMA = str.maketrans("şţŞŢ", "șțȘȚ")


def normalize_name(name: str) -> str:
    """Compare key for contestant names: comma-below diacritics, single spaces, upper case.

    "X- Y" becomes "X-Y": the sources disagree on the space after a hyphen (and a PDF line
    wrapped after a hyphen comes out the same way).
    """
    name = re.sub(r"\s+", " ", name.translate(_CEDILLA_TO_COMMA)).strip()
    return re.sub(r"(?<=\S)- (?=\S)", "-", name).upper()


class EntityResolver:
    """Map official contestant names to ``entities.csv`` IDs (by ``name``, type-filtered)."""

    def __init__(self, entities: Iterable[Mapping[str, str]], allowed_types: Sequence[str]):
        self._by_name: dict[str, list[str]] = {}
        for row in entities:
            if row["entity_type"] in allowed_types:
                self._by_name.setdefault(normalize_name(row["name"]), []).append(row["entity_id"])

    def resolve(self, name: str) -> str:
        matches = self._by_name.get(normalize_name(name), [])
        if len(matches) != 1:
            problem = "no entity" if not matches else f"several entities ({', '.join(matches)})"
            raise IngestError(
                f"contestant {name!r}: {problem} in registry/entities.csv with this name; "
                "append the missing entity (append-only) or fix the name"
            )
        return matches[0]


# --- PVs (pv.json) -----------------------------------------------------------------------------


@dataclass
class Pv:
    """One report (procès-verbal): totals fields and votes per contestant (normalized names)."""

    code: str
    report_type: str
    fields: dict[str, int]
    votes: dict[str, int]
    names: dict[str, str] = field(default_factory=dict)
    """Normalized name -> name as published."""


def _int(value: object, what: str) -> int:
    text = str(value).strip()
    if not re.fullmatch(r"\d+", text):
        raise IngestError(f"{what}: not a non-negative integer: {value!r}")
    return int(text)


def _pv(table: Mapping[str, object], code: str) -> Pv:
    report_type = str(table.get("report_type_code") or "")
    fields: dict[str, int] = {}
    for item in table.get("fields") or []:  # type: ignore[union-attr]
        name = str(item["name"])
        value = _int(item["value"], f"PV {code} field {name}")
        if fields.setdefault(name, value) != value:
            raise IngestError(f"PV {code}: field {name} appears twice with different values")
    pv = Pv(code=code, report_type=report_type, fields=fields, votes={})
    for item in table.get("candidates") or []:  # type: ignore[union-attr]
        published = str(item["candidate"])
        key = normalize_name(published)
        if key in pv.votes:
            raise IngestError(f"PV {code}: contestant {published!r} appears twice")
        pv.votes[key] = _int(item["votes"], f"PV {code} votes for {published!r}")
        pv.names[key] = published
    if not pv.votes:
        raise IngestError(f"PV {code}: no contestants")
    return pv


def parse_pv_json(content: bytes, category: str) -> tuple[Pv, list[Pv]]:
    """Return the national PV and the top-level constituency PVs of ``category``."""
    try:
        data = json.loads(content.decode("utf-8-sig"))
        national_table = data["scopes"]["CNTRY"]["categories"][category]["table"]["RO"]
        county_tables = data["scopes"]["CNTY"]["categories"][category]["table"]
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise IngestError(f"pv.json: unexpected structure ({exc!r})") from exc
    national = _pv(national_table, "RO")
    constituencies = [_pv(table, str(table["county_code"])) for table in county_tables.values()]
    codes = Counter(pv.code for pv in constituencies)
    duplicates = sorted(code for code, count in codes.items() if count > 1)
    if duplicates:
        raise IngestError(f"pv.json: several PVs for {', '.join(duplicates)}")
    if MUNICIPALITY_CODE in codes:
        constituencies = [pv for pv in constituencies if pv.code not in SECTOR_CODES]
    constituencies.sort(key=lambda pv: pv.code)
    return national, constituencies


@dataclass
class ScopeValues:
    """Official values of one scope (from the PVs)."""

    votes: dict[str, int]
    totals: dict[str, int | None]
    blank_votes: int | None
    pvs: list[Pv]
    notes: list[str] = field(default_factory=list)


def _field(pv: Pv, letter: str) -> int:
    if letter not in pv.fields:
        raise IngestError(f"PV {pv.code} ({pv.report_type}): field {letter!r} is missing")
    return pv.fields[letter]


def official_scopes(
    national: Pv, constituencies: list[Pv], fields: PvFields
) -> dict[str, ScopeValues]:
    """Build the three scopes from the PVs and check that domestic + diaspora = total."""
    diaspora_pvs = [pv for pv in constituencies if pv.code == DIASPORA_CODE]
    domestic_pvs = [pv for pv in constituencies if pv.code != DIASPORA_CODE]
    if len(diaspora_pvs) != 1 or not domestic_pvs:
        raise IngestError("pv.json: expected one constituency PV abroad (SR) and in-country PVs")
    groups = {"domestic": domestic_pvs, "diaspora": diaspora_pvs, "total": [national]}

    scopes: dict[str, ScopeValues] = {}
    for scope, pvs in groups.items():
        votes: Counter[str] = Counter()
        for pv in pvs:
            votes.update(pv.votes)
        totals: dict[str, int | None] = {
            column: sum(_field(pv, fields.letter(column)) for pv in pvs)
            for column in TOTALS_COLUMNS
        }
        blank = sum(_field(pv, fields.blank_votes) for pv in pvs) if fields.blank_votes else None
        scopes[scope] = ScopeValues(dict(votes), totals, blank, pvs)

    domestic, diaspora, total = scopes["domestic"], scopes["diaspora"], scopes["total"]
    for name in sorted(set(domestic.votes) | set(diaspora.votes) | set(total.votes)):
        parts = domestic.votes.get(name, 0) + diaspora.votes.get(name, 0)
        if name not in total.votes or parts != total.votes[name]:
            raise IngestError(
                f"{name}: domestic + diaspora = {parts}, national PV = {total.votes.get(name)}"
            )
    for scope, values in scopes.items():
        if sum(values.votes.values()) != values.totals["valid_votes"]:
            raise IngestError(
                f"{scope}: contestant votes sum to {sum(values.votes.values())}, "
                f"valid votes = {values.totals['valid_votes']}"
            )
    for column in TOTALS_COLUMNS:
        dom, dia, tot = (scopes[s].totals[column] for s in SCOPES)
        assert dom is not None and dia is not None and tot is not None
        if dom + dia == tot:
            continue
        if column == "valid_votes":
            raise IngestError(f"valid votes: domestic {dom} + diaspora {dia} != national {tot}")
        diaspora.totals[column] = None
        diaspora.notes.append(
            f"{column} left empty: domestic {dom} + this PV {dia} = {dom + dia} differs from "
            f"the BEC national PV ({tot}) by {tot - dom - dia}."
        )
    return scopes


# --- BEC national PV (PDF text layer) ----------------------------------------------------------

_VOTE_LINE = re.compile(r"^\d+ (?P<name>\D.*?) (?P<votes>\d+)(?: \d+(?:[.,]\d+)? ?%)?$")
_NUMBER_AT_END = re.compile(r"(?:^|\s)(\d+)$")


def parse_bec_text(text: str) -> tuple[dict[str, set[int]], list[str]]:
    """Votes per contestant (normalized name -> values seen) and the text lines of a BEC PV."""
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    votes: dict[str, set[int]] = {}
    for index, line in enumerate(lines):
        if not re.match(r"^\d+ \D", line):
            continue
        candidate = line
        for extra in lines[index + 1 : index + 3]:
            if _VOTE_LINE.match(candidate):
                break
            candidate = f"{candidate}{'' if candidate.endswith('-') else ' '}{extra}"
        match = _VOTE_LINE.match(candidate)
        # Contestant names are printed in upper case; this skips dates such as "04 mai 2025".
        if match and match["name"] == match["name"].upper():
            name = normalize_name(match["name"])
            votes.setdefault(name, set()).add(int(match["votes"]))
    return votes, lines


def bec_field(lines: Sequence[str], letter: str) -> int | None:
    """The value of the PV field ``letter`` (a line starting with it; the number ends a line)."""
    for index, line in enumerate(lines):
        if re.match(rf"^{re.escape(letter)}(\s|$)", line):
            for following in lines[index : index + 6]:
                match = _NUMBER_AT_END.search(following)
                if match:
                    return int(match.group(1))
            return None
    return None


def check_bec(national: Pv, text: str, fields: PvFields) -> tuple[list[str], int, int]:
    """Compare the national PV with the BEC PV text. Return (mismatches, votes, fields checked)."""
    bec_votes, lines = parse_bec_text(text)
    mismatches = []
    for name, votes in national.votes.items():
        seen = bec_votes.get(name)
        if seen != {votes}:
            mismatches.append(
                f"{national.names[name]}: pv.json {votes}, BEC PV {sorted(seen or [])}"
            )
    mismatches.extend(
        f"{name}: in the BEC PV ({sorted(values)}), not in pv.json"
        for name, values in bec_votes.items()
        if name not in national.votes
    )
    letters = [fields.letter(column) for column in TOTALS_COLUMNS]
    if fields.blank_votes:
        letters.append(fields.blank_votes)
    for letter in letters:
        value = bec_field(lines, letter)
        if value != national.fields.get(letter):
            mismatches.append(
                f"field {letter}: pv.json {national.fields.get(letter)}, BEC PV {value}"
            )
    return mismatches, len(national.votes), len(letters)


def extract_pdf_text(content: bytes) -> str:
    """Text layer of a PDF (all pages)."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


# --- Station PVs (cross-check) -----------------------------------------------------------------


@dataclass
class StationTotals:
    votes: Counter[str] = field(default_factory=Counter)
    valid_votes: int = 0
    voters: int = 0
    rows: int = 0


def _station_name(column: str) -> str:
    name = column.removesuffix(VOTES_SUFFIX)
    return normalize_name(name.removesuffix(INDEPENDENT_SUFFIX))


def _read_station_rows(content: bytes, what: str) -> list[dict[str, str]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IngestError(f"{what}: not UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = list(reader)
    if not rows or not reader.fieldnames:
        raise IngestError(f"{what}: no rows")
    return rows


def _station_value(row: Mapping[str, str], column: str, what: str) -> int:
    if column not in row:
        raise IngestError(f"{what}: column {column!r} is missing")
    value = (row[column] or "").strip()
    return _int(value, f"{what} column {column}") if value else 0


def aggregate_stations(
    stations: bytes,
    postal: bytes,
    station_fields: StationFields,
    postal_fields: StationFields,
) -> dict[str, StationTotals]:
    """Sum the station PVs per scope: abroad stations and postal votes are ``diaspora``."""
    scopes = {scope: StationTotals() for scope in SCOPES}
    for content, fields, what, all_abroad in (
        (stations, station_fields, "station CSV", False),
        (postal, postal_fields, "postal-vote CSV", True),
    ):
        for row in _read_station_rows(content, what):
            abroad = all_abroad or row.get("precinct_county_nce") == DIASPORA_PRECINCT_COUNTY
            for scope in ("diaspora" if abroad else "domestic", "total"):
                target = scopes[scope]
                target.rows += 1
                target.valid_votes += _station_value(row, fields.valid_votes, what)
                target.voters += _station_value(row, fields.voters, what)
                for column in row:
                    if column.endswith(VOTES_SUFFIX):
                        target.votes[_station_name(column)] += _station_value(row, column, what)
    return scopes


@dataclass(frozen=True)
class Difference:
    scope: str
    item: str
    official: int
    stations: int

    @property
    def delta(self) -> int:
        return self.stations - self.official


def compare_stations(
    official: Mapping[str, ScopeValues],
    stations: Mapping[str, StationTotals],
    labels: Mapping[str, str],
) -> list[Difference]:
    """Differences between the station aggregation and the official PVs (stations - official)."""
    differences = []
    for scope in SCOPES:
        values, aggregate = official[scope], stations[scope]
        pairs = [
            ("valid_votes", values.totals["valid_votes"] or 0, aggregate.valid_votes),
            ("voters", values.totals["voters"] or 0, aggregate.voters),
        ]
        for name in sorted(set(values.votes) | set(aggregate.votes)):
            pairs.append((labels.get(name, name), values.votes.get(name, 0), aggregate.votes[name]))
        differences.extend(
            Difference(scope, item, official_value, station_value)
            for item, official_value, station_value in pairs
            if official_value != station_value
        )
    return differences


# --- Downloads and archive manifest ------------------------------------------------------------

type Fetcher = Callable[[str], bytes]
type PdfTextExtractor = Callable[[bytes], str]


def http_get(url: str) -> bytes:
    """Download ``url``; a redirect means the file does not exist on prezenta.roaep.ro."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=300) as response:
        if response.geturl() != url:
            raise IngestError(f"{url}: redirected to {response.geturl()} (file not available)")
        return response.read()


@dataclass(frozen=True)
class ArchivedDocument:
    document: Document
    document_id: str
    content: bytes
    sha256: str
    raw_path: str
    retrieved_at: str
    downloaded: bool
    status: str
    """``unchanged`` (same hash as the committed manifest), ``changed``, or ``new``."""


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def acquire(
    source: ElectionSource,
    data_dir: Path,
    fetch: Fetcher,
    *,
    refresh: bool,
    today: dt.date,
) -> list[ArchivedDocument]:
    """Download (or reuse) every source file and decide its ``retrieved_at``."""
    election_dir = data_dir / "elections" / source.election_id
    previous = {
        row["source_url"]: row for row in _read_csv(election_dir / ARCHIVE_MANIFEST.filename)
    }
    raw_dir = data_dir / "raw" / "elections" / source.election_id
    archived = []
    for number, document in enumerate(source.documents, start=1):
        raw = raw_dir / document.filename
        downloaded = refresh or not raw.is_file()
        if downloaded:
            content = fetch(document.url)
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_bytes(content)
        else:
            content = raw.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        known = previous.get(document.url)
        unchanged = known is not None and known.get("sha256") == digest
        status = "unchanged" if unchanged else "new" if known is None else "changed"
        archived.append(
            ArchivedDocument(
                document=document,
                document_id=f"{source.election_id}-doc-{number:03d}",
                content=content,
                sha256=digest,
                raw_path=f"{RAW_PREFIX}/{source.election_id}/{document.filename}",
                retrieved_at=known["retrieved_at"] if unchanged and known else today.isoformat(),
                downloaded=downloaded,
                status=status,
            )
        )
    return archived


# --- Output ------------------------------------------------------------------------------------


def _csv_bytes(header: Sequence[str], rows: Iterable[Sequence[object]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow(["" if value is None else value for value in row])
    return buffer.getvalue().encode("utf-8")


def _scope_origin(scope: str, values: ScopeValues, pv_doc: str, bec_doc: str) -> str:
    if scope == "domestic":
        types = ", ".join(sorted({pv.report_type for pv in values.pvs}))
        return f"Sum of the {len(values.pvs)} in-country constituency PVs ({types}) in {pv_doc}."
    if scope == "diaspora":
        pv = values.pvs[0]
        return (
            f"Constituency PV {pv.code} ({pv.report_type}) in {pv_doc}: polling stations abroad "
            "and postal votes. registered_voters is this PV's permanent-list figure; most voters "
            "abroad vote on supplementary lists, so it is not a turnout base."
        )
    return (
        f"BEC national PV ({values.pvs[0].report_type}) in {pv_doc}; matches the BEC PV text "
        f"in {bec_doc}."
    )


_RESULT_NOTES = {
    "domestic": "Sum of the in-country constituency PVs.",
    "diaspora": "PV of the constituency abroad (incl. postal votes).",
    "total": "BEC national PV.",
}


def build_files(
    source: ElectionSource,
    scopes: Mapping[str, ScopeValues],
    entity_ids: Mapping[str, str],
    documents: Mapping[str, ArchivedDocument],
) -> dict[str, bytes]:
    """The three committed files, as bytes, keyed by file name."""
    pv_json = documents[PV_JSON]
    provenance = (pv_json.document.url, "official", pv_json.retrieved_at, "true")
    results = []
    totals = []
    for scope in SCOPES:
        values = scopes[scope]
        # Every contestant gets a row in every scope, with an explicit 0 (R-50).
        scope_votes = {name: values.votes.get(name, 0) for name in scopes["total"].votes}
        ranked = sorted(scope_votes.items(), key=lambda item: (-item[1], entity_ids[item[0]]))
        results.extend(
            [source.election_id, scope, entity_ids[name], votes, *provenance, _RESULT_NOTES[scope]]
            for name, votes in ranked
        )
        notes = [
            _scope_origin(scope, values, pv_json.document_id, documents[BEC_PDF].document_id),
            source.pv_fields.description,
        ]
        if values.blank_votes is not None:
            notes.append(
                f"Blank votes (field {source.pv_fields.blank_votes}): {values.blank_votes}."
            )
        notes.extend(values.notes)
        totals.append(
            [
                source.election_id,
                scope,
                *(values.totals[column] for column in TOTALS_COLUMNS),
                *provenance,
                " ".join(notes),
            ]
        )
    manifest = [
        [
            item.document_id,
            item.document.title,
            item.document.published_date,
            item.document.format,
            "",
            item.sha256,
            item.raw_path,
            item.document.url,
            "official",
            item.retrieved_at,
            item.document.notes,
        ]
        for item in documents.values()
    ]
    return {
        RESULTS.filename: _csv_bytes(RESULTS.header, results),
        RESULTS_TOTALS.filename: _csv_bytes(RESULTS_TOTALS.header, totals),
        ARCHIVE_MANIFEST.filename: _csv_bytes(ARCHIVE_MANIFEST.header, manifest),
    }


# --- Pipeline ----------------------------------------------------------------------------------


@dataclass
class IngestReport:
    election_id: str
    documents: list[ArchivedDocument]
    bec_votes_checked: int
    bec_fields_checked: int
    scopes: dict[str, ScopeValues]
    station_differences: list[Difference]
    station_rows: dict[str, int]
    written: list[Path]
    unchanged: list[Path]


def _election_type(data_dir: Path, election_id: str) -> str:
    for row in _read_csv(data_dir / "registry" / "elections.csv"):
        if row["election_id"] == election_id:
            return row["election_type"]
    raise IngestError(f"{election_id}: not in registry/elections.csv")


def ingest(
    election_id: str,
    data_dir: Path = Path("data"),
    *,
    sources: Mapping[str, ElectionSource] = SOURCES,
    fetch: Fetcher = http_get,
    pdf_text: PdfTextExtractor = extract_pdf_text,
    refresh: bool = False,
    today: dt.date | None = None,
) -> IngestReport:
    """Run the whole pipeline for one election and write its three files."""
    if election_id not in sources:
        raise IngestError(f"{election_id}: no source configured (known: {', '.join(sources)})")
    source = sources[election_id]
    election_type = _election_type(data_dir, election_id)
    resolver = EntityResolver(
        _read_csv(data_dir / "registry" / "entities.csv"), CONTESTANT_TYPES[election_type]
    )
    archived = acquire(source, data_dir, fetch, refresh=refresh, today=today or dt.date.today())
    documents = {item.document.key: item for item in archived}

    national, constituencies = parse_pv_json(documents[PV_JSON].content, source.category)
    scopes = official_scopes(national, constituencies, source.pv_fields)
    labels = {**{k: v for pv in constituencies for k, v in pv.names.items()}, **national.names}
    entity_ids = {name: resolver.resolve(labels[name]) for name in national.votes}
    reused = [eid for eid, count in Counter(entity_ids.values()).items() if count > 1]
    if reused:
        raise IngestError(f"several contestants resolve to {', '.join(sorted(reused))}")

    mismatches, votes_checked, fields_checked = check_bec(
        national, pdf_text(documents[BEC_PDF].content), source.pv_fields
    )
    if mismatches:
        raise IngestError("pv.json differs from the BEC national PV: " + "; ".join(mismatches))

    stations = aggregate_stations(
        documents[STATIONS].content,
        documents[STATIONS_POSTAL].content,
        source.station_fields,
        source.postal_fields,
    )
    entity_labels = {name: entity_ids.get(name, labels.get(name, name)) for name in labels}
    differences = compare_stations(scopes, stations, entity_labels)

    files = build_files(source, scopes, entity_ids, documents)
    election_dir = data_dir / "elections" / election_id
    election_dir.mkdir(parents=True, exist_ok=True)
    written, unchanged = [], []
    for filename, content in files.items():
        path = election_dir / filename
        if path.is_file() and path.read_bytes() == content:
            unchanged.append(path)
            continue
        path.write_bytes(content)
        written.append(path)
    return IngestReport(
        election_id=election_id,
        documents=archived,
        bec_votes_checked=votes_checked,
        bec_fields_checked=fields_checked,
        scopes=scopes,
        station_differences=differences,
        station_rows={scope: stations[scope].rows for scope in SCOPES},
        written=written,
        unchanged=unchanged,
    )


# --- CLI ---------------------------------------------------------------------------------------


def register(subparsers: "Subparsers") -> None:
    parser = subparsers.add_parser(
        "ingest-results",
        help="Download the official results of an election and write its results files.",
        description=(
            "Download the official results (AEP/BEC) of one election to data/raw/, check them "
            "against the BEC national report, cross-check them with the polling-station data, "
            "and write results.csv, results_totals.csv, and archive_manifest.csv under "
            "data/elections/<election_id>/. Cached raw files are reused unless --refresh."
        ),
    )
    parser.add_argument("election_id", choices=sorted(SOURCES), help="election to ingest")
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data"), help="data directory (default: data)"
    )
    parser.add_argument(
        "--refresh", action="store_true", help="download again even if data/raw/ has the files"
    )
    parser.set_defaults(handler=run)


def format_report(report: IngestReport) -> str:
    out = [f"{report.election_id}:"]
    for item in report.documents:
        state = "downloaded" if item.downloaded else "cached"
        change = {
            "unchanged": "same SHA-256 as the committed manifest",
            "changed": "SHA-256 CHANGED since the committed manifest",
            "new": "not in the committed manifest yet",
        }[item.status]
        out.append(
            f"  {item.document_id} {item.document.filename} sha256={item.sha256[:12]}... "
            f"({state}; {change}; retrieved_at {item.retrieved_at})"
        )
    out.append(
        f"  BEC national PV check: {report.bec_votes_checked} contestants and "
        f"{report.bec_fields_checked} totals fields match"
    )
    for scope in SCOPES:
        values = report.scopes[scope]
        totals = ", ".join(f"{column}={values.totals[column]}" for column in TOTALS_COLUMNS)
        out.append(f"  {scope}: {len(values.votes)} contestants, {totals}")
    rows = ", ".join(f"{scope} {count}" for scope, count in report.station_rows.items())
    out.append(
        f"  Station cross-check ({rows} PV rows): {len(report.station_differences)} differences"
    )
    for difference in report.station_differences:
        out.append(
            f"    {difference.scope} {difference.item}: official {difference.official}, "
            f"stations {difference.stations} ({difference.delta:+d})"
        )
    for path in report.written:
        out.append(f"  wrote {path.as_posix()}")
    for path in report.unchanged:
        out.append(f"  unchanged {path.as_posix()}")
    return "\n".join(out) + "\n"


def run(args: argparse.Namespace) -> int:
    out = sys.stdout
    if isinstance(out, io.TextIOWrapper):
        out.reconfigure(errors="backslashreplace")
    try:
        report = ingest(args.election_id, args.data_dir, refresh=args.refresh)
    except (IngestError, OSError) as exc:
        sys.stderr.write(f"ingest-results: error: {exc}\n")
        return 1
    out.write(format_report(report))
    return 0
