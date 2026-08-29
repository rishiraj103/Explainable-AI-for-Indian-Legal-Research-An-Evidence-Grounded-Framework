"""Week 8 controlled renderer for evidence-grounded legal research briefs.

The renderer deliberately performs no generation, retrieval, ranking, or legal
inference. It exposes only the supplied, temporally eligible Week 7 evidence
with stable provenance. This makes E3's grounding contract auditable before
Week 9 adds citation verification and E4 reliability constraints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from legal_xai.evidence_pipeline import EvidenceCandidate


ANSWER_VERSION = "week8-controlled-evidence-renderer-v2"
UNCERTAINTY_TEXT = (
    "This is an evidence-grounded research brief, not legal advice. It reports only the "
    "selected retrieved passages and does not infer conclusions beyond them. Missing or "
    "incomplete evidence should be reviewed by a human."
)
NO_ELIGIBLE_EVIDENCE_TEXT = (
    "No temporally eligible, non-duplicate evidence was selected. The system cannot state a "
    "legal conclusion for this query without fabricating support."
)
LIMITED_EVIDENCE_TEXT = (
    "Only one eligible passage was selected. It is displayed verbatim, but is insufficient for "
    "a broader legal conclusion."
)


@dataclass(frozen=True)
class GroundedAnswer:
    """A structured response whose material content is copied from selected evidence."""

    query: str
    evidence: tuple[EvidenceCandidate, ...]

    def as_dict(self) -> dict[str, Any]:
        evidence_items = [
            {
                "evidence_id": f"E{position}",
                "chunk_id": item.chunk_id,
                "source_id": item.source_id,
                "case_id": item.case_id,
                "citation": item.citation,
                "decision_date": item.decision_date,
                "court": item.court,
                "pdf_file": item.pdf_file,
                "page_number": item.page_number,
                "passage_start_char": item.passage_start_char,
                "passage_end_char": item.passage_end_char,
                "verbatim_passage": item.text,
            }
            for position, item in enumerate(self.evidence, start=1)
        ]
        if not evidence_items:
            evidence_sufficiency = "insufficient"
            uncertainty = f"{UNCERTAINTY_TEXT} {NO_ELIGIBLE_EVIDENCE_TEXT}"
        elif len(evidence_items) == 1:
            evidence_sufficiency = "limited"
            uncertainty = f"{UNCERTAINTY_TEXT} {LIMITED_EVIDENCE_TEXT}"
        else:
            evidence_sufficiency = "multiple_selected_passages"
            uncertainty = UNCERTAINTY_TEXT
        return {
            "answer_version": ANSWER_VERSION,
            "legal_issue": {"text": self.query, "source": "user_query"},
            "retrieved_authorities": [
                {
                    "evidence_id": item["evidence_id"],
                    "case_id": item["case_id"],
                    "citation": item["citation"],
                    "decision_date": item["decision_date"],
                    "court": item["court"],
                }
                for item in evidence_items
            ],
            "evidence": evidence_items,
            "supported_observations": [
                {
                    "evidence_id": item["evidence_id"],
                    "verbatim_passage": item["verbatim_passage"],
                }
                for item in evidence_items
            ],
            "evidence_sufficiency": evidence_sufficiency,
            "uncertainty": uncertainty,
        }


def render_grounded_answer(
    *, query: str, selected_evidence: Iterable[EvidenceCandidate]
) -> GroundedAnswer:
    """Render a brief from an already-selected set of eligible evidence only."""
    if not query.strip():
        raise ValueError("A legal-research query is required")
    evidence = tuple(selected_evidence)
    invalid = [item.chunk_id for item in evidence if item.temporal_status != "eligible"]
    if invalid:
        raise ValueError(f"Grounded answers cannot include ineligible evidence: {invalid}")
    if len({item.chunk_id for item in evidence}) != len(evidence):
        raise ValueError("Selected evidence must have unique chunk IDs")
    return GroundedAnswer(query=query.strip(), evidence=evidence)


def assert_answer_grounded(answer: dict[str, Any], selected_evidence: Iterable[EvidenceCandidate]) -> None:
    """Raise when an answer contains altered text, authority data, or unknown evidence."""
    expected = {item.chunk_id: item for item in selected_evidence}
    if answer.get("answer_version") != ANSWER_VERSION:
        raise ValueError("Unexpected grounded-answer version")
    evidence_items = answer.get("evidence", [])
    if len(evidence_items) != len(expected):
        raise ValueError("Answer evidence count does not match its supplied evidence")
    seen: set[str] = set()
    by_evidence_id: dict[str, str] = {}
    for item in evidence_items:
        chunk_id = item.get("chunk_id")
        source = expected.get(chunk_id)
        if source is None:
            raise ValueError(f"Answer cites an unknown chunk: {chunk_id!r}")
        if chunk_id in seen:
            raise ValueError(f"Answer repeats chunk: {chunk_id!r}")
        seen.add(chunk_id)
        if item.get("verbatim_passage") != source.text:
            raise ValueError(f"Answer alters the evidence passage for {chunk_id!r}")
        for field in ("source_id", "case_id", "citation", "decision_date", "court", "pdf_file", "page_number"):
            if item.get(field) != getattr(source, field):
                raise ValueError(f"Answer alters {field} for {chunk_id!r}")
        by_evidence_id[item["evidence_id"]] = source.text
    for authority in answer.get("retrieved_authorities", []):
        evidence_id = authority.get("evidence_id")
        if evidence_id not in by_evidence_id:
            raise ValueError(f"Answer authority references unknown evidence: {evidence_id!r}")
    for observation in answer.get("supported_observations", []):
        evidence_id = observation.get("evidence_id")
        if observation.get("verbatim_passage") != by_evidence_id.get(evidence_id):
            raise ValueError(f"Answer observation is not verbatim supplied evidence: {evidence_id!r}")
    expected_sufficiency = (
        "insufficient" if not expected else "limited" if len(expected) == 1 else "multiple_selected_passages"
    )
    if answer.get("evidence_sufficiency") != expected_sufficiency:
        raise ValueError("Answer evidence sufficiency status does not match supplied evidence")
    if expected_sufficiency == "insufficient":
        if answer.get("retrieved_authorities") or answer.get("supported_observations"):
            raise ValueError("An insufficient-evidence answer cannot claim authorities or observations")
        if NO_ELIGIBLE_EVIDENCE_TEXT not in str(answer.get("uncertainty", "")):
            raise ValueError("An insufficient-evidence answer must disclose the missing evidence")
    elif expected_sufficiency == "limited" and LIMITED_EVIDENCE_TEXT not in str(answer.get("uncertainty", "")):
        raise ValueError("A limited-evidence answer must disclose its limitation")
