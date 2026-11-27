"""Extraction drafts: label/value pairs written as a draft ``poll_results.csv`` (T-011).

Implements the "extract" step of docs/POLL_INGESTION.md. A draft is **never** canonical
data: it is written under ``build/`` (git-ignored), completed and corrected by a person
against the archived original, and only then copied into ``data/polls/<pollster_id>/``.

Values are kept exactly as printed, with the one mechanical change DATA_MODEL.md §1 allows
(decimal comma → decimal point, ``%`` dropped). Labels are kept verbatim. ``option_type``
and ``entity_id`` are *guesses* (registry names, a few Romanian non-vote phrases); the
review step confirms or replaces every guess.
"""

import re
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from sondaje.ingest.csvio import read_rows, write_rows
from sondaje.schema import ARCHIVE_MANIFEST, ELECTIONS, ENTITIES, POLL_RESULTS
from sondaje.validation.rules_elections import CONTESTANT_TYPES

VALUE_TOKEN_RE = re.compile(r"^(?P<lt><)?(?P<value>\d{1,3}(?:[.,]\d+)?)%$")
"""A value printed as one word, e.g. ``38.9%``, ``31,5%``, ``<1%``."""

NON_VOTE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bns\s*/\s*nr\b", "undecided_or_non_response"),
    (r"\bnu\s+stiu\b.*\bnu\s+raspun", "undecided_or_non_response"),
    (r"\bnu\s+(?:m\s*as\s+duce|merg|voi\s+merge|voi\s+vota|votez|as\s+vota)\b", "would_not_vote"),
    (r"\b(?:anulez|anula|vot\s+(?:nul|alb|anulat)|nul\s*/\s*alb)\b", "blank_or_invalid"),
    (r"\bnu\s+stiu\b|\bnehotarat|\bindecis|\bnu\s+m\s*am\s+hotarat", "undecided"),
    (r"^\s*nr\s*$|\bnu\s+raspund|\brefuz", "non_response"),
    (r"\bniciun(?:ul|a)\b", "none"),
    (r"\balt(?:ul|ii|i|e|ele|a)?\b|\bal[tţț]i\s+candida", "other"),
)
"""Romanian phrases → ``option_type`` guesses (matched on folded text, first match wins)."""


def _fold_char(ch: str) -> str:
    if ch in "\u2010\u2011\u2012\u2013\u2014\u2015-":
        return " "
    if ch.isspace():
        return " "
    base = "".join(c for c in unicodedata.normalize("NFKD", ch) if not unicodedata.combining(c))
    base = (base[:1] or ch).lower()
    return "i" if base == "\u0131" else base


def fold_aligned(text: str) -> str:
    """:func:`fold` without collapsing spaces: one output character per input character, so
    positions in the result are positions in ``text``."""
    return "".join(_fold_char(ch) for ch in text)


def fold(text: str) -> str:
    """Lowercase, without diacritics (ș/ş → s, ț/ţ → t, ă/â → a, î → i), hyphens as spaces."""
    return " ".join(fold_aligned(text).split())


def normalize_value(raw: str) -> str:
    """The DATA_MODEL §1 mechanical change: ``31,5`` → ``31.5`` (digits kept as printed)."""
    return raw.replace(",", ".")


@dataclass(frozen=True)
class EntityName:
    entity_id: str
    entity_type: str
    folded: str


class EntityMatcher:
    """Finds registry entities (``name`` and ``short_name``) in text, ignoring case and
    diacritics. Used only to *guess* ``entity_id``; the reviewer confirms every guess."""

    def __init__(self, names: Iterable[EntityName]) -> None:
        self.names = sorted(names, key=lambda n: -len(n.folded))

    @classmethod
    def from_registry(
        cls, data_dir: Path, entity_types: Sequence[str] | None = None
    ) -> "EntityMatcher":
        rows = read_rows(data_dir / "registry" / ENTITIES.filename, ENTITIES)
        names = []
        for row in rows:
            if entity_types is not None and row["entity_type"] not in entity_types:
                continue
            for value in {row["name"], row["short_name"]}:
                folded = fold(value)
                if len(folded) >= 3:
                    names.append(EntityName(row["entity_id"], row["entity_type"], folded))
        return cls(names)

    def _pattern(self, name: EntityName) -> re.Pattern[str]:
        words = r"\s+".join(re.escape(word) for word in name.folded.split())
        return re.compile(rf"(?<![a-z0-9]){words}(?![a-z0-9])")

    def find_all(self, text: str) -> list[tuple[int, int, EntityName]]:
        """Non-overlapping matches as positions in ``text`` (longest names first)."""
        folded = fold_aligned(text)
        taken: list[tuple[int, int, EntityName]] = []
        for name in self.names:
            for match in self._pattern(name).finditer(folded):
                start, end = match.span()
                if all(end <= s or start >= e for s, e, _ in taken):
                    taken.append((start, end, name))
        return sorted(taken, key=lambda item: item[0])

    def match_label(self, label: str) -> EntityName | None:
        """The entity whose name is the whole label, or else the longest one inside it."""
        folded = fold(label)
        exact = [n for n in self.names if n.folded == folded]
        if exact:
            return exact[0]
        found = self.find_all(label)
        return max(found, key=lambda item: item[1] - item[0])[2] if found else None


def matcher_for(data_dir: Path, election_id: str | None = None) -> EntityMatcher:
    """An :class:`EntityMatcher` over the registry; with an election, only the entity types
    that can be contestants in it (candidates for a presidential election, R-52)."""
    types: Sequence[str] | None = None
    if election_id:
        elections = read_rows(data_dir / "registry" / ELECTIONS.filename, ELECTIONS)
        election = next((r for r in elections if r["election_id"] == election_id), None)
        if election is None:
            raise FileNotFoundError(f"election {election_id!r} is not in the registry")
        types = CONTESTANT_TYPES.get(election["election_type"])
    return EntityMatcher.from_registry(data_dir, types)


def guess_type(label: str, matcher: EntityMatcher | None) -> tuple[str, str]:
    """(``option_type``, ``entity_id``) guesses for a label; empty strings when unsure."""
    folded = fold(label)
    if matcher is not None:
        entity = matcher.match_label(label)
        if entity is not None:
            return entity.entity_type, entity.entity_id
    for pattern, option_type in NON_VOTE_PATTERNS:
        if re.search(pattern, folded):
            return option_type, ""
    return "", ""


@dataclass
class DraftRow:
    """One extracted label/value pair and where it was found."""

    label: str
    value: str
    qualifier: str = ""
    where: str = ""
    option_type: str = ""
    entity_id: str = ""


@dataclass(frozen=True)
class Provenance:
    source_url: str = ""
    source_type: str = ""
    retrieved_at: str = ""


def document_source(data_dir: Path, pollster_id: str, document_id: str) -> tuple[Path, Provenance]:
    """The raw file and provenance of an archived document (``archive_manifest.csv``)."""
    manifest = data_dir / "polls" / pollster_id / ARCHIVE_MANIFEST.filename
    for row in read_rows(manifest, ARCHIVE_MANIFEST):
        if row["document_id"] == document_id:
            if not row["raw_path"]:
                raise FileNotFoundError(f"{document_id} has no raw_path in {manifest.as_posix()}")
            relative = Path(row["raw_path"]).relative_to("data")
            provenance = Provenance(row["source_url"], row["source_type"], row["retrieved_at"])
            return data_dir / relative, provenance
    raise FileNotFoundError(f"{document_id} is not in {manifest.as_posix()}")


def draft_records(
    rows: Sequence[DraftRow],
    poll_id: str = "",
    share_base: str = "",
    provenance: Provenance | None = None,
    start: int = 1,
) -> list[dict[str, str]]:
    provenance = provenance or Provenance()
    return [
        {
            "poll_id": poll_id,
            "share_base": share_base,
            "option_order": str(order),
            "option_label": row.label,
            "option_type": row.option_type,
            "entity_id": row.entity_id,
            "share_raw": row.value,
            "share_qualifier": row.qualifier,
            "source_url": provenance.source_url,
            "source_type": provenance.source_type,
            "retrieved_at": provenance.retrieved_at,
            "verified": "",
            "notes": f"DRAFT {row.where}".strip(),
        }
        for order, row in enumerate(rows, start=start)
    ]


def write_draft(
    path: Path,
    rows: Sequence[DraftRow],
    *,
    poll_id: str = "",
    share_base: str = "",
    provenance: Provenance | None = None,
    append: bool = False,
) -> int:
    """Write (or append to) a draft ``poll_results.csv``; returns the number of rows written.

    ``option_order`` restarts at 1 for each call, so run once per (poll, base).
    """
    existing = read_rows(path, POLL_RESULTS) if append else []
    records = draft_records(rows, poll_id, share_base, provenance)
    write_rows(path, POLL_RESULTS, [*existing, *records])
    return len(records)


def summary(rows: Sequence[DraftRow]) -> str:
    lines = []
    for order, row in enumerate(rows, start=1):
        value = ("<" if row.qualifier == "lt" else "") + row.value
        guess = row.entity_id or row.option_type or "?"
        lines.append(f"  {order:>2}. {row.label!r:<45} {value:>7}  [{guess}]  {row.where}")
    return "\n".join(lines)
