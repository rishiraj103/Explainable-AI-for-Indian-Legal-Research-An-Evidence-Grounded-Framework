from legal_xai.evidence_pipeline import EvidenceCandidate, select_diverse_evidence


def candidate(rank: int, source_id: str, score: float, status: str = "eligible") -> EvidenceCandidate:
    return EvidenceCandidate(
        rank=rank, chunk_id=f"{source_id}-{rank}", source_id=source_id, case_id=None, citation=None,
        decision_date="2019-01-01", court="Supreme Court of India", pdf_file="source.pdf",
        page_number=1, passage_start_char=0, passage_end_char=10, bm25_score=score,
        temporal_status=status, text="evidence text",
    )


def test_selector_uses_highest_scored_eligible_chunk_per_source():
    selected = select_diverse_evidence((
        candidate(2, "same-case", 8.0), candidate(1, "same-case", 9.0), candidate(3, "other-case", 7.0),
    ), 5)
    assert [item.chunk_id for item in selected] == ["same-case-1", "other-case-3"]


def test_selector_excludes_temporally_ineligible_candidates():
    selected = select_diverse_evidence((candidate(1, "future", 20.0, "ineligible"), candidate(2, "past", 1.0)), 5)
    assert [item.source_id for item in selected] == ["past"]


def test_selector_has_stable_rank_tie_breaker_and_respects_limit():
    selected = select_diverse_evidence((
        candidate(3, "c", 5.0), candidate(2, "b", 5.0), candidate(1, "a", 5.0),
    ), 2)
    assert [item.source_id for item in selected] == ["a", "b"]
