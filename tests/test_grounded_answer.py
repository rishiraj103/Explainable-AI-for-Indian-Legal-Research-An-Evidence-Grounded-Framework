import pytest

from legal_xai.evidence_pipeline import EvidenceCandidate
from legal_xai.grounded_answer import (
    EXPLANATION_ORDER,
    MULTIPLE_EVIDENCE_CONCLUSION,
    assert_answer_grounded,
    render_grounded_answer,
)


def evidence(chunk_id: str = "chunk-1", status: str = "eligible") -> EvidenceCandidate:
    return EvidenceCandidate(
        rank=1,
        chunk_id=chunk_id,
        source_id="source-1",
        case_id="2000 INSC 1",
        citation="(2000) 1 SCC 1",
        decision_date="2000-01-01",
        court="Supreme Court of India",
        pdf_file="source-1.pdf",
        page_number=4,
        passage_start_char=10,
        passage_end_char=40,
        bm25_score=8.0,
        temporal_status=status,
        text="The supplied evidence states the applicable legal principle.",
    )


def test_renderer_only_exposes_the_supplied_verbatim_evidence():
    source = evidence()
    answer = render_grounded_answer(query="What principle applies?", selected_evidence=[source]).as_dict()

    assert answer["legal_issue"]["text"] == "What principle applies?"
    assert answer["explanation_order"] == list(EXPLANATION_ORDER)
    assert answer["applicable_law_and_cases"][0]["citation"] == source.citation
    assert answer["supporting_evidence"][0]["verbatim_passage"] == source.text
    assert answer["conclusion"]["evidence_ids"] == ["E1"]
    assert "does not infer conclusions" in answer["uncertainty"]
    assert_answer_grounded(answer, [source])


def test_renderer_rejects_noneligible_evidence():
    with pytest.raises(ValueError, match="ineligible"):
        render_grounded_answer(query="Issue", selected_evidence=[evidence(status="ineligible")])


def test_grounding_audit_rejects_altered_passage_and_unknown_authority():
    source = evidence()
    answer = render_grounded_answer(query="Issue", selected_evidence=[source]).as_dict()
    answer["supporting_evidence"][0]["verbatim_passage"] = "Unsupported conclusion."
    with pytest.raises(ValueError, match="alters the evidence passage"):
        assert_answer_grounded(answer, [source])

    answer = render_grounded_answer(query="Issue", selected_evidence=[source]).as_dict()
    answer["applicable_law_and_cases"][0]["evidence_id"] = "E99"
    with pytest.raises(ValueError, match="unknown evidence"):
        assert_answer_grounded(answer, [source])


def test_grounding_audit_rejects_a_tempted_unsupported_conclusion():
    source = evidence()
    answer = render_grounded_answer(query="Issue", selected_evidence=[source]).as_dict()
    answer["conclusion"]["text"] = "The appeal must succeed."

    with pytest.raises(ValueError, match="broader conclusion"):
        assert_answer_grounded(answer, [source])


def test_thin_evidence_discloses_limitation_without_a_fabricated_conclusion():
    source = evidence()
    answer = render_grounded_answer(query="Issue", selected_evidence=[source]).as_dict()

    assert answer["evidence_sufficiency"] == "limited"
    assert "Only one eligible passage" in answer["uncertainty"]
    assert answer["conclusion"]["evidence_ids"] == ["E1"]
    assert_answer_grounded(answer, [source])


def test_no_eligible_evidence_reports_insufficiency_without_authority_claims():
    answer = render_grounded_answer(query="Issue", selected_evidence=[]).as_dict()

    assert answer["evidence_sufficiency"] == "insufficient"
    assert answer["applicable_law_and_cases"] == []
    assert answer["supporting_evidence"] == []
    assert "cannot state a legal conclusion" in answer["uncertainty"]
    assert_answer_grounded(answer, [])


def test_multiple_evidence_uses_the_frozen_noninferential_conclusion():
    answer = render_grounded_answer(
        query="Issue", selected_evidence=[evidence(), evidence(chunk_id="chunk-2")]
    ).as_dict()

    assert answer["conclusion"]["text"] == MULTIPLE_EVIDENCE_CONCLUSION
    assert answer["conclusion"]["evidence_ids"] == ["E1", "E2"]
    assert_answer_grounded(answer, [evidence(), evidence(chunk_id="chunk-2")])


def test_grounding_audit_rejects_out_of_order_explanation_structure():
    answer = render_grounded_answer(query="Issue", selected_evidence=[evidence()]).as_dict()
    answer["explanation_order"] = list(reversed(EXPLANATION_ORDER))

    with pytest.raises(ValueError, match="frozen order"):
        assert_answer_grounded(answer, [evidence()])
