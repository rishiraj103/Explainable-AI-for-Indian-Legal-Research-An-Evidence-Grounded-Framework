from __future__ import annotations

from legal_xai.citation_verifier import (
    CorpusEvidenceRecord,
    RetrievedCandidate,
    evaluate_against_answer_key,
    verify_answer_citations,
)


def record(*, case_id: str = "2018 INSC 12", decision_date: str = "2018-05-01") -> CorpusEvidenceRecord:
    return CorpusEvidenceRecord(
        chunk_id="chunk-1", source_id="source-1", case_id=case_id, citation="(2018) 1 SCC 12",
        decision_date=decision_date, title="Example v State", court="Supreme Court of India", pdf_file="source-1.pdf",
        page_number=4, passage_start_char=10, passage_end_char=50,
        text="The corpus passage states the legal principle.",
    )


def answer(source: CorpusEvidenceRecord | None = None) -> dict:
    source = source or record()
    evidence = {
        "evidence_id": "E1", "chunk_id": source.chunk_id, "source_id": source.source_id,
        "case_id": source.case_id, "citation": source.citation, "decision_date": source.decision_date,
        "court": source.court, "pdf_file": source.pdf_file, "page_number": source.page_number,
        "passage_start_char": source.passage_start_char, "passage_end_char": source.passage_end_char,
        "verbatim_passage": source.text,
    }
    authority = {key: evidence[key] for key in ("evidence_id", "case_id", "citation", "decision_date", "court")}
    return {"evidence": [evidence], "retrieved_authorities": [authority]}


def verify(payload: dict, source: CorpusEvidenceRecord | None = None, *, query_id: str = "2020_99", query_year: int = 2020,
           retrieved: set[str] | None = None, near: set[str] | None = None):
    source = source or record()
    return verify_answer_citations(
        answer=payload, query_id=query_id, query_year=query_year,
        corpus_records={source.chunk_id: source},
        retrieved_chunk_ids=retrieved if retrieved is not None else {source.chunk_id},
        audited_near_case_ids=near or set(),
    )


def test_verifies_a_corpus_backed_retrieved_temporally_eligible_citation():
    checks = verify(answer())
    assert len(checks) == 1
    assert checks[0].passed


def test_rejects_a_missing_corpus_chunk():
    payload = answer()
    checks = verify_answer_citations(
        answer=payload, query_id="2020_99", query_year=2020, corpus_records={},
        retrieved_chunk_ids={"chunk-1"}, audited_near_case_ids=set(),
    )
    assert checks[0].failures == ("corpus_chunk_missing",)


def test_rejects_an_altered_passage():
    payload = answer()
    payload["evidence"][0]["verbatim_passage"] = "Altered passage."
    assert "passage_mismatch" in verify(payload)[0].failures


def test_rejects_a_fabricated_case_name_claim():
    payload = answer()
    payload["retrieved_authorities"][0]["case_name"] = "Invented Authority v. Fictional State"
    assert "unsupported_authority_field:case_name" in verify(payload)[0].failures


def test_rejects_tampered_authority_citation_metadata():
    payload = answer()
    payload["retrieved_authorities"][0]["citation"] = "Invented citation"
    assert "authority_metadata_mismatch:citation" in verify(payload)[0].failures


def test_rejects_a_citation_not_returned_for_this_query():
    assert "not_retrieved_for_query" in verify(answer(), retrieved=set())[0].failures


def test_rejects_a_later_year_authority():
    source = record(decision_date="2021-01-01")
    assert verify(answer(source), source)[0].failures == ("temporal_ineligible",)


def test_rejects_a_same_year_authority_as_ambiguous():
    source = record(decision_date="2020-01-01")
    assert "temporal_ambiguous_excluded" in verify(answer(source), source)[0].failures


def test_does_not_treat_syntactic_id_equality_as_a_target_match():
    source = record(case_id="2020 INSC 99")
    assert verify(answer(source), source)[0].passed


def test_rejects_an_audited_near_duplicate_even_when_ids_differ():
    source = record(case_id="2018 INSC 12")
    assert "query_duplicate_source" in verify(answer(source), source, near={"2018 INSC 12"})[0].failures


def test_rejects_an_authority_without_linked_evidence():
    payload = answer()
    payload["retrieved_authorities"][0]["evidence_id"] = "E99"
    assert verify(payload)[0].failures == ("authority_without_linked_evidence",)


def test_answer_key_measurement_counts_a_verified_expected_authority():
    checks = verify(answer())
    measurement = evaluate_against_answer_key(
        query_id="2020_99", checks=checks,
        answer_key_entries=[{"status": "evaluation", "query_case_id": "2020_99", "authority_citation": "(2018) 1 SCC 12"}],
    )
    assert measurement["matched_expected_authorities"] == ["(2018) 1 scc 12"]
    assert measurement["expected_authorities_not_retrieved"] == []


def test_answer_key_measurement_separates_missing_and_failed_citations():
    payload = answer()
    payload["evidence"][0]["verbatim_passage"] = "Altered passage."
    measurement = evaluate_against_answer_key(
        query_id="2020_99", checks=verify(payload),
        answer_key_entries=[{"status": "evaluation", "query_case_id": "2020_99", "authority_citation": "(2018) 1 SCC 12"}],
    )
    assert measurement["matched_expected_authorities"] == []
    assert measurement["expected_authorities_not_retrieved"] == ["(2018) 1 scc 12"]
    assert len(measurement["wrong_or_unverified_displayed_citations"]) == 1


def test_answer_key_reconciles_parallel_citations_by_title_and_date():
    source = record(decision_date="2006-05-12")
    source = CorpusEvidenceRecord(
        **{**source.__dict__, "citation": "[2006] SUPP. 2 S.C.R. 582", "title": "U. Raghavendra Acharya & Ors. versus State of Karnataka & Ors."}
    )
    measurement = evaluate_against_answer_key(
        query_id="2020_99", checks=(),
        answer_key_entries=[{
            "status": "evaluation", "query_case_id": "2020_99", "authority_citation": "(2006) 9 SCC 630",
            "authority_title": "U. Raghavendra Acharya & Ors. v. State of Karnataka & Ors.",
            "authority_decision_date": "2006-05-12",
        }],
        retrieved_candidates=[RetrievedCandidate(record=source, rank=29)],
    )
    assert measurement["expected_authorities_retrieved"] == ["(2006) 9 scc 630"]
    assert measurement["expected_authorities_retrieved_not_selected"] == ["(2006) 9 scc 630"]
    assert measurement["expected_authorities_not_retrieved"] == []


def test_answer_key_reconciles_a_parallel_citation_by_verified_source_id():
    source = record(decision_date="2006-05-12")
    source = CorpusEvidenceRecord(**{**source.__dict__, "source_id": "verified-source"})
    measurement = evaluate_against_answer_key(
        query_id="2020_99", checks=(),
        answer_key_entries=[{
            "status": "evaluation", "query_case_id": "2020_99", "authority_citation": "(2006) 9 SCC 630",
            "authority_source_id": "verified-source",
        }],
        retrieved_candidates=[RetrievedCandidate(record=source, rank=29)],
    )
    assert measurement["expected_authorities_retrieved"] == ["(2006) 9 scc 630"]


def test_no_citations_is_a_valid_no_evidence_response():
    checks = verify_answer_citations(
        answer={"evidence": [], "retrieved_authorities": []}, query_id="2020_99", query_year=2020,
        corpus_records={}, retrieved_chunk_ids=set(), audited_near_case_ids=set(),
    )
    assert checks == ()
