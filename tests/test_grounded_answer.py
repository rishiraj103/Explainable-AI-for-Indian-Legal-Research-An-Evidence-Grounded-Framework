import pytest

from legal_xai.evidence_pipeline import EvidenceCandidate
from legal_xai.grounded_answer import assert_answer_grounded, render_grounded_answer


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
    assert answer["evidence"][0]["verbatim_passage"] == source.text
    assert answer["supported_observations"][0]["verbatim_passage"] == source.text
    assert_answer_grounded(answer, [source])


def test_renderer_rejects_noneligible_or_empty_evidence():
    with pytest.raises(ValueError, match="ineligible"):
        render_grounded_answer(query="Issue", selected_evidence=[evidence(status="ineligible")])
    with pytest.raises(ValueError, match="At least one"):
        render_grounded_answer(query="Issue", selected_evidence=[])


def test_grounding_audit_rejects_altered_passage_and_unknown_authority():
    source = evidence()
    answer = render_grounded_answer(query="Issue", selected_evidence=[source]).as_dict()
    answer["evidence"][0]["verbatim_passage"] = "Unsupported conclusion."
    with pytest.raises(ValueError, match="alters the evidence passage"):
        assert_answer_grounded(answer, [source])

    answer = render_grounded_answer(query="Issue", selected_evidence=[source]).as_dict()
    answer["retrieved_authorities"][0]["evidence_id"] = "E99"
    with pytest.raises(ValueError, match="unknown evidence"):
        assert_answer_grounded(answer, [source])
