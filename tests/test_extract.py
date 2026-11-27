"""Extraction helpers: text-PDF and HTML drafts, page rendering, label guesses (no network)."""

from pathlib import Path

import pytest

from sondaje.cli import main
from sondaje.ingest.csvio import read_rows, write_rows
from sondaje.ingest.drafts import (
    DraftRow,
    EntityMatcher,
    EntityName,
    fold,
    guess_type,
    matcher_for,
    write_draft,
)
from sondaje.ingest.extract_html import extract_html, parse_html, published_times
from sondaje.ingest.extract_pdf import (
    ExtractError,
    Word,
    extract_pdf,
    page_chart,
    page_lines,
    parse_pages,
    render_pdf,
    text_layer_problem,
)
from sondaje.schema import ARCHIVE_MANIFEST, POLL_RESULTS

MATCHER = EntityMatcher(
    [
        EntityName("george-simion", "candidate", "george simion"),
        EntityName("nicusor-dan", "candidate", "nicusor dan"),
        EntityName("psd", "party", "psd"),
        EntityName("aur", "party", "aur"),
    ]
)


def text_pdf(items: list[tuple[float, float, str]], width: int = 600, height: int = 400) -> bytes:
    """A one-page PDF whose text layer has ``text`` at (x, y) for each item (Helvetica 10)."""
    ops = []
    for x, y, text in items:
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        ops.append(f"BT /F1 10 Tf {x} {y} Td ({escaped}) Tj ET")
    stream = "\n".join(ops).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
        "/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>".encode(),
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(out)


COLUMN_CHART = [
    (100, 300, "38.9%"),
    (200, 250, "31.3%"),
    (300, 350, "1.4%"),
    (80, 100, "George-SIMION"),
    (190, 100, "Nicusor DAN"),
    (290, 100, "Anulez Votul"),
    (40, 30, "TITLU RAPORT"),
]


@pytest.fixture
def chart_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "chart.pdf"
    path.write_bytes(text_pdf(COLUMN_CHART))
    return path


def test_lines_mode_reads_label_value_lines() -> None:
    text = (
        "La alegerile parlamentare cu ce partid veti vota?\n"
        "Partidul Social Democrat (PSD) 32%\n"
        "Altul (sub 1% fiecare) 3%\n"
        "Cristian Terhes ( PNCR) 4% VOTAT\n"
        "Alt candidat <1%\n"
        "Intentie: 31,5%\n"
        "12%\n"
    )
    rows = page_lines(text, 4)
    assert [(r.label, r.value, r.qualifier) for r in rows] == [
        ("Partidul Social Democrat (PSD)", "32", ""),
        ("Altul (sub 1% fiecare)", "3", ""),
        ("Cristian Terhes ( PNCR)", "4", ""),
        ("Alt candidat", "1", "lt"),
        ("Intentie", "31.5", ""),
    ]
    assert "VOTAT" in rows[2].where


def test_chart_mode_pairs_columns_by_x() -> None:
    words = [
        Word("38.9%", 102, 147, 184, 196),
        Word("31.3%", 248, 293, 235, 247),
        Word("<", 390, 395, 432, 444),
        Word("1%", 396, 420, 432, 444),
        Word("George-SIMION", 84, 170, 469, 481),
        Word("Nicușor", 236, 277, 470, 482),
        Word("DAN", 280, 305, 470, 482),
        Word("Alt", 380, 395, 469, 481),
        Word("candidat", 398, 440, 469, 481),
        Word("TITLU", 835, 860, 527, 539),
    ]
    rows = page_chart(words, 3)
    assert [(r.label, r.value, r.qualifier) for r in rows] == [
        ("George-SIMION", "38.9", ""),
        ("Nicușor DAN", "31.3", ""),
        ("Alt candidat", "1", "lt"),
    ]
    assert all("CHECK" not in r.where for r in rows)


def test_chart_mode_pairs_horizontal_bars_by_y() -> None:
    words = [
        Word("PSD", 10, 30, 100, 110),
        Word("AUR", 10, 30, 130, 140),
        Word("22%", 300, 320, 100, 110),
        Word("18%", 260, 280, 131, 141),
    ]
    rows = page_chart(words, 1)
    assert [(r.label, r.value) for r in rows] == [("PSD", "22"), ("AUR", "18")]


def test_chart_mode_flags_count_mismatch() -> None:
    words = [
        Word("10%", 100, 120, 50, 60),
        Word("20%", 200, 220, 50, 60),
        Word("A", 100, 110, 100, 110),
    ]
    rows = page_chart(words, 1)
    assert len(rows) == 2
    assert all("CHECK: 2 values, 1 labels" in r.where for r in rows)


def test_extract_pdf_auto_uses_chart_for_separate_runs(chart_pdf: Path) -> None:
    rows = extract_pdf(chart_pdf)
    assert [(r.label, r.value) for r in rows] == [
        ("George-SIMION", "38.9"),
        ("Nicusor DAN", "31.3"),
        ("Anulez Votul", "1.4"),
    ]


def test_extract_pdf_lines_and_page_errors(tmp_path: Path) -> None:
    path = tmp_path / "lines.pdf"
    path.write_bytes(text_pdf([(50, 300, "PSD 32%"), (50, 280, "AUR 15%")]))
    assert [(r.label, r.value) for r in extract_pdf(path, "1", "lines")] == [
        ("PSD", "32"),
        ("AUR", "15"),
    ]
    with pytest.raises(ExtractError):
        extract_pdf(path, "2")
    with pytest.raises(ExtractError):
        extract_pdf(path, mode="ocr")
    not_pdf = tmp_path / "x.pdf"
    not_pdf.write_bytes(b"hello")
    with pytest.raises(ExtractError):
        extract_pdf(not_pdf)


def spaced_letters_pdf() -> bytes:
    """A text layer like the Sociopol PDFs: every character is a separate text run."""
    text = "Intentia de vot pentru partidele politice in luna mai 2025 PSD 32% AUR 15%"
    items = [(10 + 15 * i, 300 - 20 * (n // 38), ch) for n, ch in enumerate(text) for i in [n % 38]]
    return text_pdf([item for item in items if item[2] != " "], width=600, height=400)


def test_text_layer_problem_detects_spaced_letters_and_missing_text(tmp_path: Path) -> None:
    spaced = tmp_path / "spaced.pdf"
    spaced.write_bytes(spaced_letters_pdf())
    assert "unreadable" in (text_layer_problem(spaced) or "")
    blank = tmp_path / "blank.pdf"
    blank.write_bytes(text_pdf([]))
    assert "no text layer" in (text_layer_problem(blank) or "")
    good = tmp_path / "good.pdf"
    good.write_bytes(text_pdf([(50, 300, "Intentia de vot pentru partidele politice " * 2)]))
    assert text_layer_problem(good) is None
    with pytest.raises(ExtractError):
        text_layer_problem(spaced, "9")


def test_cli_extract_pdf_explains_an_unreadable_text_layer(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spaced = tmp_path / "spaced.pdf"
    spaced.write_bytes(spaced_letters_pdf())
    out = tmp_path / "draft.csv"
    assert main(["extract-pdf", str(spaced), "--mode", "lines", "--out", str(out)]) == 0
    err = capsys.readouterr().err
    assert "probably wrong" in err and "unreadable" in err
    assert "render-pdf" in err and "double entry" in err
    assert main(["extract-pdf", str(spaced), "--out", str(out)]) == 1
    assert "no rows found: the text layer is unreadable" in capsys.readouterr().err
    blank = tmp_path / "blank.pdf"
    blank.write_bytes(text_pdf([]))
    assert main(["extract-pdf", str(blank), "--out", str(out)]) == 1
    assert "no text layer" in capsys.readouterr().err
    good = tmp_path / "good.pdf"
    good.write_bytes(text_pdf([(50, 300, "Intentia de vot pentru partidele politice " * 2)]))
    assert main(["extract-pdf", str(good), "--out", str(out)]) == 1
    assert "no rows found; try another --mode" in capsys.readouterr().err


def test_parse_pages() -> None:
    assert parse_pages("3,5-6", 8) == [3, 5, 6]
    assert parse_pages(None, 2) == [1, 2]
    for bad in ("0", "2-1", "x", "9"):
        with pytest.raises(ExtractError):
            parse_pages(bad, 8)


def test_render_pdf(chart_pdf: Path, tmp_path: Path) -> None:
    [png] = render_pdf(chart_pdf, tmp_path / "render", "1", 50)
    assert png.name == "chart-p01.png"
    assert png.read_bytes().startswith(b"\x89PNG")


def test_fold_and_guesses() -> None:
    assert fold("  Nicuşor-DAN ") == "nicusor dan"
    assert fold("Țară Ăîâ") == "tara aia"
    assert guess_type("George-SIMION", MATCHER) == ("candidate", "george-simion")
    assert guess_type("Partidul Social Democrat (PSD)", MATCHER) == ("party", "psd")
    expected = {
        "Nu ştiu / Nu m-am hotărât": "undecided",
        "NS/NR": "undecided_or_non_response",
        "Nu m-aş duce la vot": "would_not_vote",
        "Anulez Votul": "blank_or_invalid",
        "Vot nul / alb": "blank_or_invalid",
        "NR": "non_response",
        "Altul (sub 1% fiecare)": "other",
        "Alți candidați": "other",
        "Niciunul": "none",
        "Ceva nou": "",
    }
    for label, option_type in expected.items():
        assert guess_type(label, MATCHER)[0] == option_type, label


def test_entity_matcher_keeps_original_positions() -> None:
    text = "Rezultat: 53% pentru George Simion şi 47% pentru Nicuşor  Dan."
    found = MATCHER.find_all(text)
    assert [(text[s:e], n.entity_id) for s, e, n in found] == [
        ("George Simion", "george-simion"),
        ("Nicuşor  Dan", "nicusor-dan"),
    ]


def test_matcher_for_filters_by_election(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1] / "data"
    presidential = matcher_for(root, "pres-2025-r2")
    assert guess_type("PSD", presidential) == ("", "")
    assert guess_type("Nicușor DAN", presidential) == ("candidate", "nicusor-dan")
    assert guess_type("PSD", matcher_for(root, "parl-2024-cd")) == ("party", "psd")
    with pytest.raises(FileNotFoundError):
        matcher_for(root, "pres-2099-r1")


ARTICLE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Sondaj: George Simion 53% &ndash; Nicuşor Dan 47%</title>
<meta property="article:published_time" content="2099-05-12T18:13:41+00:00">
<script type="application/ld+json">{"datePublished": "2099-05-12T18:13:41Z"}</script>
<script>var x = "99%";</script><style>.a{width:50%}</style></head>
<body><svg><title>icon 10%</title></svg>
<p>Directorul a spus că fotografia momentului arată 53% pentru George Simion şi 47% pentru
Nicuşor Dan.</p><p>Prezența ar fi de 63%, iar diferența de 6 procente.</p>
<img src="https://example.org/grafic.jpg" alt="Grafic sondaj">
</body></html>"""

TABLE_PAGE = """<html><body><table>
<tr><th>Partid</th><th>%</th></tr>
<tr><td>PSD</td><td>30,5%</td></tr>
<tr><td>AUR</td><td>&lt;1%</td></tr>
<tr><td>Alt partid</td><td>4%</td></tr>
</table></body></html>"""


def test_parse_html_metadata_and_blocks() -> None:
    page = parse_html(ARTICLE.encode("utf-8"))
    assert page.title == "Sondaj: George Simion 53% \u2013 Nicuşor Dan 47%"
    assert published_times(page) == ["2099-05-12T18:13:41+00:00", "2099-05-12T18:13:41Z"]
    assert page.images == [("https://example.org/grafic.jpg", "Grafic sondaj")]
    assert not any("99%" in b or "50%" in b or "icon" in b for b in page.blocks)


def test_html_text_mode_guesses_labels_next_to_values() -> None:
    _, rows = extract_html(ARTICLE.encode("utf-8"), "auto", MATCHER)
    assert [(r.label, r.value, r.entity_id) for r in rows] == [
        ("George Simion", "53", "george-simion"),
        ("Nicuşor Dan", "47", "nicusor-dan"),
        ("", "63", ""),
        ("", "6", ""),
    ]
    assert rows[0].where.startswith("block 1: Directorul")


def test_html_tables_mode() -> None:
    _, rows = extract_html(TABLE_PAGE.encode("utf-8"), "auto", MATCHER)
    assert [(r.label, r.value, r.qualifier, r.option_type) for r in rows] == [
        ("PSD", "30.5", "", "party"),
        ("AUR", "1", "lt", "party"),
        ("Alt partid", "4", "", "other"),
    ]
    with pytest.raises(ExtractError):
        extract_html(b"", "ocr", None)


LINES_PAGE = """<html><body><p>Intenția de vot:</p>
<p>George Simion - 50%</p><p>Nicuşor Dan \u2013 45,5 %</p><p>Nu știu - sub 1%</p>
<p>Altul - 3.5%</p>
<p>PSD - 30%, AUR - 20%; Altele - 5%</p></body></html>"""


def test_html_text_mode_reads_name_dash_value_lines() -> None:
    _, rows = extract_html(LINES_PAGE.encode("utf-8"), "text", MATCHER)
    assert [(r.label, r.value, r.qualifier, r.option_type, r.entity_id) for r in rows] == [
        ("George Simion", "50", "", "candidate", "george-simion"),
        ("Nicuşor Dan", "45.5", "", "candidate", "nicusor-dan"),
        ("Nu știu", "1", "lt", "undecided", ""),
        ("Altul", "3.5", "", "other", ""),
        ("PSD", "30", "", "party", "psd"),
        ("AUR", "20", "", "party", "aur"),
        ("Altele", "5", "", "other", ""),
    ]
    assert rows[0].where.startswith("block 2: George Simion - 50%")


def test_html_dash_after_a_long_sentence_is_not_taken_as_a_label() -> None:
    page = "<p>Directorul institutului a explicat în detaliu că PSD a obținut - 30% din voturi.</p>"
    _, rows = extract_html(page.encode("utf-8"), "text", MATCHER)
    assert [(r.label, r.value) for r in rows] == [("", "30")]


def test_write_draft_appends_with_restarting_order(tmp_path: Path) -> None:
    out = tmp_path / "draft.csv"
    write_draft(out, [DraftRow("PSD", "30", where="p.1")], poll_id="p", share_base="x")
    write_draft(out, [DraftRow("AUR", "20")], share_base="y", append=True)
    rows = read_rows(out, POLL_RESULTS)
    assert [(r["option_label"], r["option_order"], r["share_base"]) for r in rows] == [
        ("PSD", "1", "x"),
        ("AUR", "1", "y"),
    ]
    assert rows[0]["notes"] == "DRAFT p.1"


def test_cli_extract_pdf_from_an_archived_document(
    chart_pdf: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = tmp_path / "data"
    raw = data / "raw/polls/exemplar/exemplar-doc-001.pdf"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(chart_pdf.read_bytes())
    registry = Path(__file__).resolve().parents[1] / "data/registry"
    (data / "registry").mkdir()
    for name in ("entities.csv", "elections.csv"):
        (data / "registry" / name).write_bytes((registry / name).read_bytes())
    write_rows(
        data / "polls/exemplar/archive_manifest.csv",
        ARCHIVE_MANIFEST,
        [
            {
                "document_id": "exemplar-doc-001",
                "format": "pdf_text",
                "archive_url": "https://web.archive.org/web/20990101000000/https://x.org/r.pdf",
                "sha256": "0" * 64,
                "raw_path": "data/raw/polls/exemplar/exemplar-doc-001.pdf",
                "source_url": "https://x.org/r.pdf",
                "source_type": "pollster",
                "retrieved_at": "2099-01-02",
            }
        ],
    )
    out = tmp_path / "draft.csv"
    args = ["extract-pdf", "--pollster", "exemplar", "--document", "exemplar-doc-001"]
    args += ["--data-dir", str(data), "--election", "pres-2025-r2", "--out", str(out)]
    args += ["--poll-id", "exemplar-pres-2025-r2-20250506", "--share-base", "all_respondents"]
    assert main(args) == 0
    rows = read_rows(out, POLL_RESULTS)
    assert rows[0]["entity_id"] == "george-simion"
    assert rows[0]["source_url"] == "https://x.org/r.pdf"
    assert rows[2]["option_type"] == "blank_or_invalid"
    assert "DRAFT" in capsys.readouterr().out
    assert main(["extract-pdf", "--document", "exemplar-doc-001"]) == 1
    assert main(["render-pdf", str(chart_pdf), "--out-dir", str(tmp_path / "r")]) == 0
