"""HTML extraction helper: ``sondaje extract-html`` (T-011).

Turns an archived HTML page into a **draft** ``poll_results.csv`` (reviewed before use; see
:mod:`sondaje.ingest.drafts`), and prints the page metadata that the inventory and the
manifest need (title, publication time, images). Two ways to read a page:

* ``tables``: every ``<table>``, one option per row (first text cell, first value cell).
* ``text``: every percentage written in the text (``35%``, ``21,1 %``, ``14 procente``,
  ``sub 1%``), one draft row each, with the sentence it appears in. The label is a *guess*:
  the registry entity named next to the value in the same clause (the one just before it,
  else the one just after it), copied verbatim from the page. Media articles often state
  values in prose ("53% la 47% în favoarea lui ..."), so a text-mode draft is a checklist
  of every number on the page, not a topline: the reviewer keeps the rows that are poll
  options, fixes labels, and deletes the rest.

``auto`` (default) uses ``tables`` when the page has a table row with a value, else ``text``.
"""

import argparse
import html
import io
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import TYPE_CHECKING

from sondaje.ingest.drafts import (
    DraftRow,
    EntityMatcher,
    guess_type,
    matcher_for,
    normalize_value,
    summary,
    write_draft,
)
from sondaje.ingest.extract_pdf import (
    ExtractError,
    _add_source_arguments,
    resolve_source,
)
from sondaje.schema import SHARE_BASES

if TYPE_CHECKING:
    from sondaje.cli import Subparsers

MODES = ("auto", "tables", "text")
MAX_IMAGES_SHOWN = 8
BLOCK_TAGS = frozenset(
    {
        *("address", "article", "aside", "blockquote", "br", "dd", "div", "dl", "dt"),
        *("figcaption", "figure", "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header"),
        *("hr", "li", "main", "nav", "ol", "p", "pre", "section", "table", "tbody", "td"),
        *("tfoot", "th", "thead", "tr", "ul"),
    }
)
SKIP_TAGS = frozenset(["script", "style", "noscript", "svg", "template", "iframe"])
VALUE_IN_TEXT_RE = re.compile(
    r"(?<![\w.,])(?P<lt>(?:<|sub)\s*)?(?P<value>\d{1,3}(?:[.,]\d+)?)\s*"
    r"(?:%|(?:de\s+)?procente\b|(?:de\s+)?procent\b|la\s+sut[ăa]\b)",
    re.IGNORECASE,
)
CLAUSE_BREAK_RE = re.compile(
    r"[,;:()]|\s[\u2013\u2014-]\s|\s(?:iar|și|şi|dar|urmat|urmată)\s", re.IGNORECASE
)
SENTENCE_RE = re.compile(r"[^.!?…]+(?:[.!?…]+|$)")


@dataclass
class Page:
    """What the parser collected from one HTML page."""

    title: str = ""
    meta: dict[str, str] = field(default_factory=dict)
    blocks: list[str] = field(default_factory=list)
    tables: list[list[list[str]]] = field(default_factory=list)
    images: list[tuple[str, str]] = field(default_factory=list)
    json_ld: list[str] = field(default_factory=list)


class _Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.page = Page()
        self.text: list[str] = []
        self.skip = 0
        self.in_title = False
        self.in_json_ld = False
        self.json_buffer: list[str] = []
        self.table_stack: list[list[list[str]]] = []
        self.cell: list[str] | None = None

    def _flush(self) -> None:
        block = " ".join("".join(self.text).split())
        if block:
            self.page.blocks.append(block)
        self.text = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {k: v or "" for k, v in attrs}
        if tag == "script" and values.get("type") == "application/ld+json":
            self.in_json_ld = True
            self.json_buffer = []
            return
        if tag == "meta":
            key = values.get("property") or values.get("name") or values.get("itemprop")
            if key and "content" in values:
                self.page.meta.setdefault(key.lower(), values["content"])
            return
        if tag == "img":
            src = values.get("data-src") or values.get("src") or ""
            if src:
                self.page.images.append((src, values.get("alt", "")))
            return
        if tag in SKIP_TAGS:
            self.skip += 1
            return
        if self.skip:
            return
        if tag == "title":
            self.in_title = True
        if tag in BLOCK_TAGS:
            self._flush()
        if tag == "table":
            self.table_stack.append([])
        elif tag == "tr" and self.table_stack:
            self.table_stack[-1].append([])
        elif tag in ("td", "th") and self.table_stack:
            self.cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.in_json_ld:
            self.in_json_ld = False
            self.page.json_ld.append("".join(self.json_buffer))
            return
        if tag in SKIP_TAGS:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag == "title":
            self.in_title = False
            return
        if tag in ("td", "th") and self.cell is not None and self.table_stack:
            rows = self.table_stack[-1]
            if not rows:
                rows.append([])
            rows[-1].append(" ".join("".join(self.cell).split()))
            self.cell = None
        if tag == "table" and self.table_stack:
            self.page.tables.append(self.table_stack.pop())
        if tag in BLOCK_TAGS:
            self._flush()

    def handle_data(self, data: str) -> None:
        if self.in_json_ld:
            self.json_buffer.append(data)
            return
        if self.in_title:
            self.page.title += data
            return
        if self.skip:
            return
        self.text.append(data)
        if self.cell is not None:
            self.cell.append(data)

    def close(self) -> None:
        super().close()
        self._flush()


def parse_html(content: bytes) -> Page:
    match = re.search(rb"<meta[^>]+charset=[\"']?([\w-]+)", content[:4096], re.IGNORECASE)
    encoding = match.group(1).decode() if match else "utf-8"
    try:
        text = content.decode(encoding, errors="replace")
    except LookupError:
        text = content.decode("utf-8", errors="replace")
    parser = _Parser()
    parser.feed(text)
    parser.close()
    parser.page.title = " ".join(html.unescape(parser.page.title).split())
    return parser.page


def published_times(page: Page) -> list[str]:
    """Publication timestamps declared by the page (meta tags and JSON-LD)."""
    found = [
        page.meta[key]
        for key in ("article:published_time", "datepublished", "date", "pubdate")
        if key in page.meta
    ]
    for block in page.json_ld:
        found.extend(re.findall(r'"datePublished"\s*:\s*"([^"]+)"', block))
    return list(dict.fromkeys(found))


def table_rows(page: Page) -> list[DraftRow]:
    rows = []
    for t, table in enumerate(page.tables, start=1):
        for r, cells in enumerate(table, start=1):
            label = next((c for c in cells if re.search(r"[^\W\d_]", c)), None)
            value = next((m for c in cells if (m := VALUE_IN_TEXT_RE.fullmatch(c.strip()))), None)
            if label is None or value is None:
                continue
            rows.append(
                DraftRow(
                    label=label,
                    value=normalize_value(value.group("value")),
                    qualifier="lt" if value.group("lt") else "",
                    where=f"table {t} row {r}",
                )
            )
    return rows


def _clause_bounds(sentence: str, start: int, end: int) -> tuple[int, int]:
    """The clause around ``sentence[start:end]``: from the previous break to the next one."""
    left = 0
    for match in CLAUSE_BREAK_RE.finditer(sentence, 0, start):
        left = match.end()
    following = CLAUSE_BREAK_RE.search(sentence, end)
    return left, following.start() if following else len(sentence)


def text_rows(page: Page, matcher: EntityMatcher | None) -> list[DraftRow]:
    rows = []
    for b, block in enumerate(page.blocks, start=1):
        for sentence_match in SENTENCE_RE.finditer(block):
            sentence = sentence_match.group(0).strip()
            entities = matcher.find_all(sentence) if matcher else []
            values = list(VALUE_IN_TEXT_RE.finditer(sentence))
            for value in values:
                start, end = value.span()
                left, right = _clause_bounds(sentence, start, end)
                before = [
                    e
                    for e in entities
                    if left <= e[0]
                    and e[1] <= start
                    and not any(e[1] <= v.start() < start for v in values)
                ]
                after = [
                    e
                    for e in entities
                    if end <= e[0]
                    and e[1] <= right
                    and not any(end <= v.start() < e[0] for v in values)
                ]
                chosen = before[-1] if before else after[0] if after else None
                label = sentence[chosen[0] : chosen[1]] if chosen else ""
                rows.append(
                    DraftRow(
                        label=label,
                        value=normalize_value(value.group("value")),
                        qualifier="lt" if value.group("lt") else "",
                        where=f"block {b}: {sentence[:220]}",
                        option_type=chosen[2].entity_type if chosen else "",
                        entity_id=chosen[2].entity_id if chosen else "",
                    )
                )
    return rows


def extract_html(
    content: bytes, mode: str, matcher: EntityMatcher | None
) -> tuple[Page, list[DraftRow]]:
    if mode not in MODES:
        raise ExtractError(f"mode must be one of {', '.join(MODES)}")
    page = parse_html(content)
    rows: list[DraftRow] = []
    if mode in ("auto", "tables"):
        rows = table_rows(page)
        for row in rows:
            row.option_type, row.entity_id = guess_type(row.label, matcher)
    if mode == "text" or (mode == "auto" and not rows):
        rows = text_rows(page, matcher)
    return page, rows


def describe(page: Page) -> str:
    lines = [f"title: {page.title}"]
    for key in ("og:title", "article:published_time", "article:modified_time", "og:url"):
        if key in page.meta:
            lines.append(f"{key}: {page.meta[key]}")
    for stamp in published_times(page):
        lines.append(f"published (declared): {stamp}")
    images = [
        (src, alt)
        for src, alt in page.images
        if re.search(r"\.(?:jpe?g|png|gif|webp)\b", src, re.IGNORECASE)
    ]
    for src, alt in images[:MAX_IMAGES_SHOWN]:
        lines.append(f"image: {src}" + (f"  alt={alt!r}" if alt else ""))
    if len(images) > MAX_IMAGES_SHOWN:
        lines.append(f"... and {len(images) - MAX_IMAGES_SHOWN} more image(s)")
    lines.append(f"{len(page.blocks)} text block(s), {len(page.tables)} table(s)")
    return "\n".join(lines)


# --- CLI ------------------------------------------------------------------------------------------


def register(subparsers: "Subparsers") -> None:
    parser = subparsers.add_parser(
        "extract-html",
        help="Draft a poll_results.csv from an HTML page (tables or text; reviewed before use).",
        description=(
            "Read an archived HTML page: print its title, declared publication time, and images, "
            "and write a DRAFT poll_results.csv (default under build/drafts/) from its tables or "
            "from every percentage in its text. Review every row against the original."
        ),
    )
    _add_source_arguments(parser)
    parser.add_argument("--mode", choices=MODES, default="auto", help="how to read the page")
    parser.add_argument("--poll-id", default="", help="poll_id to put in the draft")
    parser.add_argument("--share-base", choices=SHARE_BASES, help="share_base for these rows")
    parser.add_argument("--election", help="election_id: guess only entities that can run in it")
    parser.add_argument("--out", type=Path, help="draft CSV (default: build/drafts/<name>.csv)")
    parser.add_argument("--append", action="store_true", help="append to an existing draft")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(errors="backslashreplace")
    try:
        path, provenance = resolve_source(args)
        content = path.read_bytes()
        page, rows = extract_html(content, args.mode, matcher_for(args.data_dir, args.election))
    except (ExtractError, OSError) as exc:
        sys.stderr.write(f"extract-html: error: {exc}\n")
        return 1
    out = args.out or Path("build") / "drafts" / f"{args.document or path.stem}.csv"
    count = write_draft(
        out,
        rows,
        poll_id=args.poll_id,
        share_base=args.share_base or "",
        provenance=provenance,
        append=args.append,
    )
    sys.stdout.write(describe(page) + "\n")
    sys.stdout.write(f"{count} draft row(s):\n{summary(rows)}\n")
    sys.stdout.write(f"wrote {out.as_posix()} (DRAFT: review every row against the original)\n")
    return 0 if rows else 1
