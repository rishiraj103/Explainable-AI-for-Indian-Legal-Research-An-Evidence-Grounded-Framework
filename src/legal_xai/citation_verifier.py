"""Week 9 citation and evidence verification for controlled E3 answers."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping

from legal_xai.retrieval import exclude_query_duplicate
from legal_xai.temporal import assess_temporal_eligibility


VERIFICATION_VERSION = "week9-citation-evidence-verifier-v2"
AUTHORITY_FIELDS = frozenset({"evidence_id", "case_id", "citation", "decision_date", "court"})


@dataclass(frozen=True)
class CorpusEvidenceRecord:
    """The provenance fields a citation must reproduce exactly."""

    chunk_id: str
    source_id: str
    case_id: str | None
    citation: str | None
    decision_date: str
    title: str | None
    court: str
    pdf_file: str
    page_number: int
    passage_start_char: int
    passage_end_char: int
    text: str


@dataclass(frozen=True)
class CitationCheck:
    evidence_id: str | None
    chunk_id: str | None
    citation: str | None
    passed: bool
    failures: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "chunk_id": self.chunk_id,
            "citation": self.citation,
            "passed": self.passed,
            "failures": list(self.failures),
        }


@dataclass(frozen=True)
class RetrievedCandidate:
    """A temporally eligible corpus chunk considered for a particular run."""

    record: CorpusEvidenceRecord
    rank: int


def _normalise_citation(value: str | None) -> str:
    return " ".join((value or "").casefold().split())


def _normalise_title(value: str | None) -> str:
    """Normalize title variants such as ``v.`` and ``versus`` for cross-citation matching."""

    value = (value or "").casefold().replace("versus", " v ")
    value = re.sub(r"\bu\.?\s*p\.?\b", "uttar pradesh", value)
    tokens = re.findall(r"[a-z0-9]+", value)
    return " ".join(
        token for token in tokens
        if token not in {"and", "anr", "another", "ors", "others", "etc", "of", "the"}
    )


def _candidate_matches_expected(candidate: RetrievedCandidate, expected: Mapping[str, Any]) -> bool:
    expected_source_id = str(expected.get("authority_source_id", ""))
    if expected_source_id and expected_source_id == candidate.record.source_id:
        return True
    expected_citation = _normalise_citation(expected.get("authority_citation"))
    if expected_citation and _normalise_citation(candidate.record.citation) == expected_citation:
        return True
    expected_title = _normalise_title(expected.get("authority_title"))
    return bool(
        expected_title
        and expected_title == _normalise_title(candidate.record.title)
        and str(expected.get("authority_decision_date", "")) == candidate.record.decision_date
    )


def _check_metadata(evidence: Mapping[str, Any], record: CorpusEvidenceRecord) -> list[str]:
    failures: list[str] = []
    expected = {
        "source_id": record.source_id,
        "case_id": record.case_id,
        "citation": record.citation,
        "decision_date": record.decision_date,
        "court": record.court,
        "pdf_file": record.pdf_file,
        "page_number": record.page_number,
        "passage_start_char": record.passage_start_char,
        "passage_end_char": record.passage_end_char,
    }
    for field, value in expected.items():
        if evidence.get(field) != value:
            failures.append(f"corpus_metadata_mismatch:{field}")
    if evidence.get("verbatim_passage") != record.text:
        failures.append("passage_mismatch")
    return failures


def verify_answer_citations(
    *,
    answer: Mapping[str, Any],
    query_id: str,
    query_year: int,
    corpus_records: Mapping[str, CorpusEvidenceRecord],
    retrieved_chunk_ids: set[str],
    audited_near_case_ids: set[str],
) -> tuple[CitationCheck, ...]:
    """Verify every displayed citation against corpus, run, dedup, and time rules."""

    # Week 10 uses explanatory section names; accept the old names only so
    # archived Week 8/9 outputs remain independently reproducible.
    evidence_items = answer.get("supporting_evidence", answer.get("evidence", []))
    by_evidence_id = {
        item.get("evidence_id"): item
        for item in evidence_items
        if isinstance(item, Mapping) and item.get("evidence_id")
    }
    checks: list[CitationCheck] = []

    for authority in answer.get("applicable_law_and_cases", answer.get("retrieved_authorities", [])):
        evidence_id = authority.get("evidence_id") if isinstance(authority, Mapping) else None
        evidence = by_evidence_id.get(evidence_id)
        if evidence is None:
            checks.append(CitationCheck(
                evidence_id=evidence_id,
                chunk_id=None,
                citation=authority.get("citation") if isinstance(authority, Mapping) else None,
                passed=False,
                failures=("authority_without_linked_evidence",),
            ))
            continue

        chunk_id = evidence.get("chunk_id")
        record = corpus_records.get(chunk_id)
        failures: list[str] = []
        if isinstance(authority, Mapping):
            for field in sorted(set(authority) - AUTHORITY_FIELDS):
                failures.append(f"unsupported_authority_field:{field}")
        if record is None:
            failures.append("corpus_chunk_missing")
        else:
            failures.extend(_check_metadata(evidence, record))
            for field in ("case_id", "citation", "decision_date", "court"):
                if authority.get(field) != getattr(record, field):
                    failures.append(f"authority_metadata_mismatch:{field}")
            if exclude_query_duplicate(query_id, record.case_id, audited_near_case_ids):
                failures.append("query_duplicate_source")
            temporal = assess_temporal_eligibility(query_year, record.decision_date)
            if temporal.status.value != "eligible":
                failures.append(f"temporal_{temporal.status.value}")
        if chunk_id not in retrieved_chunk_ids:
            failures.append("not_retrieved_for_query")
        checks.append(CitationCheck(
            evidence_id=evidence_id,
            chunk_id=chunk_id,
            citation=evidence.get("citation"),
            passed=not failures,
            failures=tuple(failures),
        ))
    return tuple(checks)


def evaluate_against_answer_key(
    *,
    query_id: str,
    checks: Iterable[CitationCheck],
    answer_key_entries: Iterable[Mapping[str, Any]],
    retrieved_candidates: Iterable[RetrievedCandidate] = (),
) -> dict[str, Any]:
    """Measure key-authority retrieval and final displayed citations separately.

    Citation strings alone are insufficient: the eCourts corpus commonly stores an
    S.C.R. citation while a source-verified key may identify the same authority by
    its parallel SCC citation. A verified authority source ID, followed by title
    plus exact decision date, are identity fallbacks for a candidate that was
    actually retrieved.
    """

    expected_entries = [
        entry for entry in answer_key_entries
        if entry.get("status") == "evaluation" and entry.get("query_case_id") == query_id
    ]
    expected = {_normalise_citation(str(entry.get("authority_citation", ""))) for entry in expected_entries}
    verified = {
        _normalise_citation(check.citation)
        for check in checks
        if check.passed and check.citation
    }
    candidates = tuple(retrieved_candidates)
    retrieved_matches = {
        _normalise_citation(str(entry.get("authority_citation", ""))): [
            candidate for candidate in candidates if _candidate_matches_expected(candidate, entry)
        ]
        for entry in expected_entries
    }
    displayed_chunk_ids = {check.chunk_id for check in checks if check.passed and check.chunk_id}
    retrieved_expected = {citation for citation, matches in retrieved_matches.items() if matches}
    displayed_expected = {
        citation for citation, matches in retrieved_matches.items()
        if any(match.record.chunk_id in displayed_chunk_ids for match in matches)
    }
    # Preserve standalone unit use where only a displayed citation is available.
    displayed_expected |= expected & verified
    retrieved_expected |= displayed_expected
    failed = [check.as_dict() for check in checks if not check.passed]
    return {
        "query_id": query_id,
        "expected_authority_citations": sorted(expected),
        "verified_displayed_citations": sorted(verified),
        "matched_expected_authorities": sorted(displayed_expected),
        "expected_authorities_retrieved": sorted(retrieved_expected),
        "expected_authorities_retrieved_not_selected": sorted(retrieved_expected - displayed_expected),
        "expected_authorities_not_retrieved": sorted(expected - retrieved_expected),
        "retrieved_expected_authority_details": [
            {
                "expected_authority_citation": citation,
                "matches": [
                    {
                        "rank": candidate.rank,
                        "source_id": candidate.record.source_id,
                        "corpus_citation": candidate.record.citation,
                        "decision_date": candidate.record.decision_date,
                        "title": candidate.record.title,
                    }
                    for candidate in matches
                ],
            }
            for citation, matches in sorted(retrieved_matches.items())
            if matches
        ],
        "wrong_or_unverified_displayed_citations": failed,
    }
