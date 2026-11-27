"""``sondaje archive``: download, hash, snapshot, manifest and inventory (no network)."""

import datetime as dt
import gzip
import hashlib
import io
import urllib.error
from email.message import Message
from pathlib import Path

import pytest

from sondaje.cli import main
from sondaje.ingest import archive as archive_module
from sondaje.ingest.archive import (
    SAVE_ENDPOINT,
    ArchiveError,
    ArchiveRequest,
    Response,
    archive,
    detect_format,
    direct_download_url,
    format_result,
    snapshot_url,
)
from sondaje.ingest.csvio import read_rows, write_rows
from sondaje.schema import ARCHIVE_MANIFEST, INVENTORY

URL = "https://example.org/exemplar/raport.pdf"
TODAY = dt.date(2099, 6, 1)
PAGE = b"<!DOCTYPE html><html><body><p>Partidul Alfa 30%</p></body></html>"
SNAPSHOT = f"https://web.archive.org/web/20990601120000/{URL}"
SAVE = f"https://web.archive.org/save/{URL}"
RAW_SNAPSHOT = f"https://web.archive.org/web/20990601120000id_/{URL}"
LOOKUP = (
    "https://archive.org/wayback/available?url=https%3A%2F%2Fexample.org%2Fexemplar%2Fraport.pdf"
)


class FakeWeb:
    """Answers requests from a URL → response (or exception) table and records them.

    A list is a sequence of answers, one per request (the last one repeats)."""

    def __init__(self, routes: dict[str, Response | Exception | list[Response | Exception]]):
        self.routes = routes
        self.calls: list[str] = []

    def __call__(self, url: str, timeout: float) -> Response:
        self.calls.append(url)
        answer = self.routes.get(url, OSError(f"no route for {url}"))
        if isinstance(answer, list):
            answer = answer.pop(0) if len(answer) > 1 else answer[0]
        if isinstance(answer, Exception):
            raise answer
        return answer


def inventory_row(url: str = URL, status: str = "found") -> dict[str, str]:
    return {
        "publication_url": url,
        "election_id": "parl-2099-cd",
        "title": "",
        "published_date": "",
        "fieldwork_start": "",
        "fieldwork_end": "",
        "found_via": "pollster_site",
        "discovery_url": "",
        "status": status,
        "exclusion_reason": "",
        "document_id": "",
        "poll_id": "",
        "source_url": url,
        "source_type": "pollster",
        "retrieved_at": "2099-05-30",
        "verified": "false",
        "notes": "",
    }


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "data" / "polls" / "exemplar"
    write_rows(directory / ARCHIVE_MANIFEST.filename, ARCHIVE_MANIFEST, [])
    write_rows(directory / INVENTORY.filename, INVENTORY, [inventory_row()])
    return tmp_path / "data"


def request(data_dir: Path, **changes: object) -> ArchiveRequest:
    values: dict[str, object] = {
        "url": URL,
        "pollster_id": "exemplar",
        "data_dir": data_dir,
        "source_type": "pollster",
        "title": "Barometru, mai 2099",
        "retries": 0,
    }
    values.update(changes)
    return ArchiveRequest(**values)  # type: ignore[arg-type]


def manifest(data_dir: Path) -> list[dict[str, str]]:
    return read_rows(data_dir / "polls/exemplar/archive_manifest.csv", ARCHIVE_MANIFEST)


def inventory(data_dir: Path) -> list[dict[str, str]]:
    return read_rows(data_dir / "polls/exemplar/inventory.csv", INVENTORY)


def happy_web() -> FakeWeb:
    return FakeWeb(
        {
            URL: Response(URL, PAGE),
            SAVE: Response(SNAPSHOT, b"<html>Wayback</html>"),
            RAW_SNAPSHOT: Response(RAW_SNAPSHOT, PAGE),
        }
    )


def test_new_document_is_downloaded_hashed_snapshotted_and_recorded(data_dir: Path) -> None:
    web = happy_web()
    result = archive(request(data_dir, notes="Line one.\nLine two."), web, TODAY)
    digest = hashlib.sha256(PAGE).hexdigest()
    assert result.document_id == "exemplar-doc-001"
    assert result.status == "new"
    assert result.archive_url == SNAPSHOT
    assert result.snapshot_check is not None and result.snapshot_check.startswith("identical")
    raw = data_dir / "raw/polls/exemplar/exemplar-doc-001.html"
    assert raw.read_bytes() == PAGE
    assert manifest(data_dir) == [
        {
            "document_id": "exemplar-doc-001",
            "title": "Barometru, mai 2099",
            "published_date": "",
            "format": "html",
            "archive_url": SNAPSHOT,
            "sha256": digest,
            "raw_path": "data/raw/polls/exemplar/exemplar-doc-001.html",
            "source_url": URL,
            "source_type": "pollster",
            "retrieved_at": "2099-06-01",
            "notes": "Line one. Line two.",
        }
    ]
    [row] = inventory(data_dir)
    assert (row["status"], row["document_id"]) == ("archived", "exemplar-doc-001")
    assert web.calls == [URL, SAVE, RAW_SNAPSHOT]
    text = (data_dir / "polls/exemplar/archive_manifest.csv").read_bytes()
    assert b"\r" not in text and text.endswith(b"\n")


def test_failed_save_falls_back_to_an_existing_snapshot(data_dir: Path) -> None:
    older = f"http://web.archive.org/web/20990101000000/{URL}"
    web = FakeWeb(
        {
            URL: Response(URL, PAGE),
            SAVE: OSError("HTTP Error 520"),
            LOOKUP: Response(
                LOOKUP,
                b'{"archived_snapshots": {"closest": {"available": true, "status": "200", '
                b'"url": "' + older.encode() + b'"}}}',
            ),
        }
    )
    result = archive(request(data_dir, check=False), web, TODAY)
    assert result.archive_url == f"https://web.archive.org/web/20990101000000/{URL}"
    assert "Save Page Now failed" in result.attempts[0]
    assert "2099-01-01" in result.snapshot_origin
    assert manifest(data_dir)[0]["archive_url"] == result.archive_url


def test_no_snapshot_means_nothing_is_written(data_dir: Path) -> None:
    web = FakeWeb(
        {
            URL: Response(URL, PAGE),
            SAVE: OSError("timed out"),
            LOOKUP: Response(LOOKUP, b'{"archived_snapshots": {}}'),
        }
    )
    with pytest.raises(ArchiveError, match="no Web Archive snapshot") as exc:
        archive(request(data_dir), web, TODAY)
    assert "timed out" in str(exc.value)
    assert "found no snapshot" in str(exc.value)
    assert manifest(data_dir) == []
    assert inventory(data_dir)[0]["status"] == "found"
    assert (data_dir / "raw/polls/exemplar/exemplar-doc-001.html").is_file()


def test_snapshot_of_another_url_is_not_accepted(data_dir: Path) -> None:
    web = FakeWeb(
        {
            URL: Response(URL, PAGE),
            SAVE: Response("https://web.archive.org/web/20990601120000/https://example.org/", b""),
            LOOKUP: Response(LOOKUP, b'{"archived_snapshots": {}}'),
        }
    )
    with pytest.raises(ArchiveError, match="no snapshot of this URL"):
        archive(request(data_dir), web, TODAY)


def test_supplied_archive_url_skips_save_now(data_dir: Path) -> None:
    supplied = "https://archive.ph/AbCdE"
    web = FakeWeb({URL: Response(URL, PAGE)})
    result = archive(request(data_dir, archive_url=supplied), web, TODAY)
    assert result.archive_url == supplied
    assert result.snapshot_check is None
    assert web.calls == [URL]


def test_snapshot_with_different_bytes_is_reported(data_dir: Path) -> None:
    web = happy_web()
    web.routes[RAW_SNAPSHOT] = Response(RAW_SNAPSHOT, PAGE + b"<!-- ad -->")
    result = archive(request(data_dir), web, TODAY)
    assert result.snapshot_check is not None and result.snapshot_check.startswith("DIFFERENT")


def test_gzip_encoded_snapshot_is_compared_after_decompressing(data_dir: Path) -> None:
    web = happy_web()
    web.routes[RAW_SNAPSHOT] = Response(RAW_SNAPSHOT, gzip.compress(PAGE))
    result = archive(request(data_dir), web, TODAY)
    assert result.snapshot_check is not None
    assert result.snapshot_check.startswith("identical")
    assert "gzip" in result.snapshot_check


@pytest.mark.parametrize(
    "served", [gzip.compress(PAGE + b"<!-- ad -->"), b"\x1f\x8b not really gzip"]
)
def test_gzip_snapshot_with_other_bytes_and_broken_gzip_are_different(
    data_dir: Path, served: bytes
) -> None:
    web = happy_web()
    web.routes[RAW_SNAPSHOT] = Response(RAW_SNAPSHOT, served)
    result = archive(request(data_dir), web, TODAY)
    assert result.snapshot_check is not None
    assert result.snapshot_check.startswith("DIFFERENT")


def http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://x.org", code, f"HTTP {code}", Message(), None)


def test_save_page_now_rate_limit_is_retried_with_backoff(data_dir: Path) -> None:
    web = happy_web()
    web.routes[SAVE] = [http_error(429), OSError("connection refused"), Response(SNAPSHOT, b"")]
    waits: list[float] = []
    result = archive(request(data_dir, retries=2), web, TODAY, sleep=waits.append)
    assert result.archive_url == SNAPSHOT
    assert result.attempts[0].startswith("Save Page Now returned a snapshot")
    assert web.calls == [URL, SAVE, SAVE, SAVE, RAW_SNAPSHOT]
    assert waits == [10.0, 20.0]


def test_retries_are_limited_and_the_check_failure_is_explicit(data_dir: Path) -> None:
    web = happy_web()
    web.routes[RAW_SNAPSHOT] = ConnectionRefusedError("[WinError 10061] refused")
    waits: list[float] = []
    result = archive(request(data_dir, retries=1), web, TODAY, sleep=waits.append)
    assert web.calls.count(RAW_SNAPSHOT) == 2
    assert waits == [10.0]
    assert result.snapshot_check is not None
    assert result.snapshot_check.startswith("NOT CHECKED")
    assert "WinError 10061" in result.snapshot_check
    assert manifest(data_dir)[0]["archive_url"] == SNAPSHOT


@pytest.mark.parametrize("error", [http_error(403), http_error(404), ValueError("bad URL")])
def test_permanent_failures_are_not_retried(data_dir: Path, error: Exception) -> None:
    web = FakeWeb({URL: error})
    with pytest.raises(ArchiveError, match="download failed"):
        archive(request(data_dir, retries=3), web, TODAY, sleep=pytest.fail)
    assert web.calls == [URL]


def test_download_is_retried_after_a_server_error(data_dir: Path) -> None:
    web = happy_web()
    web.routes[URL] = [http_error(503), Response(URL, PAGE)]
    result = archive(request(data_dir, retries=1), web, TODAY, sleep=lambda _: None)
    assert result.status == "new"
    assert web.calls[:2] == [URL, URL]


def test_negative_retries_are_rejected(data_dir: Path) -> None:
    with pytest.raises(ArchiveError, match="--retries"):
        archive(request(data_dir, retries=-1), happy_web(), TODAY)


VIEW = "https://drive.google.com/file/d/1AbC_d-9/view?usp=sharing"
DIRECT = "https://drive.google.com/uc?export=download&id=1AbC_d-9"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


def drive_web(downloaded: bytes) -> FakeWeb:
    snapshot = f"https://web.archive.org/web/20990601120000/{DIRECT}"
    raw = f"https://web.archive.org/web/20990601120000id_/{DIRECT}"
    return FakeWeb(
        {
            DIRECT: Response(DIRECT, downloaded),
            SAVE_ENDPOINT + DIRECT: Response(snapshot, b""),
            raw: Response(raw, downloaded),
        }
    )


def test_google_drive_view_link_is_resolved_to_the_direct_download(data_dir: Path) -> None:
    write_rows(data_dir / "polls/exemplar/inventory.csv", INVENTORY, [inventory_row(VIEW)])
    web = drive_web(PNG)
    result = archive(request(data_dir, url=VIEW), web, TODAY)
    assert result.download_url == DIRECT
    assert web.calls[0] == DIRECT and VIEW not in web.calls
    assert result.archive_url == f"https://web.archive.org/web/20990601120000/{DIRECT}"
    assert result.snapshot_check is not None and result.snapshot_check.startswith("identical")
    [row] = manifest(data_dir)
    assert row["source_url"] == VIEW and row["format"] == "image"
    assert inventory(data_dir)[0]["publication_url"] == VIEW
    assert "resolved to " + DIRECT in format_result(result)


def test_google_drive_viewer_page_is_not_archived_as_the_file(data_dir: Path) -> None:
    write_rows(data_dir / "polls/exemplar/inventory.csv", INVENTORY, [inventory_row(VIEW)])
    web = drive_web(b"<!DOCTYPE html><html><body>Quota exceeded</body></html>")
    with pytest.raises(ArchiveError, match="Google Drive returned a web page"):
        archive(request(data_dir, url=VIEW), web, TODAY)
    assert manifest(data_dir) == []


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://drive.google.com/file/d/1AbC_d-9/view", DIRECT),
        ("https://drive.google.com/file/d/1AbC_d-9", DIRECT),
        ("https://drive.google.com/open?id=1AbC_d-9", DIRECT),
        ("https://drive.google.com/uc?export=download&id=1AbC_d-9", None),
        ("https://drive.google.com/drive/folders/1AbC_d-9", None),
        ("https://example.org/file/d/1AbC_d-9/view", None),
    ],
)
def test_direct_download_url(url: str, expected: str | None) -> None:
    assert direct_download_url(url) == (expected or url)


def test_publication_must_be_in_the_inventory(data_dir: Path) -> None:
    web = happy_web()
    other = "https://example.org/other.pdf"
    with pytest.raises(ArchiveError, match="is not in"):
        archive(request(data_dir, url=other), web, TODAY)
    assert web.calls == []


def test_missing_pollster_directory_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(ArchiveError, match="does not exist"):
        archive(request(tmp_path), happy_web(), TODAY)


def test_download_failure_is_reported(data_dir: Path) -> None:
    web = FakeWeb({URL: OSError("HTTP Error 403: Forbidden")})
    with pytest.raises(ArchiveError, match="--file"):
        archive(request(data_dir), web, TODAY)
    assert manifest(data_dir) == []


def test_rearchiving_unchanged_bytes_keeps_the_row(data_dir: Path) -> None:
    archive(request(data_dir), happy_web(), TODAY)
    web = FakeWeb({URL: Response(URL, PAGE)})
    result = archive(request(data_dir, title=None), web, dt.date(2099, 7, 1))
    assert result.status == "unchanged"
    assert web.calls == [URL]
    [row] = manifest(data_dir)
    assert (row["retrieved_at"], row["title"], row["archive_url"]) == (
        "2099-06-01",
        "Barometru, mai 2099",
        SNAPSHOT,
    )


def test_changed_bytes_update_the_same_document(data_dir: Path) -> None:
    archive(request(data_dir), happy_web(), TODAY)
    web = happy_web()
    new_page = PAGE.replace(b"30%", b"31%")
    web.routes[URL] = Response(URL, new_page)
    web.routes[RAW_SNAPSHOT] = Response(RAW_SNAPSHOT, new_page)
    result = archive(request(data_dir), web, dt.date(2099, 7, 1))
    assert (result.status, result.document_id) == ("updated", "exemplar-doc-001")
    [row] = manifest(data_dir)
    assert row["retrieved_at"] == "2099-07-01"
    assert row["sha256"] == hashlib.sha256(new_page).hexdigest()


def test_second_document_gets_the_next_id_and_local_file_is_used(
    data_dir: Path, tmp_path: Path
) -> None:
    archive(request(data_dir), happy_web(), TODAY)
    second = "https://example.org/stiri/grafic.png"
    rows = inventory(data_dir)
    rows.append(inventory_row(second))
    write_rows(data_dir / "polls/exemplar/inventory.csv", INVENTORY, rows)
    image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
    saved = tmp_path / "grafic.png"
    saved.write_bytes(image)
    web = FakeWeb({})
    result = archive(
        request(data_dir, url=second, file=saved, source_type="media", archive_url=SNAPSHOT),
        web,
        TODAY,
    )
    assert (result.document_id, result.document_format) == ("exemplar-doc-002", "image")
    assert result.raw_path == "data/raw/polls/exemplar/exemplar-doc-002.png"
    assert web.calls == []


def test_invalid_arguments_are_rejected(data_dir: Path) -> None:
    for changes in (
        {"url": "example.org/x"},
        {"pollster_id": "Exemplar"},
        {"published_date": "2099-02-30"},
        {"source_type": "blog"},
        {"document_format": "docx"},
    ):
        with pytest.raises(ArchiveError):
            archive(request(data_dir, **changes), happy_web(), TODAY)


def test_detect_format() -> None:
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    blank = io.BytesIO()
    writer.write(blank)
    assert detect_format(blank.getvalue(), "https://x.org/a.pdf") == "pdf_image"
    assert detect_format(b"\xff\xd8\xff\xe0rest", "https://x.org/a") == "image"
    assert detect_format(b"  <!doctype HTML><html></html>", "https://x.org/a") == "html"
    assert detect_format(b'{"a": 1}', "https://x.org/a") == "json"
    assert detect_format(b"a,b\n1,2\n", "https://x.org/a.csv") == "csv"
    assert detect_format(b"plain", "https://x.org/a") == "other"


def test_snapshot_url_normalizes_and_matches_the_original() -> None:
    assert snapshot_url(f"http://web.archive.org/web/20990101000000im_/{URL}", URL) == (
        f"https://web.archive.org/web/20990101000000/{URL}"
    )
    assert snapshot_url(
        "https://web.archive.org/web/20990101000000/http://www.example.org/exemplar/raport.pdf",
        URL,
    )
    assert snapshot_url(f"https://example.org/web/20990101000000/{URL}", URL) is None


def test_cli_reports_and_exit_codes(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(archive_module, "http_fetch", happy_web())
    code = main(
        [
            "archive",
            URL,
            "--pollster",
            "exemplar",
            "--source-type",
            "pollster",
            "--data-dir",
            str(data_dir),
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "exemplar-doc-001 (new)" in out and SNAPSHOT in out
    monkeypatch.setattr(archive_module, "http_fetch", FakeWeb({}))
    code = main(["archive", URL + "x", "--pollster", "exemplar", "--data-dir", str(data_dir)])
    assert code == 1
    assert "archive: error:" in capsys.readouterr().err
