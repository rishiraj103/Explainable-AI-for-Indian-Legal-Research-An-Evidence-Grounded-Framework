import pytest

from legal_xai.retrieval import fts_query


def test_fts_query_extracts_searchable_terms() -> None:
    assert fts_query("Anticipatory bail under Section 438") == "anticipatory OR bail OR under OR section OR 438"


def test_fts_query_rejects_non_searchable_input() -> None:
    with pytest.raises(ValueError, match="two-character"):
        fts_query("?!")
