"""Text-PDF extraction helpers: ``sondaje extract-pdf`` and ``sondaje render-pdf`` (T-011).

``extract-pdf`` turns the text layer of chosen pages into a **draft** ``poll_results.csv``
(see :mod:`sondaje.ingest.drafts`; drafts are reviewed before anything is committed). Three
ways to read a page:

* ``lines``: one option per text line, ``<label> <value>%`` (tables and horizontal bar
  charts whose labels and values share a line, e.g. CURS presentations).
* ``chart``: value labels of a bar chart (``38.9%`` above or beside each bar) paired with
  the category labels by position: by x for column charts, by y for horizontal bars (e.g.
  the Verifield report, where values and labels are separate text runs).
* ``tables``: ruled tables found by pdfplumber, one option per row (first text cell, first
  value cell).

``auto`` (default) uses ``lines`` when a page has at least two such lines, else ``chart``.
Values inside **images** have no text layer; render those pages with ``render-pdf`` and use
manual double entry (docs/POLL_INGESTION.md).
"""

import argparse
import io
import re
import statistics
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sondaje.ingest.drafts import (
    VALUE_TOKEN_RE,
    DraftRow,
    Provenance,
    document_source,
    guess_type,
    matcher_for,
    normalize_value,
    summary,
    write_draft,
)
from sondaje.schema import SHARE_BASES

if TYPE_CHECKING:
    from sondaje.cli import Subparsers

LINE_RE = re.compile(
    r"^(?P<label>.*[^\W\d_].*?)[\s:\u2013-]*(?P<lt><\s*|sub\s+)?(?P<value>\d{1,3}(?:[.,]\d+)?)\s*%"
    r"(?P<rest>[^%]*)$",
    re.IGNORECASE,
)
"""``<label> <value>%`` on one line; the label is greedy, so the line's *last* value is used
(``Altul (sub 1% fiecare) 3%`` → ``Altul (sub 1% fiecare)``, ``3``)."""
MODES = ("auto", "lines", "chart", "tables")
LABEL_GAP = 10.0
"""Horizontal gap (pt) that separates two category labels of a column chart."""
LABEL_BAND_LINES = 3.0
"""Category labels may wrap: the label band is this many text heights tall."""
MIN_TEXT_LETTERS = 50
"""A page range with fewer letters than this has no usable text layer."""
SPLIT_WORDS_SHARE = 0.4
"""A text layer where this share of the words are single characters is unreadable."""


class ExtractError(Exception):
    """The input cannot be read."""


@dataclass(frozen=True)
class Word:
    text: str
    x0: float
    x1: float
    top: float
    bottom: float

    @property
    def x(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def y(self) -> float:
        return (self.top + self.bottom) / 2


def _value(word: Word) -> tuple[str, str] | None:
    match = VALUE_TOKEN_RE.match(word.text)
    if match is None:
        return None
    return normalize_value(match.group("value")), "lt" if match.group("lt") else ""


def _merge_lt(words: list[Word]) -> list[Word]:
    """Join a separate ``<`` word with the value that follows it (``<`` ``1%`` → ``<1%``)."""
    merged: list[Word] = []
    for word in words:
        if merged and merged[-1].text == "<" and VALUE_TOKEN_RE.match(word.text):
            previous = merged.pop()
            word = Word("<" + word.text, previous.x0, word.x1, word.top, word.bottom)
        merged.append(word)
    return merged


def page_lines(text: str, page: int) -> list[DraftRow]:
    rows = []
    for number, line in enumerate(text.splitlines(), start=1):
        match = LINE_RE.match(line.strip())
        if match is None:
            continue
        label = match.group("label").strip(" \t:\u2013-")
        rest = match.group("rest").strip()
        where = f"p.{page} line {number}" + (f" (also on the line: {rest!r})" if rest else "")
        rows.append(
            DraftRow(
                label=label,
                value=normalize_value(match.group("value")),
                qualifier="lt" if match.group("lt") else "",
                where=where,
            )
        )
    return rows


def _cluster(words: list[Word], key_start: str, key_end: str, gap: float) -> list[list[Word]]:
    """Group words whose [start, end] intervals (on one axis) overlap or are within ``gap``."""
    groups: list[list[Word]] = []
    end = float("-inf")
    for word in sorted(words, key=lambda w: getattr(w, key_start)):
        if groups and getattr(word, key_start) <= end + gap:
            groups[-1].append(word)
            end = max(end, getattr(word, key_end))
        else:
            groups.append([word])
            end = getattr(word, key_end)
    return groups


def _label_text(group: list[Word]) -> str:
    lines = _cluster(group, "top", "bottom", 0.0)
    return " ".join(
        " ".join(w.text for w in sorted(line, key=lambda w: w.x0))
        for line in sorted(lines, key=lambda line: min(w.top for w in line))
    )


def page_chart(words: Sequence[Word], page: int) -> list[DraftRow]:
    """Pair chart value labels with category labels by position (see the module docstring)."""
    merged = _merge_lt(sorted(words, key=lambda w: (round(w.top), w.x0)))
    values = [w for w in merged if _value(w)]
    others = [w for w in merged if not _value(w)]
    if len(values) < 2 or not others:
        return []
    height = statistics.median(w.bottom - w.top for w in merged) or 10.0
    same_row = sum(
        any(w.x1 < v.x0 and abs(w.y - v.y) < 0.6 * height for w in others) for v in values
    )
    columns = same_row * 2 < len(values)
    if columns:
        below = [w for w in others if w.top > max(v.top for v in values)]
        if not below:
            return []
        first = min(w.top for w in below)
        band = [w for w in below if w.top <= first + LABEL_BAND_LINES * height]
        groups = _cluster(band, "x0", "x1", LABEL_GAP)
        centers = [
            (statistics.fmean([min(w.x0 for w in g), max(w.x1 for w in g)]), g) for g in groups
        ]
        axis = "x"
    else:
        left = [w for w in others if w.x1 < min(v.x0 for v in values)]
        if not left:
            return []
        groups = _cluster(left, "top", "bottom", height * 0.3)
        centers = [
            (statistics.fmean([min(w.top for w in g), max(w.bottom for w in g)]), g) for g in groups
        ]
        axis = "y"
    ordered_values = sorted(values, key=lambda v: v.x if columns else v.y)
    ordered_labels = sorted(centers, key=lambda item: item[0])
    exact = len(ordered_values) == len(ordered_labels)
    rows = []
    for index, word in enumerate(ordered_values):
        position = word.x if columns else word.y
        if exact:
            _, group = ordered_labels[index]
        else:
            _, group = min(ordered_labels, key=lambda item: abs(item[0] - position))
        value, qualifier = _value(word) or ("", "")
        note = f"p.{page} chart, paired by {axis}"
        if not exact:
            note += f" (CHECK: {len(ordered_values)} values, {len(ordered_labels)} labels)"
        rows.append(DraftRow(_label_text(group), value, qualifier, note))
    return rows


def page_tables(tables: Sequence[Sequence[Sequence[str | None]]], page: int) -> list[DraftRow]:
    rows = []
    for t, table in enumerate(tables, start=1):
        for r, cells in enumerate(table, start=1):
            texts = [" ".join((cell or "").split()) for cell in cells]
            label = next((c for c in texts if re.search(r"[^\W\d_]", c)), None)
            value = next(
                (m for c in texts if (m := VALUE_TOKEN_RE.match(c.replace(" ", "")))), None
            )
            if label is None or value is None:
                continue
            rows.append(
                DraftRow(
                    label=label,
                    value=normalize_value(value.group("value")),
                    qualifier="lt" if value.group("lt") else "",
                    where=f"p.{page} table {t} row {r}",
                )
            )
    return rows


def parse_pages(spec: str | None, count: int) -> list[int]:
    """``"3,5-7"`` → ``[3, 5, 6, 7]`` (1-based); ``None`` → every page."""
    if not spec:
        return list(range(1, count + 1))
    pages: list[int] = []
    for part in spec.split(","):
        first, _, last = part.strip().partition("-")
        try:
            start, end = int(first), int(last or first)
        except ValueError as exc:
            raise ExtractError(f"bad page list {spec!r}") from exc
        if not 1 <= start <= end <= count:
            raise ExtractError(f"pages {part!r} outside 1..{count}")
        pages.extend(range(start, end + 1))
    return pages


def extract_pdf(path: Path, pages: str | None = None, mode: str = "auto") -> list[DraftRow]:
    """Extract label/value pairs from the text layer of ``path`` (see the module docstring)."""
    import pdfplumber

    if mode not in MODES:
        raise ExtractError(f"mode must be one of {', '.join(MODES)}")
    rows: list[DraftRow] = []
    try:
        pdf_context = pdfplumber.open(path)
    except Exception as exc:  # pdfminer raises several types for non-PDF input
        raise ExtractError(f"{path}: cannot open as PDF ({exc})") from exc
    with pdf_context as pdf:
        for number in parse_pages(pages, len(pdf.pages)):
            page: Any = pdf.pages[number - 1]
            if mode == "tables":
                rows.extend(page_tables(page.extract_tables(), number))
                continue
            found: list[DraftRow] = []
            if mode in ("auto", "lines"):
                found = page_lines(page.extract_text() or "", number)
            if mode == "chart" or (mode == "auto" and len(found) < 2):
                words = [
                    Word(w["text"], w["x0"], w["x1"], w["top"], w["bottom"])
                    for w in page.extract_words()
                ]
                found = page_chart(words, number)
            rows.extend(found)
    return rows


def text_layer_problem(path: Path, pages: str | None = None) -> str | None:
    """Why the text layer of the chosen pages cannot be read, or ``None`` if it looks readable.

    Two cases: no text at all (a scanned or image-only PDF), and text whose letters are
    separate runs (spaced letters, split numbers), so words and values cannot be rebuilt."""
    import pdfplumber

    try:
        with pdfplumber.open(path) as pdf:
            words = [
                word["text"]
                for number in parse_pages(pages, len(pdf.pages))
                for word in pdf.pages[number - 1].extract_words()
            ]
    except ExtractError:
        raise
    except Exception as exc:  # pdfminer raises several types for broken files
        raise ExtractError(f"{path}: cannot open as PDF ({exc})") from exc
    letters = sum(ch.isalpha() for word in words for ch in word)
    if letters < MIN_TEXT_LETTERS:
        return "the pages have no text layer (a scanned or image-only PDF)"
    if sum(len(word) == 1 for word in words) / len(words) >= SPLIT_WORDS_SHARE:
        return (
            "the text layer is unreadable: most words are single characters (spaced letters, "
            "split numbers), so labels and values cannot be rebuilt"
        )
    return None


def render_pdf(path: Path, out_dir: Path, pages: str | None, resolution: int) -> list[Path]:
    """Render pages to PNG (for manual double entry from chart images)."""
    import pdfplumber

    written = []
    out_dir.mkdir(parents=True, exist_ok=True)
    with pdfplumber.open(path) as pdf:
        for number in parse_pages(pages, len(pdf.pages)):
            target = out_dir / f"{path.stem}-p{number:02d}.png"
            pdf.pages[number - 1].to_image(resolution=resolution).save(target)
            written.append(target)
    return written


# --- CLI ------------------------------------------------------------------------------------------


def _add_source_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("file", nargs="?", type=Path, help="a local PDF file")
    parser.add_argument("--pollster", help="pollster_id, with --document")
    parser.add_argument("--document", help="document_id in the pollster's archive_manifest.csv")
    parser.add_argument("--pages", help='pages, e.g. "3" or "3,5-6" (default: all)')
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data"), help="data directory (default: data)"
    )


def resolve_source(args: argparse.Namespace) -> tuple[Path, Provenance | None]:
    if args.document:
        if not args.pollster:
            raise ExtractError("--document needs --pollster")
        return document_source(args.data_dir, args.pollster, args.document)
    if args.file is None:
        raise ExtractError("give a file, or --pollster and --document")
    return args.file, None


def register(subparsers: "Subparsers") -> None:
    parser = subparsers.add_parser(
        "extract-pdf",
        help="Draft a poll_results.csv from the text layer of a PDF (reviewed before use).",
        description=(
            "Extract label/value pairs from the text layer of a PDF into a DRAFT "
            "poll_results.csv (default under build/drafts/). option_type and entity_id are "
            "guesses. Review every row against the original before copying it into data/."
        ),
    )
    _add_source_arguments(parser)
    parser.add_argument("--mode", choices=MODES, default="auto", help="how to read the pages")
    parser.add_argument("--poll-id", default="", help="poll_id to put in the draft")
    parser.add_argument("--share-base", choices=SHARE_BASES, help="share_base for these rows")
    parser.add_argument("--election", help="election_id: guess only entities that can run in it")
    parser.add_argument("--out", type=Path, help="draft CSV (default: build/drafts/<name>.csv)")
    parser.add_argument("--append", action="store_true", help="append to an existing draft")
    parser.set_defaults(handler=run_extract)

    render = subparsers.add_parser(
        "render-pdf",
        help="Render PDF pages to PNG for manual double entry.",
        description="Render PDF pages to PNG images (default under build/render/).",
    )
    _add_source_arguments(render)
    render.add_argument("--resolution", type=int, default=150, help="DPI (default: 150)")
    render.add_argument("--out-dir", type=Path, help="output directory")
    render.set_defaults(handler=run_render)


def run_extract(args: argparse.Namespace) -> int:
    try:
        path, provenance = resolve_source(args)
        rows = extract_pdf(path, args.pages, args.mode)
        matcher = matcher_for(args.data_dir, args.election)
    except (ExtractError, OSError) as exc:
        sys.stderr.write(f"extract-pdf: error: {exc}\n")
        return 1
    for row in rows:
        row.option_type, row.entity_id = guess_type(row.label, matcher)
    out = args.out or Path("build") / "drafts" / f"{args.document or path.stem}.csv"
    count = write_draft(
        out,
        rows,
        poll_id=args.poll_id,
        share_base=args.share_base or "",
        provenance=provenance,
        append=args.append,
    )
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(errors="backslashreplace")
    sys.stdout.write(f"{count} draft row(s) from {path}:\n{summary(rows)}\n")
    sys.stdout.write(f"wrote {out.as_posix()} (DRAFT: review every row against the original)\n")
    try:
        problem = text_layer_problem(path, args.pages)
    except ExtractError as exc:
        problem = str(exc)
    advice = (
        "Render the pages with `sondaje render-pdf` and enter the values by double entry "
        "(docs/POLL_INGESTION.md section 7); OCR is not part of the toolkit.\n"
    )
    if problem is not None:
        verdict = "no rows found" if not rows else "the rows above are probably wrong"
        sys.stderr.write(f"extract-pdf: {verdict}: {problem}.\n  {advice}")
    elif not rows:
        sys.stderr.write(
            "extract-pdf: no rows found; try another --mode, or enter the values by hand\n"
        )
    return 0 if rows else 1


def run_render(args: argparse.Namespace) -> int:
    try:
        path, _ = resolve_source(args)
        out_dir = args.out_dir or Path("build") / "render" / (args.document or path.stem)
        written = render_pdf(path, out_dir, args.pages, args.resolution)
    except (ExtractError, OSError) as exc:
        sys.stderr.write(f"render-pdf: error: {exc}\n")
        return 1
    for target in written:
        sys.stdout.write(f"wrote {target.as_posix()}\n")
    return 0
