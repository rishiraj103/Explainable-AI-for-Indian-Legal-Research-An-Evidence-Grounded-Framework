"""Small reusable helpers for evidence retrieval."""

from __future__ import annotations

import re


def fts_query(query_text: str) -> str:
    """Convert natural-language input to a conservative FTS5 OR query."""

    terms = re.findall(r"[A-Za-z0-9]{2,}", query_text.casefold())[:32]
    if not terms:
        raise ValueError("query must contain at least one two-character alphanumeric term")
    return " OR ".join(terms)
