import pytest

from legal_xai.retrieval import exclude_query_duplicate, fts_query, salient_query_terms


def test_fts_query_extracts_searchable_terms() -> None:
    terms = fts_query("Anticipatory bail under Section 438", mode="salient_tfidf").split(" OR ")
    assert {"anticipatory", "bail", "section", "438"}.issubset(terms)


def test_fts_query_rejects_non_searchable_input() -> None:
    with pytest.raises(ValueError, match="two-character"):
        fts_query("?!")


def test_salient_query_terms_look_beyond_procedural_opening_boilerplate() -> None:
    text = (
        "Civil appellate jurisdiction civil appeal leave granted by the high court. "
        "The appeal challenges a municipal octroi assessment on petroleum products. "
        "The petroleum pipeline and municipal corporation dispute concerns section 482 liability."
    )
    terms = salient_query_terms(text)
    assert {"municipal", "octroi", "petroleum", "section", "482"}.issubset(terms)
    assert not {"civil", "appellate", "jurisdiction", "appeal", "court", "leave"} & set(terms)


def test_salient_query_terms_are_bounded_and_unique() -> None:
    text = " ".join(f"substantive{i}" for i in range(80))
    terms = salient_query_terms(text)
    assert len(terms) == 32
    assert len(terms) == len(set(terms))


def test_legacy_query_mode_remains_available_for_regression_reproduction() -> None:
    assert fts_query("Anticipatory bail under Section 438", mode="legacy_first_32") == "anticipatory OR bail OR under OR section OR 438"


def test_salient_query_mode_is_the_frozen_default() -> None:
    text = "Civil appellate jurisdiction. Municipal octroi on petroleum products under section 482."
    assert fts_query(text) == fts_query(text, mode="salient_tfidf")


def test_fts_query_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError, match="unknown query mode"):
        fts_query("valid terms", mode="unknown")


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
