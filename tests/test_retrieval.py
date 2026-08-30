import pytest

from legal_xai.retrieval import exclude_query_duplicate, fts_query


def test_fts_query_extracts_searchable_terms() -> None:
    assert fts_query("Anticipatory bail under Section 438") == "anticipatory OR bail OR under OR section OR 438"


def test_fts_query_rejects_non_searchable_input() -> None:
    with pytest.raises(ValueError, match="two-character"):
        fts_query("?!")


def test_syntactic_id_equality_is_not_treated_as_a_self_match() -> None:
    assert not exclude_query_duplicate("2019_890", "2019 INSC 890", set())


def test_alignment_audited_target_is_excluded() -> None:
    assert exclude_query_duplicate("2019_890", "2019 INSC 890", {"2019 INSC 890"})


def test_content_self_match_is_excluded_without_crosswalk_mapping() -> None:
    text = "Alice Example challenged an unlawful termination by the employer. " * 120
    assert exclude_query_duplicate("2019_890", "unmapped", set(), query_case_text=text, candidate_source_text=text)


def test_topically_similar_but_distinct_document_is_retained() -> None:
    query = "Alice challenged termination after a disciplinary enquiry at her school. " * 120
    candidate = "Bob challenged termination after a procurement dispute at his factory. " * 120
    assert not exclude_query_duplicate("2019_890", "unmapped", set(), query_case_text=query, candidate_source_text=candidate)


def test_audited_near_duplicate_is_excluded() -> None:
    assert exclude_query_duplicate("2019_890", "2019 INSC 891", {"2019 INSC 891"})


def test_unrelated_case_is_retained() -> None:
    assert not exclude_query_duplicate("2019_890", "2018 INSC 890", {"2019 INSC 891"})
