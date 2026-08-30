"""Small reusable helpers for evidence retrieval."""

from __future__ import annotations

import re
import csv
from collections import Counter
from math import log1p
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer

from legal_xai.alignment import (
    DEFAULT_MIN_DIRECT_SIX_TOKEN_PHRASES,
    shared_phrase_count_from_query_set,
    shared_six_token_phrases,
)


SALIENT_QUERY_VERSION = "tfidf-segment-salient-terms-v1"
SALIENT_QUERY_MAX_TERMS = 32
LEGACY_QUERY_VERSION = "legacy-first-32-terms-v1"

# These are structural terms found repeatedly in Supreme Court-report opening
# matter. They add little legal-issue discrimination and previously dominated
# the first-32-term query. Statute/article labels are intentionally retained.
PROCEDURAL_STOP_WORDS = frozenset({
    "a", "an", "and", "appeal", "appeals", "appellate", "appellant", "appellants", "application", "applications",
    "are", "arising", "at", "been", "before", "by", "case", "cases", "civil", "company", "companynsel",
    "companyrt", "consideration", "court", "dated", "directed", "from", "for", "granted", "has", "have",
    "hearing", "high", "in", "is", "it", "judgment", "jurisdiction", "learned", "leave", "matter", "no",
    "of", "on", "order", "original", "parties", "petition", "petitions", "respondent", "respondents",
    "special", "supreme", "the", "these", "this", "to", "under", "versus", "v", "was", "were", "with",
})


def _query_segments(query_text: str) -> list[str]:
    """Split full facts text into stable TF-IDF units without using a model."""
    segments = [
        segment.strip()
        for segment in re.split(r"(?:\r?\n){2,}|(?<=[.!?])\s+", query_text)
        if len(re.findall(r"[A-Za-z0-9]{2,}", segment)) >= 4
    ]
    return segments or [query_text]


def salient_query_terms(query_text: str, *, max_terms: int = SALIENT_QUERY_MAX_TERMS) -> list[str]:
    """Select distinctive full-document keywords for the FTS5 BM25 query.

    A TF-IDF vectorizer is fitted to the document's own sentence/paragraph
    segments. Terms that are specific to substantive passages rank above
    repeated procedural opening matter; a small statutory-reference boost
    retains section/article numbers when they occur anywhere in the facts.
    """
    if max_terms < 1:
        raise ValueError("max_terms must be positive")
    all_tokens = re.findall(r"[A-Za-z0-9]{2,}", query_text.casefold())
    if not all_tokens:
        raise ValueError("query must contain at least one two-character alphanumeric term")
    token_counts = Counter(all_tokens)
    try:
        vectorizer = TfidfVectorizer(
            token_pattern=r"(?u)\b[a-zA-Z0-9]{2,}\b",
            lowercase=True,
            stop_words=sorted(PROCEDURAL_STOP_WORDS),
            norm="l2",
        )
        matrix = vectorizer.fit_transform(_query_segments(query_text))
        terms = vectorizer.get_feature_names_out()
        # Maximum segment salience finds concentrated substantive issue terms;
        # log term-frequency rewards recurring case-specific concepts gently.
        scores = {
            term: float(matrix[:, index].max()) * (1.0 + log1p(token_counts[term]))
            for index, term in enumerate(terms)
        }
    except ValueError:  # All terms were procedural stop words.
        scores = {
            term: 1.0 + log1p(count)
            for term, count in token_counts.items()
            if term not in PROCEDURAL_STOP_WORDS
        }

    # Explicit legal references retain both their label and numeric identifier.
    statutory_terms: set[str] = set()
    for label, number in re.findall(r"\b(section|sections|article|articles)\s+(\d+[a-z]*)", query_text.casefold()):
        statutory_terms.update({"section" if label.startswith("section") else "article", number})
    for term in statutory_terms:
        if term in token_counts:
            scores[term] = scores.get(term, 0.0) + 10.0

    first_position = {term: all_tokens.index(term) for term in scores}
    ranked = sorted(scores, key=lambda term: (-scores[term], first_position[term], term))
    selected = ranked[:max_terms]
    if not selected:
        raise ValueError("query has no non-procedural searchable terms")
    return selected


def fts_query(query_text: str, *, mode: str = "legacy_first_32") -> str:
    """Convert facts text to a configured, deterministic FTS5 OR query.

    ``salient_tfidf`` is retained for the recorded Week 9 corrective attempt.
    It is not the frozen runtime default because it did not meet the
    predeclared majority-of-nine dev-probe adoption criterion.
    """
    if mode == "legacy_first_32":
        terms = re.findall(r"[A-Za-z0-9]{2,}", query_text.casefold())[:SALIENT_QUERY_MAX_TERMS]
        if not terms:
            raise ValueError("query must contain at least one two-character alphanumeric term")
        return " OR ".join(terms)
    if mode == "salient_tfidf":
        return " OR ".join(salient_query_terms(query_text))
    raise ValueError(f"unknown query mode: {mode}")


def canonical_case_id(value: str | None) -> str | None:
    """Map ILDC `YYYY_N` and eCourts `YYYY INSC N` IDs to one key."""
    text = "" if value is None else str(value).strip()
    match = re.fullmatch(r"(\d{4})_(\d+)", text)
    if not match:
        match = re.fullmatch(r"(\d{4})\s+INSC\s+(\d+)", text, flags=re.I)
    return f"{match.group(1)}_{int(match.group(2))}" if match else None


def query_exclusion_cases(query_id: str, matches_file: Path) -> set[str]:
    """Return exact or audited-near-duplicate eCourts cases for one query."""
    excluded: set[str] = set()
    if not matches_file.exists():
        return excluded
    with matches_file.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("ildc_id") == query_id and row.get("ecourts_case_id"):
                excluded.add(str(row["ecourts_case_id"]))
    return excluded


def exclude_query_duplicate(
    query_id: str,
    candidate_case_id: str | None,
    audited_near_cases: set[str],
    *,
    query_case_text: str | None = None,
    candidate_source_text: str | None = None,
    query_six_token_phrases: set[str] | None = None,
) -> bool:
    """Exclude only a content-alignment-audited target or near-duplicate source.

    ILDC's ``YYYY_N`` suffix and eCourts' ``YYYY INSC N`` suffix are not a
    common identity namespace.  Canonical-ID equality is therefore unsafe as a
    retrieval-time self-match rule; accepted crosswalk rows provide the only
    admissible target-case identities.
    """
    del query_id  # Kept for the stable public call signature and audit logs.
    if str(candidate_case_id) in audited_near_cases:
        return True
    if query_case_text and candidate_source_text:
        if query_six_token_phrases is None:
            count, _ = shared_six_token_phrases(
                query_case_text, candidate_source_text,
                stop_at=DEFAULT_MIN_DIRECT_SIX_TOKEN_PHRASES,
            )
        else:
            count, _ = shared_phrase_count_from_query_set(
                query_six_token_phrases, candidate_source_text,
                stop_at=DEFAULT_MIN_DIRECT_SIX_TOKEN_PHRASES,
            )
        return count >= DEFAULT_MIN_DIRECT_SIX_TOKEN_PHRASES
    return False
