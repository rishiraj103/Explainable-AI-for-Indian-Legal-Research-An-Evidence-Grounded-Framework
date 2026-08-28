"""Frozen, reusable pre-decision input extraction for ILDC experiments.

ILDC Single exposes a full judgment in its ``text`` field rather than a
gold-standard facts annotation.  This module deliberately keeps only text
before the earliest unambiguous dispositive cue or closing section heading.
It is shared by E1 and the later E2 experiment so model comparisons use the
same input preparation rule.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any


@dataclass(frozen=True)
class FactsExtractionRule:
    """Versioned patterns and parameters that define the frozen input policy."""

    version: str
    section_header_patterns: tuple[str, ...]
    dispositive_patterns: tuple[str, ...]
    minimum_sentence_aligned_chars: int
    fallback_retained_fraction: float
    minimum_retained_fraction: float
    minimum_facts_words: int


@dataclass(frozen=True)
class FactsExtractionResult:
    """Pre-decision text plus an audit trail explaining the chosen boundary."""

    text: str
    boundary_char: int | None
    boundary_reason: str
    source_char_count: int
    retained_char_count: int


def load_facts_extraction_rule(path: str | Path) -> FactsExtractionRule:
    """Load the experiment's frozen facts-extraction rule from JSON."""

    payload: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    return FactsExtractionRule(
        version=str(payload["version"]),
        section_header_patterns=tuple(payload["section_header_patterns"]),
        dispositive_patterns=tuple(payload["dispositive_patterns"]),
        minimum_sentence_aligned_chars=int(payload["minimum_sentence_aligned_chars"]),
        fallback_retained_fraction=float(payload["fallback_retained_fraction"]),
        minimum_retained_fraction=float(payload["minimum_retained_fraction"]),
        minimum_facts_words=int(payload["minimum_facts_words"]),
    )


def _earliest_boundary(text: str, rule: FactsExtractionRule) -> tuple[int | None, str]:
    candidates: list[tuple[int, str]] = []
    for pattern in rule.section_header_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            candidates.append((match.start(), "section_header"))
    for pattern in rule.dispositive_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            candidates.append((match.start(), "dispositive_cue"))
    if not candidates:
        return None, "no_boundary_found"
    return min(candidates, key=lambda item: item[0])


def _sentence_aligned_boundary(text: str, boundary: int, minimum_chars: int) -> int:
    """Back up to a sentence end so the retained text never ends mid-sentence."""

    prefix = text[:boundary]
    sentence_ends = list(re.finditer(r"[.!?](?:[\"')\]\u201d\u2019]+)?\s*", prefix))
    if sentence_ends and sentence_ends[-1].end() >= minimum_chars:
        return sentence_ends[-1].end()
    return boundary


def extract_case_facts(text: str | None, rule: FactsExtractionRule) -> FactsExtractionResult:
    """Extract a conservative pre-decision input slice using a frozen rule.

    The earliest recognized closing-section header or outcome/dispositive cue
    ends the input, subject to a frozen maximum retained fraction. This cap
    prevents a late cue from preserving almost an entire judgment. If possible,
    each boundary moves back to the preceding sentence end.
    """

    source = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not source:
        return FactsExtractionResult("", None, "empty_input", 0, 0)

    boundary, reason = _earliest_boundary(source, rule)
    positional_cap = round(len(source) * rule.fallback_retained_fraction)
    if boundary is None or boundary > positional_cap:
        boundary = positional_cap
        reason = "positional_cap"

    aligned = _sentence_aligned_boundary(source, boundary, rule.minimum_sentence_aligned_chars)
    retained = source[:aligned].rstrip()
    return FactsExtractionResult(retained, aligned, reason, len(source), len(retained))


def find_outcome_cues(text: str, rule: FactsExtractionRule) -> list[str]:
    """Return matched dispositive phrases for validation; never alters text."""

    matches: list[str] = []
    for pattern in rule.dispositive_patterns:
        matches.extend(match.group(0) for match in re.finditer(pattern, text, flags=re.IGNORECASE))
    return sorted(set(matches), key=str.casefold)


def facts_input_is_eligible(result: FactsExtractionResult, rule: FactsExtractionRule) -> bool:
    """Return whether an extracted slice has enough pre-decision material for E1/E2.

    A very early disposition cue can leave only a caption or counsel list. Such
    rows are excluded rather than allowing a tiny, non-factual fragment into a
    supposedly facts-only experiment. The caller must record excluded IDs.
    """

    if result.source_char_count == 0:
        return False
    retained_fraction = result.retained_char_count / result.source_char_count
    return (
        retained_fraction >= rule.minimum_retained_fraction
        and len(result.text.split()) >= rule.minimum_facts_words
    )
