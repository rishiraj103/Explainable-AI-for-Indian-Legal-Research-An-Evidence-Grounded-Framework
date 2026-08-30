"""Small reusable helpers for evidence retrieval."""

from __future__ import annotations

import re
import csv
from pathlib import Path

from legal_xai.alignment import DEFAULT_MIN_DIRECT_SIX_TOKEN_PHRASES, shared_six_token_phrases


def fts_query(query_text: str) -> str:
    """Convert natural-language input to a conservative FTS5 OR query."""

    terms = re.findall(r"[A-Za-z0-9]{2,}", query_text.casefold())[:32]
    if not terms:
        raise ValueError("query must contain at least one two-character alphanumeric term")
    return " OR ".join(terms)


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
        count, _ = shared_six_token_phrases(
            query_case_text, candidate_source_text,
            stop_at=DEFAULT_MIN_DIRECT_SIX_TOKEN_PHRASES,
        )
        return count >= DEFAULT_MIN_DIRECT_SIX_TOKEN_PHRASES
    return False
