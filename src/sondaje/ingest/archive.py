"""Archive a poll publication: ``sondaje archive <url> --pollster <pollster_id>`` (T-011).

Implements the archive step of docs/POLL_INGESTION.md and the archive fields of
DATA_MODEL.md §5.2 and §6.10 (``archive_url``, ``sha256``, ``raw_path``, ``format``):

1. The publication must already be listed in ``data/polls/<pollster_id>/inventory.csv``
   (§6.13); archiving never invents an inventory row.
2. The file is downloaded (or read from ``--file`` when it had to be saved by hand), hashed
   (SHA-256), and saved to ``data/raw/polls/<pollster_id>/<document_id>.<ext>`` (git-ignored)
   once a snapshot is secured (step 3). A Google Drive ``view`` link is resolved to the direct
   download, which is also what gets snapshotted. Requests that fail with HTTP 429, a server
   error, a refused connection, or a timeout are retried (``--retries``).
3. A Web Archive snapshot is requested through Save Page Now. If that fails, an existing
   snapshot is looked up through the Wayback availability API. ``--archive-url`` supplies a
   snapshot made by other means. **No archive URL is ever made up**: when no snapshot can be
   created, found, or supplied, the command stops with an error and writes nothing (not even
   the raw file).
4. The snapshot's bytes are downloaded (gzip-encoded captures are decompressed) and compared
   with the download, and the result is reported (dynamic HTML pages usually differ; PDFs and
   images should not). Running the command again on unchanged bytes repeats the check.
5. The pollster's ``archive_manifest.csv`` row is appended (or updated, keyed by
   ``source_url``), and every inventory row for the URL gets the ``document_id``; rows with
   status ``found`` move to ``archived``.
"""

import argparse
import datetime as dt
import gzip
import hashlib
import http.client
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from sondaje.ingest.csvio import CsvFormatError, read_rows, write_rows
from sondaje.schema import ARCHIVE_MANIFEST, DOCUMENT_FORMATS, INVENTORY, SOURCE_TYPES

if TYPE_CHECKING:
    from sondaje.cli import Subparsers

USER_AGENT = (
    "Mozilla/5.0 (compatible; sondaje-la-control/0.1; "
    "+https://github.com/maxim-dirtu/sondaje-la-control)"
)
SAVE_ENDPOINT = "https://web.archive.org/save/"
AVAILABILITY_ENDPOINT = "https://archive.org/wayback/available?url="
SNAPSHOT_RE = re.compile(r"^https?://web\.archive\.org/web/(\d{14})(?:[a-z]{2}_)?/(.+)$")
DOWNLOAD_TIMEOUT = 120.0
SAVE_TIMEOUT = 300.0
LOOKUP_TIMEOUT = 60.0
URL_RE = re.compile(r"^https?://\S+$")
DRIVE_FILE_RE = re.compile(r"^/file/d/([\w-]+)(?:/|$)")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RAW_PREFIX = "data/raw/polls"
MIN_PDF_TEXT_LETTERS = 50
"""A PDF whose text layer has fewer letters than this is treated as ``pdf_image``."""

IMAGE_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"\xff\xd8\xff", ".jpg"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
)
SUFFIX_FORMATS = {".csv": "csv", ".xlsx": "xlsx", ".json": "json", ".zip": "zip"}


class ArchiveError(Exception):
    """The publication could not be archived; nothing was written to ``data/polls/``."""


@dataclass(frozen=True)
class Response:
    """An HTTP response: the final URL (after redirects), the headers, and the body."""

    url: str
    content: bytes
    headers: Mapping[str, str] = field(default_factory=dict)


type Fetcher = Callable[[str, float], Response]
FETCH_ERRORS = (OSError, http.client.HTTPException, ValueError)
"""What a fetcher may raise for a failed request (``urllib.error.URLError`` is an OSError)."""


def http_fetch(url: str, timeout: float) -> Response:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return Response(response.geturl(), response.read(), dict(response.headers.items()))


DEFAULT_RETRIES = 2
RETRY_BASE_DELAY = 10.0
"""Seconds before the first retry; the wait doubles with each further retry."""


def is_retriable(exc: Exception) -> bool:
    """Rate limiting (HTTP 429), server errors, refused or dropped connections and timeouts are
    worth another try; a bad URL or another client error (403, 404, ...) is not."""
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code == 429 or exc.code >= 500
    return not isinstance(exc, ValueError)


def retrying(fetch: Fetcher, retries: int, sleep: Callable[[float], None] = time.sleep) -> Fetcher:
    """``fetch`` that retries a retriable failure up to ``retries`` times, with backoff."""

    def fetch_with_retries(url: str, timeout: float) -> Response:
        for attempt in range(retries + 1):
            try:
                return fetch(url, timeout)
            except FETCH_ERRORS as exc:
                if attempt >= retries or not is_retriable(exc):
                    raise
                sleep(RETRY_BASE_DELAY * 2**attempt)
        raise AssertionError("unreachable")

    return fetch_with_retries


# --- Format detection ---------------------------------------------------------------------------


def pdf_has_text(content: bytes) -> bool:
    """True if the PDF has a text layer (at least :data:`MIN_PDF_TEXT_LETTERS` letters)."""
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(content))
        letters = 0
        for page in reader.pages:
            letters += sum(ch.isalpha() for ch in page.extract_text() or "")
            if letters >= MIN_PDF_TEXT_LETTERS:
                return True
    except Exception:  # pypdf raises many types on broken files; treat as no text layer
        return False
    return False


def image_suffix(content: bytes) -> str | None:
    for signature, suffix in IMAGE_SIGNATURES:
        if content.startswith(signature):
            return suffix
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp"
    return None


def url_suffix(url: str) -> str:
    return PurePosixPath(urllib.parse.urlsplit(url).path).suffix.lower()


def detect_format(content: bytes, url: str) -> str:
    """The DATA_MODEL §6.10 ``format`` of a downloaded file, from its bytes (and URL)."""
    if content.startswith(b"%PDF"):
        return "pdf_text" if pdf_has_text(content) else "pdf_image"
    if image_suffix(content):
        return "image"
    head = content[:4096].lstrip().lower()
    if head.startswith((b"<!doctype html", b"<html")) or b"<html" in head:
        return "html"
    suffix = url_suffix(url)
    if suffix in SUFFIX_FORMATS:
        return SUFFIX_FORMATS[suffix]
    if content.startswith(b"PK\x03\x04"):
        return "zip"
    if head.startswith((b"{", b"[")):
        try:
            json.loads(content)
        except ValueError:
            return "other"
        return "json"
    return "other"


def raw_suffix(document_format: str, content: bytes, url: str) -> str:
    if document_format in ("pdf_text", "pdf_image"):
        return ".pdf"
    if document_format == "html":
        return ".html"
    if document_format == "image":
        return image_suffix(content) or url_suffix(url) or ".img"
    if document_format in ("csv", "xlsx", "json", "zip"):
        return f".{document_format}"
    suffix = url_suffix(url)
    return suffix if re.fullmatch(r"\.[a-z0-9]{1,5}", suffix) else ".bin"


# --- Web Archive ----------------------------------------------------------------------------------


def direct_download_url(url: str) -> str:
    """The direct-download URL of a Google Drive ``view`` link (an HTML viewer, not the file);
    any other URL is returned unchanged."""
    parts = urllib.parse.urlsplit(url)
    if (parts.hostname or "").lower() != "drive.google.com":
        return url
    match = DRIVE_FILE_RE.match(parts.path)
    if match is None and parts.path.rstrip("/") == "/open":
        ids = urllib.parse.parse_qs(parts.query).get("id")
        match = re.fullmatch(r"([\w-]+)", ids[0]) if ids else None
    if match is None:
        return url
    return f"https://drive.google.com/uc?export=download&id={match.group(1)}"


def _comparable(url: str) -> str:
    """A URL without scheme, ``www.``, default port, and trailing slash (for comparisons)."""
    parts = urllib.parse.urlsplit(url.strip())
    host = (parts.hostname or "").lower().removeprefix("www.")
    path = parts.path.rstrip("/")
    query = f"?{parts.query}" if parts.query else ""
    return f"{host}{path}{query}"


def snapshot_url(candidate: str, original: str) -> str | None:
    """The canonical ``https://web.archive.org/web/<timestamp>/<url>`` form of a snapshot URL of
    ``original``, or ``None`` if ``candidate`` is not a snapshot of it."""
    match = SNAPSHOT_RE.match(candidate.strip())
    if match is None:
        return None
    timestamp, archived = match.groups()
    if _comparable(urllib.parse.unquote(archived)) != _comparable(original):
        return None
    return f"https://web.archive.org/web/{timestamp}/{archived}"


def snapshot_date(snapshot: str) -> str:
    match = SNAPSHOT_RE.match(snapshot)
    if match is None:
        return "unknown date"
    stamp = match.group(1)
    return f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}"


def save_snapshot(url: str, fetch: Fetcher) -> tuple[str | None, str]:
    """Ask Save Page Now for a snapshot. Returns (snapshot URL or None, explanation)."""
    try:
        response = fetch(SAVE_ENDPOINT + url, SAVE_TIMEOUT)
    except FETCH_ERRORS as exc:
        return None, f"Save Page Now failed: {exc}"
    candidates = [response.url]
    location = response.headers.get("Content-Location") or response.headers.get("content-location")
    if location:
        candidates.append(urllib.parse.urljoin("https://web.archive.org/", location))
    for candidate in candidates:
        snapshot = snapshot_url(candidate, url)
        if snapshot is not None:
            return snapshot, (
                f"Save Page Now returned a snapshot dated {snapshot_date(snapshot)} "
                "(it may return a recent existing capture instead of a new one)"
            )
    return None, f"Save Page Now returned no snapshot of this URL (ended at {response.url})"


def lookup_snapshot(url: str, fetch: Fetcher) -> tuple[str | None, str]:
    """Look up the closest existing snapshot (Wayback availability API)."""
    try:
        response = fetch(AVAILABILITY_ENDPOINT + urllib.parse.quote(url, safe=""), LOOKUP_TIMEOUT)
        data = json.loads(response.content)
    except FETCH_ERRORS as exc:
        return None, f"Wayback lookup failed: {exc}"
    closest = (data.get("archived_snapshots") or {}).get("closest") or {}
    if not closest.get("available") or str(closest.get("status")) != "200":
        return None, "Wayback lookup found no snapshot of this URL"
    snapshot = snapshot_url(str(closest.get("url", "")), url)
    if snapshot is None:
        return None, f"Wayback lookup returned an unusable URL: {closest.get('url')!r}"
    return snapshot, f"existing snapshot dated {snapshot_date(snapshot)} (Wayback lookup)"


def _gunzipped_sha256(content: bytes) -> str | None:
    """SHA-256 of the decompressed bytes if ``content`` is gzip data, else ``None``."""
    if content[:2] != b"\x1f\x8b":
        return None
    try:
        return hashlib.sha256(gzip.decompress(content)).hexdigest()
    except (OSError, EOFError, zlib.error):
        return None


def check_snapshot(snapshot: str, sha256: str, fetch: Fetcher) -> str:
    """Compare the snapshot's original bytes (``id_`` mode) with the downloaded file."""
    match = SNAPSHOT_RE.match(snapshot)
    if match is None:
        return "not checked (not a web.archive.org snapshot URL)"
    timestamp, archived = match.groups()
    try:
        content = fetch(f"https://web.archive.org/web/{timestamp}id_/{archived}", SAVE_TIMEOUT)
    except FETCH_ERRORS as exc:
        return (
            f"NOT CHECKED: the snapshot download failed ({exc}). The snapshot is unverified: "
            "open it and compare by hand, or run the same command again to repeat the check"
        )
    if hashlib.sha256(content.content).hexdigest() == sha256:
        return "identical: the snapshot has the same bytes as the download"
    if _gunzipped_sha256(content.content) == sha256:
        return (
            "identical: the snapshot has the same bytes as the download "
            "(the Web Archive served it gzip-encoded; compared after decompressing)"
        )
    return (
        "DIFFERENT: the snapshot's bytes differ from the download (usual for dynamic HTML "
        "pages; for a PDF or an image, open the snapshot and compare, and say so in notes)"
    )


# --- Archiving ------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ArchiveRequest:
    url: str
    pollster_id: str
    data_dir: Path
    document_format: str | None = None
    source_type: str | None = None
    title: str | None = None
    published_date: str | None = None
    notes: str | None = None
    archive_url: str | None = None
    save: bool = True
    check: bool = True
    file: Path | None = None
    retries: int = DEFAULT_RETRIES
    """Retries of a download or Web Archive request that failed in a retriable way."""


@dataclass
class ArchiveResult:
    document_id: str
    status: str
    """``new`` (row appended), ``updated`` (new bytes), or ``unchanged`` (same SHA-256)."""
    raw_path: str
    sha256: str
    size: int
    document_format: str
    format_detected: bool
    archive_url: str
    snapshot_origin: str
    snapshot_check: str | None
    inventory_updated: int
    attempts: list[str] = field(default_factory=list)
    download_url: str | None = None
    """For a Google Drive ``view`` link: the direct-download URL that was downloaded and
    snapshotted (the manifest's ``source_url`` stays the link as published)."""


def _clean(value: str | None) -> str | None:
    return None if value is None else " ".join(value.split())


def _check_request(request: ArchiveRequest) -> None:
    if not URL_RE.match(request.url):
        raise ArchiveError(f"not an absolute http(s) URL: {request.url!r}")
    if not SLUG_RE.match(request.pollster_id):
        raise ArchiveError(f"not a pollster_id: {request.pollster_id!r}")
    if request.document_format is not None and request.document_format not in DOCUMENT_FORMATS:
        raise ArchiveError(f"--format must be one of {', '.join(DOCUMENT_FORMATS)}")
    if request.source_type is not None and request.source_type not in SOURCE_TYPES:
        raise ArchiveError(f"--source-type must be one of {', '.join(SOURCE_TYPES)}")
    if request.published_date is not None:
        try:
            ok = DATE_RE.match(request.published_date) and dt.date.fromisoformat(
                request.published_date
            )
        except ValueError:
            ok = False
        if not ok:
            raise ArchiveError(f"--published-date must be YYYY-MM-DD: {request.published_date!r}")
    if request.retries < 0:
        raise ArchiveError("--retries must be 0 or more")
    if request.archive_url is not None and not URL_RE.match(request.archive_url):
        raise ArchiveError(f"--archive-url is not an absolute http(s) URL: {request.archive_url!r}")


def _next_document_id(pollster_id: str, rows: list[dict[str, str]]) -> str:
    pattern = re.compile(rf"^{re.escape(pollster_id)}-doc-(\d+)$")
    numbers = [int(m.group(1)) for row in rows if (m := pattern.match(row["document_id"]))]
    return f"{pollster_id}-doc-{max(numbers, default=0) + 1:03d}"


def archive(
    request: ArchiveRequest,
    fetch: Fetcher | None = None,
    today: dt.date | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> ArchiveResult:
    """Archive one publication (see the module docstring). Raises :class:`ArchiveError`."""
    _check_request(request)
    fetch = retrying(fetch or http_fetch, request.retries, sleep)
    today = today or dt.date.today()
    directory = request.data_dir / "polls" / request.pollster_id
    manifest_path = directory / ARCHIVE_MANIFEST.filename
    inventory_path = directory / INVENTORY.filename
    if not inventory_path.is_file():
        raise ArchiveError(
            f"{inventory_path.as_posix()} does not exist; create the pollster directory with the "
            "header lines of DATA_MODEL.md §6.14 and list the publication first"
        )
    try:
        manifest = read_rows(manifest_path, ARCHIVE_MANIFEST)
        inventory = read_rows(inventory_path, INVENTORY)
    except CsvFormatError as exc:
        raise ArchiveError(str(exc)) from exc
    listed = [row for row in inventory if row["publication_url"] == request.url]
    if not listed:
        raise ArchiveError(
            f"{request.url} is not in {inventory_path.as_posix()}; add a row for it "
            "(status found) before archiving it (POLL_INGESTION.md step 2)"
        )
    existing = next((row for row in manifest if row["source_url"] == request.url), None)
    source_type = request.source_type or (existing or {}).get("source_type")
    if not source_type:
        raise ArchiveError("--source-type is required for a new document")

    fetch_url = direct_download_url(request.url)
    if request.file is not None:
        content = request.file.read_bytes()
    else:
        try:
            content = fetch(fetch_url, DOWNLOAD_TIMEOUT).content
        except FETCH_ERRORS as exc:
            raise ArchiveError(
                f"download failed: {exc}. If the site blocks scripts, save the file with a "
                "browser and pass it with --file"
            ) from exc
    if not content:
        raise ArchiveError("the download is empty")
    digest = hashlib.sha256(content).hexdigest()
    document_format = request.document_format or detect_format(content, request.url)
    if (
        fetch_url != request.url
        and request.file is None
        and request.document_format is None
        and document_format == "html"
    ):
        raise ArchiveError(
            f"Google Drive returned a web page, not the file, for {fetch_url} (a private file, "
            "a quota limit, or a file too large for the virus-scan check). Save the file with a "
            "browser and pass it with --file"
        )
    document_id = (
        existing["document_id"] if existing else _next_document_id(request.pollster_id, manifest)
    )
    raw_name = document_id + raw_suffix(document_format, content, request.url)
    raw_file = request.data_dir / "raw" / "polls" / request.pollster_id / raw_name
    unchanged = existing is not None and existing["sha256"] == digest

    attempts: list[str] = []
    snapshot: str | None = None
    origin = ""
    if request.archive_url is not None:
        snapshot, origin = request.archive_url, "supplied with --archive-url"
    elif unchanged and existing and existing["archive_url"]:
        snapshot, origin = existing["archive_url"], "kept from the manifest (same SHA-256)"
    else:
        if request.save:
            snapshot, origin = save_snapshot(fetch_url, fetch)
            attempts.append(origin)
        if snapshot is None:
            snapshot, origin = lookup_snapshot(fetch_url, fetch)
            attempts.append(origin)
    if snapshot is None:
        raise ArchiveError(
            "no Web Archive snapshot could be created or found ("
            + "; ".join(attempts)
            + f"). Nothing was saved or written (sha256 of the download: {digest}); no raw file "
            "is left under data/raw/. Retry later, or make a snapshot by other means and pass "
            "it with --archive-url; never enter a URL that was not checked"
        )
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_bytes(content)
    snapshot_check = (
        check_snapshot(snapshot, digest, fetch)
        if request.check and request.archive_url is None
        else None
    )

    row = {
        "document_id": document_id,
        "title": _clean(request.title) if request.title is not None else None,
        "published_date": request.published_date,
        "format": document_format,
        "archive_url": snapshot,
        "sha256": digest,
        "raw_path": f"{RAW_PREFIX}/{request.pollster_id}/{raw_name}",
        "source_url": request.url,
        "source_type": source_type,
        "retrieved_at": existing["retrieved_at"] if unchanged and existing else today.isoformat(),
        "notes": _clean(request.notes) if request.notes is not None else None,
    }
    if existing is not None:
        for column in ("title", "published_date", "notes"):
            if row[column] is None:
                row[column] = existing[column]
        if request.document_format is None and existing["format"]:
            row["format"] = existing["format"]
            document_format = existing["format"]
        existing.update({k: v or "" for k, v in row.items()})
    else:
        manifest.append({k: v or "" for k, v in row.items()})
    write_rows(manifest_path, ARCHIVE_MANIFEST, manifest)

    updated = 0
    for item in listed:
        changed = item["document_id"] != document_id or item["status"] == "found"
        item["document_id"] = document_id
        if item["status"] == "found":
            item["status"] = "archived"
        updated += changed
    write_rows(inventory_path, INVENTORY, inventory)

    return ArchiveResult(
        document_id=document_id,
        status="new" if existing is None else "unchanged" if unchanged else "updated",
        raw_path=row["raw_path"] or "",
        sha256=digest,
        size=len(content),
        document_format=document_format,
        format_detected=request.document_format is None and existing is None,
        archive_url=snapshot,
        snapshot_origin=origin,
        snapshot_check=snapshot_check,
        inventory_updated=updated,
        attempts=attempts,
        download_url=fetch_url if fetch_url != request.url else None,
    )


# --- CLI ------------------------------------------------------------------------------------------


def register(subparsers: "Subparsers") -> None:
    parser = subparsers.add_parser(
        "archive",
        help="Download a poll publication, hash it, snapshot it, and record it.",
        description=(
            "Archive one publication listed in data/polls/<pollster_id>/inventory.csv: download "
            "it to data/raw/ (git-ignored), compute its SHA-256, request a Web Archive snapshot "
            "(Save Page Now, else the closest existing snapshot), and append or update its row "
            "in archive_manifest.csv. Inventory rows for the URL get the document_id and move "
            "from 'found' to 'archived'. Without a snapshot nothing is written."
        ),
    )
    parser.add_argument("url", help="the publication URL (as listed in inventory.csv)")
    parser.add_argument("--pollster", required=True, help="pollster_id (directory name)")
    parser.add_argument(
        "--source-type", choices=SOURCE_TYPES, help="DATA_MODEL §5.1 source_type (new documents)"
    )
    parser.add_argument(
        "--format",
        dest="document_format",
        choices=DOCUMENT_FORMATS,
        help="DATA_MODEL §6.10 format (default: detected from the file)",
    )
    parser.add_argument("--title", help="title as published (original language)")
    parser.add_argument("--published-date", help="publication date, YYYY-MM-DD")
    parser.add_argument("--notes", help="English notes for the manifest row")
    parser.add_argument(
        "--archive-url",
        help="an existing snapshot URL (checked by you) to use instead of Save Page Now",
    )
    parser.add_argument(
        "--no-save", action="store_true", help="do not request a new snapshot; only look one up"
    )
    parser.add_argument(
        "--no-check", action="store_true", help="do not compare the snapshot with the download"
    )
    parser.add_argument(
        "--file", type=Path, help="use this local copy instead of downloading (saved by hand)"
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help=(
            "retries (waits of 10 s, 20 s, ...) for a download or Web Archive request that "
            "fails with HTTP 429, a server error, a refused connection or a timeout "
            f"(default: {DEFAULT_RETRIES})"
        ),
    )
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data"), help="data directory (default: data)"
    )
    parser.set_defaults(handler=run)


def format_result(result: ArchiveResult) -> str:
    detected = "detected" if result.format_detected else "given or kept"
    lines = [
        f"{result.document_id} ({result.status})",
    ]
    if result.download_url is not None:
        lines.append(f"  Google Drive view link resolved to {result.download_url}")
    lines += [
        f"  saved {result.size} bytes to {result.raw_path}",
        f"  format {result.document_format} ({detected}); sha256 {result.sha256}",
    ]
    lines.extend(f"  tried: {attempt}" for attempt in result.attempts[:-1])
    lines.append(f"  archive_url {result.archive_url}")
    lines.append(f"    {result.snapshot_origin}")
    if result.snapshot_check is not None:
        lines.append(f"  snapshot check: {result.snapshot_check}")
    lines.append("  archive_manifest.csv written")
    lines.append(f"  inventory.csv: {result.inventory_updated} row(s) linked to the document")
    return "\n".join(lines) + "\n"


def run(args: argparse.Namespace) -> int:
    out = sys.stdout
    if isinstance(out, io.TextIOWrapper):
        out.reconfigure(errors="backslashreplace")
    request = ArchiveRequest(
        url=args.url,
        pollster_id=args.pollster,
        data_dir=args.data_dir,
        document_format=args.document_format,
        source_type=args.source_type,
        title=args.title,
        published_date=args.published_date,
        notes=args.notes,
        archive_url=args.archive_url,
        save=not args.no_save,
        check=not args.no_check,
        file=args.file,
        retries=args.retries,
    )
    try:
        result = archive(request)
    except (ArchiveError, OSError) as exc:
        sys.stderr.write(f"archive: error: {exc}\n")
        return 1
    out.write(format_result(result))
    return 0
