"""Build the final Week 13 RQ3 paired-format review packet.

Each pair is rendered from one persisted, verified Week 11 E4 evidence set.
The structured and unstructured displays therefore differ only in presentation;
this script audits the citation-ID sequence for every pair before writing the
packet. It reads persisted data only and never reruns retrieval or changes a
frozen system setting.
"""

from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

import psycopg

from load_provenance import DEFAULT_DATABASE_URL


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_SPEC = (
    ("2008_1629", "clean_success"),
    ("1980_105", "clean_success_small_eligible_pool_top5"),
    ("1980_133", "retrieved_not_selected_rank_15"),
    ("1981_55", "retrieved_not_selected_rank_28"),
    ("1985_40", "retrieved_not_selected_rank_78"),
    ("1997_792", "citation_traceable_authority_consistency_failure"),
    ("2013_35", "absent_at_k100"),
)
RANDOMIZATION_SEED = 20260903
CONCLUSION = "No legal conclusion is inferred beyond the cited supporting evidence; review the verbatim passages and their provenance."
UNCERTAINTY = "This is an evidence-grounded research brief, not legal advice. It reports only selected retrieved passages and does not infer conclusions beyond them. Missing or incomplete evidence should be reviewed by a human."


def presentation_orders() -> dict[str, str]:
    """Use a reproducible shuffle so a rebuilt packet retains reviewer order."""
    rng = random.Random(RANDOMIZATION_SEED)
    return {
        case_id: rng.choice(("structured_first", "unstructured_first"))
        for case_id, _ in SAMPLE_SPEC
    }


def render_structured(query_excerpt: str, evidence: list[dict[str, Any]]) -> tuple[str, list[str]]:
    lines = ["### Structured, evidence-linked brief", "", "**Issue context (excerpt)**", query_excerpt, "", "**Authorities and source locators**"]
    for item in evidence:
        lines.append(
            f"- {item['evidence_id']}: {item['citation'] or 'No reporter citation'}; {item['decision_date']}; "
            f"{item['court']}; source `{item['source_id']}`; page {item['page_number']}; citation ID `{item['chunk_id']}`."
        )
    lines.extend(["", "**Supporting evidence**", ""])
    for item in evidence:
        lines.extend([
            f"{item['evidence_id']} (citation ID `{item['chunk_id']}`, verbatim):",
            "> " + item["text"].replace("\n", "\n> "),
            "",
        ])
    lines.extend(["**Conclusion**", CONCLUSION, "", "**Uncertainty**", UNCERTAINTY])
    return "\n".join(lines), [item["chunk_id"] for item in evidence]


def render_unstructured(query_excerpt: str, evidence: list[dict[str, Any]]) -> tuple[str, list[str]]:
    """Render identical material without the structured explanation order."""
    lines = ["### Unstructured evidence presentation", "", query_excerpt, ""]
    for item in evidence:
        lines.extend([
            (
                f"- {item['citation'] or 'No reporter citation'}; {item['decision_date']}; {item['court']}; "
                f"source `{item['source_id']}`; page {item['page_number']}; citation ID `{item['chunk_id']}`."
            ),
            item["text"],
            "",
        ])
    lines.extend([CONCLUSION, "", UNCERTAINTY])
    return "\n".join(lines), [item["chunk_id"] for item in evidence]


def response_row(case_id: str, order: str) -> dict[str, Any]:
    blank = {
        "source_clarity": None,
        "source_finding_ease": None,
        "appropriate_trust": None,
        "limits_clear": None,
        "notes": "",
    }
    return {
        "case_id": case_id,
        "presentation_order": order,
        "display_1": blank.copy(),
        "display_2": blank.copy(),
        "comparison_preference": "",
        "comparison_notes": "",
    }


def main() -> None:
    evaluation_path = ROOT / "artifacts/week11_temporal_prerank_evaluation.json"
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))["per_case_records"]
    records = {row["query_case_id"]: row for row in evaluation}
    missing = [case_id for case_id, _ in SAMPLE_SPEC if case_id not in records]
    if missing:
        raise ValueError(f"missing fixed sample cases: {missing}")

    orders = presentation_orders()
    response_template = {
        "review_version": "week13-human-explanation-review-v2-rq3-ablation",
        "reviewer": {"role_or_background": "", "review_date": "", "outside_reviewer": None},
        "ratings": [],
    }
    packet = [
        "# Week 13 Review Packet: RQ3 Explanation-Format Ablation",
        "",
        "## Purpose",
        "",
        "For each case, compare two presentations of the exact same verified retrieved evidence. One is structured; the other is unstructured. This is not legal advice and does not ask you to decide the case. Rate clarity, traceability, appropriate trust, and uncertainty communication.",
        "",
        "## Rating instructions",
        "",
        "For each display, score: source clarity; ease of locating source details; appropriate trustworthiness without independently checking sources; and clarity of uncertainty/limits. Use 1=strongly disagree and 5=strongly agree. Add a short note. The order is deterministically shuffled per case to reduce first-display preference. Do not assess legal correctness.",
        "",
    ]
    parity_rows: list[dict[str, Any]] = []

    with psycopg.connect(os.getenv("LEGAL_XAI_DATABASE_URL", DEFAULT_DATABASE_URL)) as connection, connection.cursor() as cursor:
        for case_id, sample_role in SAMPLE_SPEC:
            record = records[case_id]
            cursor.execute("SELECT query_text FROM retrieval_runs WHERE run_id = %s", (record["retrieval_run_id"],))
            result = cursor.fetchone()
            if result is None:
                raise ValueError(f"missing persisted query for {case_id}")
            query = str(result[0])
            excerpt = " ".join(query.split())[:1200] + ("..." if len(query) > 1200 else "")

            evidence: list[dict[str, Any]] = []
            for check in record["citation_checks"]:
                cursor.execute(
                    "SELECT source_id, citation, decision_date::text, court, page_number, chunk_text "
                    "FROM corpus_chunks WHERE chunk_id = %s",
                    (check["chunk_id"],),
                )
                row = cursor.fetchone()
                if row is None:
                    raise ValueError(f"missing cited chunk {check['chunk_id']}")
                source_id, citation, date, court, page, text = row
                if citation != check["citation"]:
                    raise ValueError(f"citation changed for {check['chunk_id']}")
                evidence.append({
                    "evidence_id": check["evidence_id"],
                    "chunk_id": check["chunk_id"],
                    "source_id": source_id,
                    "citation": citation,
                    "decision_date": date,
                    "court": court,
                    "page_number": page,
                    "text": text,
                })

            structured, structured_ids = render_structured(excerpt, evidence)
            unstructured, unstructured_ids = render_unstructured(excerpt, evidence)
            frozen_ids = [check["chunk_id"] for check in record["citation_checks"]]
            if structured_ids != unstructured_ids:
                raise ValueError(f"citation parity failure for {case_id}")
            if structured_ids != frozen_ids:
                raise ValueError(f"rendered citations do not match frozen E4 citations for {case_id}")

            order = orders[case_id]
            first, second = (structured, unstructured) if order == "structured_first" else (unstructured, structured)
            packet.extend([
                f"## Case `{case_id}`",
                "",
                first,
                "",
                "**Response for Display 1:** source clarity __/5; source-finding ease __/5; appropriate trust __/5; limits clear __/5; notes: ______",
                "",
                "---",
                "",
                second,
                "",
                "**Response for Display 2:** source clarity __/5; source-finding ease __/5; appropriate trust __/5; limits clear __/5; notes: ______",
                "",
                "**Comparison:** Which display better supports responsible legal research, and why? ______",
                "",
            ])
            response_template["ratings"].append(response_row(case_id, order))
            parity_rows.append({
                "case_id": case_id,
                "sample_role": sample_role,
                "presentation_order": order,
                "frozen_e4_citation_ids": frozen_ids,
                "structured_citation_ids": structured_ids,
                "unstructured_citation_ids": unstructured_ids,
                "citation_parity_passed": True,
                "citation_checks_passed": record["citation_checks_passed"],
            })

    packet.extend([
        "## Reviewer declaration",
        "",
        "I reviewed these materials independently. I understand they are a small, non-random sample and that this review measures perceived explanation quality, not legal correctness. Name/initials (optional): ______",
        "",
    ])
    audit = {
        "review_version": "week13-human-explanation-review-v2-rq3-ablation",
        "source": str(evaluation_path.relative_to(ROOT)).replace("\\", "/"),
        "derivation": "Read persisted final Week 11 E4 citation checks and corpus chunks only; no retrieval, model, answer-key, or frozen-setting change.",
        "randomization_seed": RANDOMIZATION_SEED,
        "sample_case_count": len(parity_rows),
        "sample_notes": {"absent_at_k100_case": "2013_35"},
        "per_case": parity_rows,
        "summary": {
            "citation_parity_passed": all(row["citation_parity_passed"] for row in parity_rows),
            "cases_with_exact_citation_parity": sum(row["citation_parity_passed"] for row in parity_rows),
            "total_citations_per_presentation": sum(len(row["structured_citation_ids"]) for row in parity_rows),
            "ratings_recorded": 0,
        },
    }
    (ROOT / "artifacts/week13_review_packet.md").write_text("\n".join(packet), encoding="utf-8")
    (ROOT / "artifacts/week13_review_response_template.json").write_text(json.dumps(response_template, indent=2) + "\n", encoding="utf-8")
    (ROOT / "artifacts/week13_rq3_ablation_parity.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(audit["summary"], indent=2))


if __name__ == "__main__":
    main()
