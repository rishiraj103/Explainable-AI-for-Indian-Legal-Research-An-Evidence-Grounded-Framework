"""Reusable evidence gate for ILDC-to-eCourts document identity mappings.

ILDC identifiers may resemble eCourts ``YYYY INSC N`` identifiers, but the
numeric suffixes are not a shared identity namespace.  A syntactic ID match is
therefore only a candidate hint.  Any accepted mapping must be checked against
both eCourts title/party metadata and direct document-text overlap.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


STOP_WORDS = frozenset({
    "and", "anr", "another", "appeal", "appeals", "court", "etc", "for", "from", "has", "have", "in",
    "judgment", "law", "ltd", "limited", "of", "or", "ors", "others", "state", "the", "this", "to",
    "union", "v", "versus", "with",
})
DEFAULT_MIN_SHARED_TERMS = 2
DEFAULT_MIN_IDENTITY_COVERAGE = 0.8
DEFAULT_MIN_DIRECT_SIX_TOKEN_PHRASES = 100


def normalized_tokens(value: object) -> set[str]:
    """Return distinctive case-identity tokens from text or metadata."""
    text = "" if value is None else str(value).casefold()
    return {
        token for token in re.findall(r"[a-z][a-z0-9]{2,}", text)
        if token not in STOP_WORDS
    }


def document_tokens(value: object) -> list[str]:
    """Return stable tokens for direct phrase fingerprints."""
    return re.findall(r"[a-z]{3,}", ("" if value is None else str(value)).casefold())


def six_token_phrase_set(value: object, *, width: int = 6) -> set[str]:
    """Create reusable direct-content fingerprints for one document."""
    tokens = document_tokens(value)
    return {" ".join(tokens[index:index + width]) for index in range(len(tokens) - width + 1)}


def shared_phrase_count_from_query_set(
    query_phrases: set[str],
    source_text: object,
    *,
    width: int = 6,
    stop_at: int | None = None,
) -> tuple[int, str | None]:
    """Count source fingerprints against a precomputed query fingerprint set."""
    source = document_tokens(source_text)
    if not query_phrases or len(source) < width:
        return 0, None
    count = 0
    first: str | None = None
    for index in range(len(source) - width + 1):
        phrase = " ".join(source[index:index + width])
        if phrase not in query_phrases:
            continue
        count += 1
        first = first or phrase
        if stop_at is not None and count >= stop_at:
            break
    return count, first


def title_party_tokens(title: object, petitioner: object, respondent: object) -> set[str]:
    """Build the reusable metadata identity signature for an eCourts source."""
    return normalized_tokens(" ".join(str(value or "") for value in (title, petitioner, respondent)))


def title_party_alignment(
    ildc_text: object,
    title: object,
    petitioner: object,
    respondent: object,
    *,
    min_shared_terms: int = DEFAULT_MIN_SHARED_TERMS,
    min_coverage: float = DEFAULT_MIN_IDENTITY_COVERAGE,
) -> tuple[bool, tuple[str, ...], float]:
    """Check the title/party signal without treating an ID as an identity proof."""
    source_terms = title_party_tokens(title, petitioner, respondent)
    shared = normalized_tokens(ildc_text) & source_terms
    coverage = len(shared) / len(source_terms) if source_terms else 0.0
    passed = len(shared) >= min_shared_terms and coverage >= min_coverage
    return passed, tuple(sorted(shared)), coverage


def shared_six_token_phrases(
    ildc_text: object,
    source_text: object,
    *,
    width: int = 6,
    stop_at: int | None = None,
) -> tuple[int, str | None]:
    """Count direct contiguous phrase fingerprints shared by two documents.

    ``stop_at`` keeps full-corpus scans bounded while still distinguishing an
    aligned document from a collision at the configured gate threshold.
    """
    return shared_phrase_count_from_query_set(
        six_token_phrase_set(ildc_text, width=width), source_text, width=width, stop_at=stop_at,
    )


@dataclass(frozen=True)
class ContentAlignment:
    """Auditable decision for a candidate ILDC/eCourts document pair."""

    title_party_passed: bool
    shared_identity_terms: tuple[str, ...]
    identity_coverage: float
    direct_phrase_count: int
    example_shared_phrase: str | None
    direct_content_passed: bool
    passed: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "title_party_passed": self.title_party_passed,
            "shared_identity_terms": list(self.shared_identity_terms),
            "identity_coverage": self.identity_coverage,
            "direct_phrase_count": self.direct_phrase_count,
            "example_shared_phrase": self.example_shared_phrase,
            "direct_content_passed": self.direct_content_passed,
            "passed": self.passed,
        }


def assess_content_alignment(
    *,
    ildc_text: object,
    source_text: object,
    title: object,
    petitioner: object,
    respondent: object,
    min_shared_terms: int = DEFAULT_MIN_SHARED_TERMS,
    min_identity_coverage: float = DEFAULT_MIN_IDENTITY_COVERAGE,
    min_direct_phrases: int = DEFAULT_MIN_DIRECT_SIX_TOKEN_PHRASES,
) -> ContentAlignment:
    """Apply the permanent two-signal alignment gate to a candidate pair."""
    title_passed, shared_terms, coverage = title_party_alignment(
        ildc_text, title, petitioner, respondent,
        min_shared_terms=min_shared_terms, min_coverage=min_identity_coverage,
    )
    direct_count, example = shared_six_token_phrases(
        ildc_text, source_text, stop_at=min_direct_phrases,
    )
    direct_passed = direct_count >= min_direct_phrases
    return ContentAlignment(
        title_party_passed=title_passed,
        shared_identity_terms=shared_terms,
        identity_coverage=coverage,
        direct_phrase_count=direct_count,
        example_shared_phrase=example,
        direct_content_passed=direct_passed,
        passed=title_passed and direct_passed,
    )
