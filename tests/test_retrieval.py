import pytest

from legal_xai.retrieval import exclude_query_duplicate, fts_query


def test_fts_query_extracts_searchable_terms() -> None:
    assert fts_query("Anticipatory bail under Section 438") == "anticipatory OR bail OR under OR section OR 438"


def test_fts_query_rejects_non_searchable_input() -> None:
    with pytest.raises(ValueError, match="two-character"):
        fts_query("?!")


def test_exact_self_match_is_excluded() -> None:
    assert exclude_query_duplicate("2019_890", "2019 INSC 890", set())


def test_audited_near_duplicate_is_excluded() -> None:
    assert exclude_query_duplicate("2019_890", "2019 INSC 891", {"2019 INSC 891"})


def test_unrelated_case_is_retained() -> None:
    assert not exclude_query_duplicate("2019_890", "2018 INSC 890", {"2019 INSC 891"})
