"""Build a fixed, paired human-review packet from persisted Week 11 evidence.

The packet compares the same selected evidence in structured and flattened
presentations.  It does not generate new legal content or rerun retrieval.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg

from load_provenance import DEFAULT_DATABASE_URL


ROOT = Path(__file__).resolve().parents[1]
SAMPLES = (
    ("2008_1629", "structured_first"),
    ("1997_792", "flat_first"),
    ("1980_133", "structured_first"),
    ("2002_944", "flat_first"),
)


def display_structured(query_excerpt: str, evidence: list[dict]) -> str:
    lines = ["### Structured, evidence-linked brief", "", "**Issue context (excerpt)**", query_excerpt, "", "**Authorities and sources**"]
    for index, item in enumerate(evidence, start=1):
        lines.append(f"- E{index}: {item['citation'] or 'No reporter citation'}; {item['decision_date']}; {item['court']}; source `{item['source_id']}`; page {item['page_number']}.")
    lines.extend(["", "**Supporting evidence**", ""])
    for index, item in enumerate(evidence, start=1):
        lines.extend([f"E{index} (verbatim):", "> " + item["text"].replace("\n", "\n> "), ""])
    lines.extend(["**Conclusion**", "No legal conclusion is inferred beyond the cited supporting evidence; review the verbatim passages and their provenance.", "", "**Uncertainty**", "This is an evidence-grounded research brief, not legal advice. It reports only selected retrieved passages and does not infer conclusions beyond them. Missing or incomplete evidence should be reviewed by a human."])
    return "\n".join(lines)


def display_flat(query_excerpt: str, evidence: list[dict]) -> str:
    lines = ["### Flattened comparison brief", "", "Issue context (excerpt):", query_excerpt, "", "Selected material:"]
    for item in evidence:
        citation = item["citation"] or "No reporter citation"
        lines.extend([f"{citation} ({item['decision_date']})", item["text"], ""])
    lines.append("No legal conclusion is inferred beyond the material above. Missing or incomplete evidence should be reviewed by a human.")
    return "\n".join(lines)


def main() -> None:
    evaluation = json.loads((ROOT / "artifacts/week11_initial_evaluation.json").read_text(encoding="utf-8"))["per_case_records"]
    records = {row["query_case_id"]: row for row in evaluation}
    response_template = {"review_version": "week13-human-explanation-review-v1", "reviewer": {"role_or_background": "", "review_date": "", "outside_reviewer": None}, "ratings": []}
    packet = [
        "# Week 13 Human Review Packet: Explanation Clarity and Trust",
        "",
        "## Purpose",
        "",
        "You will compare two presentations of exactly the same retrieved legal evidence. This is not legal advice and does not ask you to decide the case. Please assess clarity, traceability, and whether the presentation earns appropriate trust.",
        "",
        "## How to respond",
        "",
        "For each display, score: (1) clarity of where claims/evidence come from; (2) ease of finding source details; (3) appropriate trustworthiness without independently checking the source; and (4) whether uncertainty/limits are clear. Use 1=strongly disagree and 5=strongly agree. Add a short free-text note. The order is alternated to reduce simple first-display preference.",
        "",
    ]
    with psycopg.connect(os.getenv("LEGAL_XAI_DATABASE_URL", DEFAULT_DATABASE_URL)) as connection, connection.cursor() as cursor:
        for case_id, order in SAMPLES:
            record = records[case_id]
            cursor.execute("SELECT query_text FROM retrieval_runs WHERE run_id = %s", (record["retrieval_run_id"],))
            query = str(cursor.fetchone()[0])
            evidence: list[dict] = []
            for check in record["citation_checks"]:
                cursor.execute(
                    "SELECT source_id, citation, decision_date::text, court, page_number, chunk_text "
                    "FROM corpus_chunks WHERE chunk_id = %s", (check["chunk_id"],)
                )
                source_id, citation, date, court, page, text = cursor.fetchone()
                evidence.append({"source_id": source_id, "citation": citation, "decision_date": date, "court": court, "page_number": page, "text": text})
            excerpt = " ".join(query.split())[:1200] + ("..." if len(query) > 1200 else "")
            structured = display_structured(excerpt, evidence)
            flat = display_flat(excerpt, evidence)
            first, second = (structured, flat) if order == "structured_first" else (flat, structured)
            packet.extend([f"## Case `{case_id}`", "", first, "", "**Response for Display 1:** source clarity __/5; source-finding ease __/5; appropriate trust __/5; limits clear __/5; notes: ______", "", "---", "", second, "", "**Response for Display 2:** source clarity __/5; source-finding ease __/5; appropriate trust __/5; limits clear __/5; notes: ______", "", "**Comparison:** Which display better supports responsible legal research, and why? ______", ""])
            response_template["ratings"].append({"case_id": case_id, "presentation_order": order, "display_1": {"source_clarity": None, "source_finding_ease": None, "appropriate_trust": None, "limits_clear": None, "notes": ""}, "display_2": {"source_clarity": None, "source_finding_ease": None, "appropriate_trust": None, "limits_clear": None, "notes": ""}, "comparison_preference": "", "comparison_notes": ""})
    packet.extend(["## Reviewer declaration", "", "I reviewed these materials independently. I understand they are a small, non-random sample and that this review measures perceived explanation quality, not legal correctness. Name/initials (optional): ______", ""])
    (ROOT / "artifacts/week13_human_review_packet.md").write_text("\n".join(packet), encoding="utf-8")
    (ROOT / "artifacts/week13_review_response_template.json").write_text(json.dumps(response_template, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sample_cases": [case_id for case_id, _ in SAMPLES], "status": "review_packet_ready"}, indent=2))


if __name__ == "__main__":
    main()
