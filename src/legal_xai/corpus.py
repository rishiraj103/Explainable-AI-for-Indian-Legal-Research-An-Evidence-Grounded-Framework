"""Conservative, deterministic preparation of judgment text for evidence use.

Raw PDFs are never altered.  This module operates only on extracted text and
returns page-bound chunks with enough metadata to trace every passage back to
its source judgment and page.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


_MARGINAL_MARKER = re.compile(r"^[A-H]$")
_PAGE_NUMBER = re.compile(r"^\d{1,6}$")
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+(?=[A-Z\[])")
_REPORT_HEADER = re.compile(r"^(?:[A-H]\s+)?SUPREME COURT REPORTS\b", re.IGNORECASE)


@dataclass(frozen=True)
class TextChunk:
    """A cleaned passage with a locator relative to its original PDF page."""

    text: str
    page_number: int
    chunk_number: int
    start_char: int
    end_char: int


def _normalise_line(line: str) -> str:
    """Normalise a line for exact repeated-header detection only."""

    line = line.strip()
    line = _REPORT_HEADER.sub("", line)
    return re.sub(r"\s+", " ", line).casefold().strip()


def repeated_page_furniture(raw_pages: list[str], minimum_repetitions: int = 3) -> set[str]:
    """Return first/last-page lines repeated within one judgment.

    Headers and running case titles occur at page edges.  Restricting removal to
    lines repeated at least three times within the *same* PDF avoids applying a
    global stop-list to substantive legal text.
    """

    occurrences: dict[str, set[int]] = {}
    for page_number, raw_page in enumerate(raw_pages):
        lines = [line.strip() for line in raw_page.splitlines() if line.strip()]
        edge_lines = lines[:4] + lines[-4:]
        for line in edge_lines:
            if _MARGINAL_MARKER.fullmatch(line) or _PAGE_NUMBER.fullmatch(line):
                continue
            normalised = _normalise_line(line)
            if normalised:
                occurrences.setdefault(normalised, set()).add(page_number)
    return {line for line, pages in occurrences.items() if len(pages) >= minimum_repetitions}


def clean_page_text(raw_text: str, repeated_furniture: set[str] | None = None) -> str:
    """Remove extraction clutter without paraphrasing legal content.

    The rules intentionally remove only isolated margin letters, standalone page
    numbers, replacement glyphs, line-wrap hyphens, and excess whitespace.
    """

    lines: list[str] = []
    repeated_furniture = repeated_furniture or set()
    for line in raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        stripped = line.strip()
        if (
            not stripped
            or _MARGINAL_MARKER.fullmatch(stripped)
            or _PAGE_NUMBER.fullmatch(stripped)
            or _REPORT_HEADER.match(stripped)
            or _normalise_line(stripped) in repeated_furniture
        ):
            continue
        lines.append(stripped.replace("\ufffd", " "))

    joined = "\n".join(lines)
    joined = re.sub(r"(?<=[A-Za-z])-[ \t]*\n[ \t]*(?=[a-z])", "", joined)
    joined = re.sub(r"[ \t]*\n[ \t]*", " ", joined)
    return re.sub(r"\s+", " ", joined).strip()


def is_non_evidentiary_chunk(text: str) -> bool:
    """Identify short fragments and counsel-name lists, not evidence passages."""

    words = text.split()
    if len(words) <= 3:
        outcome = re.search(
            r"\b(?:appeal|petition|application|case)\s+(?:is\s+)?(?:dismissed|allowed|granted|disposed)\b",
            text,
            re.IGNORECASE,
        )
        return outcome is None
    has_many_name_separators = text.count(",") >= 3
    looks_like_names = sum(word[:1].isupper() for word in words) >= max(4, len(words) // 3)
    ends_like_counsel_listing = text.rstrip().endswith(("Adv.", "Advs."))
    return has_many_name_separators and looks_like_names and (
        ends_like_counsel_listing or len(words) <= 50
    )


def chunk_page_text(
    cleaned_text: str,
    page_number: int,
    *,
    max_words: int = 220,
    max_sentences: int = 4,
) -> list[TextChunk]:
    """Split one cleaned page into short, sentence-aligned evidence passages."""

    if not cleaned_text:
        return []
    if max_words < 1 or max_sentences < 1:
        raise ValueError("max_words and max_sentences must be positive")

    sentences = [part.strip() for part in _SENTENCE_BREAK.split(cleaned_text) if part.strip()]
    if not sentences:
        sentences = [cleaned_text]

    chunks: list[TextChunk] = []
    current: list[str] = []
    current_words = 0
    search_from = 0
    for sentence in sentences:
        words = len(sentence.split())
        if current and (len(current) >= max_sentences or current_words + words > max_words):
            text = " ".join(current)
            start = cleaned_text.find(text, search_from)
            chunks.append(TextChunk(text, page_number, len(chunks) + 1, start, start + len(text)))
            search_from = start + len(text)
            current, current_words = [], 0
        current.append(sentence)
        current_words += words

    if current:
        text = " ".join(current)
        start = cleaned_text.find(text, search_from)
        chunks.append(TextChunk(text, page_number, len(chunks) + 1, start, start + len(text)))
    return chunks
