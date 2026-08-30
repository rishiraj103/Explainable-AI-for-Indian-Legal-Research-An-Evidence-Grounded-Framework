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


ANSWER_VERSION = "week10-verified-explanation-renderer-v1"
EXPLANATION_ORDER = (
    "legal_issue",
    "applicable_law_and_cases",
    "supporting_evidence",
    "conclusion",
    "uncertainty",
)
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
MULTIPLE_EVIDENCE_CONCLUSION = (
    "No legal conclusion is inferred beyond the cited supporting evidence; review the "
    "verbatim passages and their provenance."
)
LIMITED_EVIDENCE_CONCLUSION = (
    "No broader legal conclusion is stated because only one supporting passage was selected."
)
NO_EVIDENCE_CONCLUSION = (
    "No legal conclusion is stated because no temporally eligible, non-duplicate evidence was selected."
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
            conclusion = NO_EVIDENCE_CONCLUSION
        elif len(evidence_items) == 1:
            evidence_sufficiency = "limited"
            uncertainty = f"{UNCERTAINTY_TEXT} {LIMITED_EVIDENCE_TEXT}"
            conclusion = LIMITED_EVIDENCE_CONCLUSION
        else:
            evidence_sufficiency = "multiple_selected_passages"
            uncertainty = UNCERTAINTY_TEXT
            conclusion = MULTIPLE_EVIDENCE_CONCLUSION
        return {
            "answer_version": ANSWER_VERSION,
            "explanation_order": list(EXPLANATION_ORDER),
            "legal_issue": {"text": self.query, "source": "user_query"},
            "applicable_law_and_cases": [
                {
                    "evidence_id": item["evidence_id"],
                    "case_id": item["case_id"],
                    "citation": item["citation"],
                    "decision_date": item["decision_date"],
                    "court": item["court"],
                }
                for item in evidence_items
            ],
            "supporting_evidence": evidence_items,
            "conclusion": {
                "text": conclusion,
                "mode": "evidence_bound_no_inference",
                "evidence_ids": [item["evidence_id"] for item in evidence_items],
            },
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
    if answer.get("explanation_order") != list(EXPLANATION_ORDER):
        raise ValueError("Answer explanation sections are not in the frozen order")
    evidence_items = answer.get("supporting_evidence", [])
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
    for authority in answer.get("applicable_law_and_cases", []):
        evidence_id = authority.get("evidence_id")
        if evidence_id not in by_evidence_id:
            raise ValueError(f"Answer authority references unknown evidence: {evidence_id!r}")
    expected_sufficiency = (
        "insufficient" if not expected else "limited" if len(expected) == 1 else "multiple_selected_passages"
    )
    if answer.get("evidence_sufficiency") != expected_sufficiency:
        raise ValueError("Answer evidence sufficiency status does not match supplied evidence")
    conclusion = answer.get("conclusion", {})
    if conclusion.get("mode") != "evidence_bound_no_inference":
        raise ValueError("Answer conclusion is not evidence-bound")
    if conclusion.get("evidence_ids") != [item["evidence_id"] for item in evidence_items]:
        raise ValueError("Answer conclusion references evidence inconsistently")
    if expected_sufficiency == "insufficient":
        if answer.get("applicable_law_and_cases"):
            raise ValueError("An insufficient-evidence answer cannot claim authorities or observations")
        if conclusion.get("text") != NO_EVIDENCE_CONCLUSION:
            raise ValueError("An insufficient-evidence answer must not infer a conclusion")
        if NO_ELIGIBLE_EVIDENCE_TEXT not in str(answer.get("uncertainty", "")):
            raise ValueError("An insufficient-evidence answer must disclose the missing evidence")
    elif expected_sufficiency == "limited":
        if conclusion.get("text") != LIMITED_EVIDENCE_CONCLUSION:
            raise ValueError("A limited-evidence answer must not infer a broader conclusion")
        if LIMITED_EVIDENCE_TEXT not in str(answer.get("uncertainty", "")):
            raise ValueError("A limited-evidence answer must disclose its limitation")
    elif conclusion.get("text") != MULTIPLE_EVIDENCE_CONCLUSION:
        raise ValueError("A multiple-evidence answer must use the frozen non-inferential conclusion")
