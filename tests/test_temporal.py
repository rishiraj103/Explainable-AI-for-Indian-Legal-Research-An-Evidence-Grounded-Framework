from legal_xai.temporal import (
    TemporalStatus,
    assess_temporal_eligibility,
    partition_evidence_candidates,
)


def test_earlier_year_is_eligible() -> None:
    decision = assess_temporal_eligibility(2010, "2009-12-31")
    assert decision.status is TemporalStatus.ELIGIBLE


def test_ecourts_day_month_year_date_is_parsed() -> None:
    decision = assess_temporal_eligibility(2010, "31-12-2009")
    assert decision.status is TemporalStatus.ELIGIBLE


def test_same_year_is_ambiguous_and_excluded() -> None:
    decision = assess_temporal_eligibility(2010, "2010-01-01")
    assert decision.status is TemporalStatus.AMBIGUOUS_EXCLUDED


def test_later_year_is_ineligible() -> None:
    decision = assess_temporal_eligibility(2010, "2011-01-01")
    assert decision.status is TemporalStatus.INELIGIBLE


def test_missing_precedent_date_is_excluded() -> None:
    decision = assess_temporal_eligibility(2010, None)
    assert decision.status is TemporalStatus.EXCLUDED_MISSING_METADATA


def test_missing_ildc_year_is_excluded() -> None:
    decision = assess_temporal_eligibility(None, "2009-12-31")
    assert decision.status is TemporalStatus.EXCLUDED_MISSING_METADATA


def test_unparseable_date_is_excluded() -> None:
    decision = assess_temporal_eligibility("2010_123.txt", "unknown")
    assert decision.status is TemporalStatus.EXCLUDED_MISSING_METADATA


def test_retrieval_candidates_are_partitioned_without_dropping_exclusions() -> None:
    candidates = [
        {"source_id": "earlier", "decision_date": "2009-12-31"},
        {"source_id": "same", "decision_date": "2010-01-01"},
        {"source_id": "later", "decision_date": "2011-01-01"},
        {"source_id": "unknown", "decision_date": None},
    ]
    buckets = partition_evidence_candidates(2010, candidates)
    assert [item["source_id"] for item in buckets.eligible] == ["earlier"]
    assert [item["source_id"] for item in buckets.ambiguous_excluded] == ["same"]
    assert [item["source_id"] for item in buckets.ineligible] == ["later"]
    assert [item["source_id"] for item in buckets.missing_metadata] == ["unknown"]
