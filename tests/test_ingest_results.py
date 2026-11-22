"""Tests for ``sondaje ingest-results`` (T-010), on small fictitious fixtures, offline."""

import csv
import datetime as dt
import io
import json
from pathlib import Path

import pytest

from conftest import FIXTURES, DataDir, DataDirFactory
from sondaje.cli import build_parser, main
from sondaje.ingest import results as ingest_results
from sondaje.ingest.results import (
    BEC_PDF,
    BEC_REPORT,
    PARLIAMENTARY_PV_FIELDS,
    PV_JSON,
    SOURCES,
    STATIONS,
    STATIONS_POSTAL,
    Difference,
    Document,
    ElectionSource,
    EntityResolver,
    IngestError,
    StationFields,
    aggregate_stations,
    bec_field,
    check_bec,
    compare_stations,
    ingest,
    normalize_name,
    official_scopes,
    parse_bec_text,
    parse_pv_json,
)
from sondaje.validation.model import Severity

INGEST = FIXTURES / "ingest" / "parl-2099-cd"
ELECTION = "parl-2099-cd"
TODAY = dt.date(2099, 6, 20)
BASE = "https://example.org/aep/parl-2099"

SOURCE = ElectionSource(
    election_id=ELECTION,
    category="CD",
    pv_fields=PARLIAMENTARY_PV_FIELDS,
    station_fields=StationFields(valid_votes="e"),
    postal_fields=StationFields(valid_votes="d1"),
    documents=(
        Document(PV_JSON, f"{BASE}/pv.json", "json"),
        Document(BEC_PDF, f"{BASE}/bec_pv.txt", "pdf_text", title="Proces-verbal BEC"),
        Document(BEC_REPORT, f"{BASE}/bec_scan.pdf", "pdf_image"),
        Document(STATIONS, f"{BASE}/pv_part_cntry_cd.csv", "csv"),
        Document(STATIONS_POSTAL, f"{BASE}/pv_part_cntry_cd_c.csv", "csv"),
    ),
)
SOURCES_UNDER_TEST = {ELECTION: SOURCE}
SCAN = b"%PDF-1.4 fictitious scan"


class FakeWeb:
    """Serves the fixture files by URL and counts the downloads."""

    def __init__(self) -> None:
        self.files = {document.url: _fixture_bytes(document) for document in SOURCE.documents}
        self.calls: list[str] = []

    def __call__(self, url: str) -> bytes:
        self.calls.append(url)
        return self.files[url]


def _fixture_bytes(document: Document) -> bytes:
    if document.key == BEC_REPORT:
        return SCAN
    return (INGEST / document.filename).read_bytes()


def _text(content: bytes) -> str:
    """Stand-in for the PDF text extractor: the fixture 'PDF' is its text layer."""
    if content == SCAN:
        raise AssertionError("the scanned report is not read by the pipeline")
    return content.decode("utf-8")


def run_ingest(data: DataDir, web: FakeWeb, *, today: dt.date = TODAY, refresh: bool = False):
    return ingest(
        ELECTION,
        data.root,
        sources=SOURCES_UNDER_TEST,
        fetch=web,
        pdf_text=_text,
        refresh=refresh,
        today=today,
    )


def rows(data: DataDir, filename: str) -> list[dict[str, str]]:
    text = data.read_bytes(f"elections/{ELECTION}/{filename}").decode("utf-8")
    return list(csv.DictReader(io.StringIO(text, newline="")))


def election_files(data: DataDir) -> dict[str, bytes]:
    names = ("results.csv", "results_totals.csv", "archive_manifest.csv")
    return {name: data.read_bytes(f"elections/{ELECTION}/{name}") for name in names}


# --- Names -------------------------------------------------------------------------------------


def test_normalize_name_unifies_diacritics_case_and_hyphen_spacing() -> None:
    assert normalize_name("Alianţa  Gama ") == normalize_name("ALIANȚA GAMA")
    assert (
        normalize_name("Uniunea Bulgară din Banat- România") == "UNIUNEA BULGARĂ DIN BANAT-ROMÂNIA"
    )
    assert normalize_name("PARTIDUL X - Y") == "PARTIDUL X - Y"


def test_resolver_filters_by_entity_type() -> None:
    entities = [
        {"entity_id": "ion-exemplu", "entity_type": "independent", "name": "Ion Exemplu"},
        {"entity_id": "ion-exemplu-2099", "entity_type": "candidate", "name": "Ion Exemplu"},
    ]
    assert EntityResolver(entities, ("candidate",)).resolve("ION EXEMPLU") == "ion-exemplu-2099"
    assert EntityResolver(entities, ("party", "independent")).resolve("ION EXEMPLU") == (
        "ion-exemplu"
    )
    with pytest.raises(IngestError, match="several entities"):
        EntityResolver(entities, ("candidate", "independent")).resolve("Ion Exemplu")
    with pytest.raises(IngestError, match="no entity"):
        EntityResolver(entities, ("party",)).resolve("Ion Exemplu")


# --- PVs ---------------------------------------------------------------------------------------


def test_parse_pv_json_drops_bucharest_sectors_when_a_bucharest_pv_exists() -> None:
    national, constituencies = parse_pv_json((INGEST / "pv.json").read_bytes(), "CD")
    assert [pv.code for pv in constituencies] == ["AB", "B", "SR"]
    assert national.fields == {"a1": 8010, "b": 4180, "e": 4075, "f": 91, "g": 17}
    assert national.votes[normalize_name("Alianța Gama")] == 1005


def _pv_table(code: str, votes: int) -> dict[str, object]:
    return {
        "county_code": code,
        "report_type_code": "PRSD_BES" if code.startswith("S") else "PRSD_BEJ",
        "fields": [{"name": "c", "value": str(votes)}],
        "candidates": [{"candidate": "ION EXEMPLU", "votes": votes}],
    }


def test_parse_pv_json_keeps_sectors_without_a_bucharest_pv() -> None:
    data = {
        "scopes": {
            "CNTY": {
                "categories": {
                    "PRSD": {"table": {"1": _pv_table("S1", 5), "2": _pv_table("SR", 2)}}
                }
            },
            "CNTRY": {"categories": {"PRSD": {"table": {"RO": _pv_table("RO", 7)}}}},
        }
    }
    _, constituencies = parse_pv_json(json.dumps(data).encode(), "PRSD")
    assert [pv.code for pv in constituencies] == ["S1", "SR"]


def test_parse_pv_json_rejects_conflicting_duplicate_fields() -> None:
    data = json.loads((INGEST / "pv.json").read_text(encoding="utf-8"))
    data["scopes"]["CNTRY"]["categories"]["CD"]["table"]["RO"]["fields"][-1]["value"] = "4076"
    with pytest.raises(IngestError, match="field e appears twice"):
        parse_pv_json(json.dumps(data).encode(), "CD")


def test_official_scopes_split_and_unmatched_invalid_votes() -> None:
    national, constituencies = parse_pv_json((INGEST / "pv.json").read_bytes(), "CD")
    scopes = official_scopes(national, constituencies, PARLIAMENTARY_PV_FIELDS)
    alfa = normalize_name("Partidul Alfa")
    assert {scope: values.votes.get(alfa) for scope, values in scopes.items()} == {
        "domestic": 1600,
        "diaspora": 100,
        "total": 1700,
    }
    assert scopes["domestic"].totals == {
        "registered_voters": 8000,
        "voters": 3715,
        "valid_votes": 3620,
        "invalid_votes": 80,
    }
    assert scopes["diaspora"].totals["invalid_votes"] is None
    assert "differs from the BEC national PV (91) by 3" in scopes["diaspora"].notes[0]
    assert scopes["total"].totals["invalid_votes"] == 91
    assert [scopes[s].blank_votes for s in ("domestic", "diaspora", "total")] == [15, 2, 17]


def test_official_scopes_stop_when_domestic_plus_diaspora_differs_from_national() -> None:
    data = json.loads((INGEST / "pv.json").read_text(encoding="utf-8"))
    data["scopes"]["CNTY"]["categories"]["CD"]["table"]["43"]["candidates"][0]["votes"] = "101"
    national, constituencies = parse_pv_json(json.dumps(data).encode(), "CD")
    with pytest.raises(IngestError, match="PARTIDUL ALFA: domestic \\+ diaspora = 1701"):
        official_scopes(national, constituencies, PARLIAMENTARY_PV_FIELDS)


# --- BEC national PV text ----------------------------------------------------------------------


def test_parse_bec_text_reads_wrapped_names_and_skips_dates() -> None:
    votes, lines = parse_bec_text((INGEST / "bec_pv.txt").read_text(encoding="utf-8"))
    assert votes == {
        "PARTIDUL ALFA": {1700},
        "PARTIDUL BETA": {1350},
        "ALIANȚA GAMA": {1005},
        "PARTIDUL OMEGA": {20},
    }
    assert bec_field(lines, "a") == 9000
    assert bec_field(lines, "a1") == 8010
    assert bec_field(lines, "b") == 4180
    assert bec_field(lines, "f") == 91
    assert bec_field(lines, "z") is None


def test_check_bec_reports_every_difference() -> None:
    national, _ = parse_pv_json((INGEST / "pv.json").read_bytes(), "CD")
    text = (INGEST / "bec_pv.txt").read_text(encoding="utf-8")
    assert check_bec(national, text, PARLIAMENTARY_PV_FIELDS) == ([], 4, 5)
    changed = text.replace("PARTIDUL BETA 1350", "PARTIDUL BETA 1351").replace(
        "nule3) 91", "nule3) 90"
    )
    mismatches, _, _ = check_bec(national, changed, PARLIAMENTARY_PV_FIELDS)
    assert mismatches == [
        "PARTIDUL BETA: pv.json 1350, BEC PV [1351]",
        "field f: pv.json 91, BEC PV 90",
    ]


# --- Station cross-check -----------------------------------------------------------------------


def test_station_aggregation_and_differences() -> None:
    stations = aggregate_stations(
        (INGEST / "pv_part_cntry_cd.csv").read_bytes(),
        (INGEST / "pv_part_cntry_cd_c.csv").read_bytes(),
        StationFields(valid_votes="e"),
        StationFields(valid_votes="d1"),
    )
    assert {scope: totals.rows for scope, totals in stations.items()} == {
        "domestic": 3,
        "diaspora": 2,
        "total": 5,
    }
    gama = normalize_name("Alianța Gama")
    assert stations["diaspora"].votes[gama] == 205
    assert stations["diaspora"].valid_votes == 455
    assert stations["total"].voters == 4180

    national, constituencies = parse_pv_json((INGEST / "pv.json").read_bytes(), "CD")
    scopes = official_scopes(national, constituencies, PARLIAMENTARY_PV_FIELDS)
    labels = {normalize_name("Partidul Alfa"): "alfa"}
    assert compare_stations(scopes, stations, labels) == [
        Difference("domestic", "valid_votes", 3620, 3619),
        Difference("domestic", "alfa", 1600, 1599),
        Difference("total", "valid_votes", 4075, 4074),
        Difference("total", "alfa", 1700, 1699),
    ]


def test_station_independent_suffix_is_stripped() -> None:
    header = "precinct_county_nce,b,e,ION EXEMPLU-CANDIDAT INDEPENDENT-voturi\n"
    stations = header.encode() + b"1,10,9,9\n"
    postal = b"precinct_county_nce,b,d1\n43,0,0\n"
    totals = aggregate_stations(
        stations, postal, StationFields(valid_votes="e"), StationFields(valid_votes="d1")
    )
    assert totals["domestic"].votes == {"ION EXEMPLU": 9}


# --- End to end --------------------------------------------------------------------------------


def test_ingest_writes_files_that_pass_validation(fixture_copy: DataDirFactory) -> None:
    data = fixture_copy("example")
    web = FakeWeb()
    report = run_ingest(data, web)

    assert sorted(web.calls) == sorted(document.url for document in SOURCE.documents)
    assert len(report.station_differences) == 4
    errors = [issue for issue in data.issues() if issue.severity is Severity.ERROR]
    assert errors == []

    results = rows(data, "results.csv")
    votes = {(row["scope"], row["entity_id"]): int(row["votes"]) for row in results}
    for entity in ("alfa", "beta", "gama", "omega"):
        assert votes["domestic", entity] + votes["diaspora", entity] == votes["total", entity]
    assert votes["diaspora", "omega"] == 0
    assert [(row["scope"], row["entity_id"]) for row in results[:4]] == [
        ("domestic", "alfa"),
        ("domestic", "beta"),
        ("domestic", "gama"),
        ("domestic", "omega"),
    ]
    assert {row["source_url"] for row in results} == {f"{BASE}/pv.json"}
    assert {row["retrieved_at"] for row in results} == {"2099-06-20"}

    totals = {row["scope"]: row for row in rows(data, "results_totals.csv")}
    assert totals["total"]["valid_votes"] == "4075"
    assert totals["diaspora"]["invalid_votes"] == ""
    assert "Blank votes (field g): 2." in totals["diaspora"]["notes"]

    manifest = rows(data, "archive_manifest.csv")
    assert [row["document_id"] for row in manifest] == [
        f"{ELECTION}-doc-{number:03d}" for number in range(1, 6)
    ]
    assert manifest[0]["raw_path"] == f"data/raw/elections/{ELECTION}/pv.json"
    raw = data.root / "raw" / "elections" / ELECTION / "pv.json"
    assert raw.read_bytes() == (INGEST / "pv.json").read_bytes()


def test_rerun_reproduces_the_files_exactly(fixture_copy: DataDirFactory) -> None:
    data = fixture_copy("example")
    run_ingest(data, FakeWeb())
    first = election_files(data)

    # Cached raw files, a later day: nothing is downloaded and nothing changes.
    cached = FakeWeb()
    report = run_ingest(data, cached, today=TODAY + dt.timedelta(days=30))
    assert cached.calls == []
    assert election_files(data) == first
    assert report.written == []
    assert {item.status for item in report.documents} == {"unchanged"}

    # Fresh download of identical bytes: retrieved_at stays the committed one.
    report = run_ingest(data, FakeWeb(), today=TODAY + dt.timedelta(days=60), refresh=True)
    assert election_files(data) == first
    assert all(item.downloaded for item in report.documents)


def test_changed_source_gets_a_new_retrieved_at(fixture_copy: DataDirFactory) -> None:
    data = fixture_copy("example")
    run_ingest(data, FakeWeb())
    web = FakeWeb()
    web.files[f"{BASE}/bec_scan.pdf"] = SCAN + b" (re-scanned)"
    later = TODAY + dt.timedelta(days=1)
    report = run_ingest(data, web, today=later, refresh=True)
    statuses = {item.document.key: item.status for item in report.documents}
    assert statuses[BEC_REPORT] == "changed"
    assert statuses[PV_JSON] == "unchanged"
    manifest = {
        row["document_id"]: row["retrieved_at"] for row in rows(data, "archive_manifest.csv")
    }
    assert manifest[f"{ELECTION}-doc-003"] == later.isoformat()
    assert manifest[f"{ELECTION}-doc-001"] == TODAY.isoformat()


def test_bec_mismatch_stops_before_writing(fixture_copy: DataDirFactory) -> None:
    data = fixture_copy("example")
    before = election_files(data)
    web = FakeWeb()
    web.files[f"{BASE}/bec_pv.txt"] = web.files[f"{BASE}/bec_pv.txt"].replace(b"1700", b"1701")
    with pytest.raises(IngestError, match="differs from the BEC national PV"):
        run_ingest(data, web)
    assert election_files(data) == before


def test_unknown_contestant_stops(fixture_copy: DataDirFactory) -> None:
    data = fixture_copy("example")
    data.replace_value("registry/entities.csv", "name", "Partidul Omega", "Partidul Omicron")
    with pytest.raises(IngestError, match="'PARTIDUL OMEGA': no entity"):
        run_ingest(data, FakeWeb())


# --- Configuration and CLI ---------------------------------------------------------------------


def test_sources_cover_the_mvp_elections() -> None:
    assert set(SOURCES) == {"parl-2024-cd", "pres-2025-r1", "pres-2025-r2"}
    for election_id, source in SOURCES.items():
        assert source.election_id == election_id
        assert [document.key for document in source.documents] == [
            PV_JSON,
            BEC_PDF,
            BEC_REPORT,
            STATIONS,
            STATIONS_POSTAL,
        ]
        assert all(document.url.startswith("https://") for document in source.documents)


def test_cli_registers_ingest_results() -> None:
    args = build_parser().parse_args(["ingest-results", "pres-2025-r1", "--data-dir", "x"])
    assert args.handler is ingest_results.run
    assert args.data_dir == Path("x")
    assert args.refresh is False


def test_cli_reports_errors_with_exit_code_1(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    def failing_ingest(*args: object, **kwargs: object) -> None:
        raise IngestError("boom")

    monkeypatch.setattr(ingest_results, "ingest", failing_ingest)
    assert main(["ingest-results", "pres-2025-r1", "--data-dir", str(tmp_path)]) == 1
    assert "ingest-results: error: boom" in capsys.readouterr().err
