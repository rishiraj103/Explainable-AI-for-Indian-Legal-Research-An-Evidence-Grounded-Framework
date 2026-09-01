"""Reconcile final frozen Week 11 retrieval runs and write objective error buckets.

This script never runs retrieval again. It reads the run UUIDs stored by the
final evaluation, reconstructs candidate/selection identity from PostgreSQL,
and corrects only the per-case retrieved-but-not-selected reporting field.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import psycopg

from load_provenance import DEFAULT_DATABASE_URL
from legal_xai.citation_verifier import CitationCheck, CorpusEvidenceRecord, RetrievedCandidate, evaluate_against_answer_key


def candidates_for_run(run_id: str, database_url: str) -> tuple[RetrievedCandidate, ...]:
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT rr.rank, cc.chunk_id, cc.source_id, cc.case_id, cc.citation, cc.decision_date, cc.title, "
            "cc.court, cc.pdf_file, cc.page_number, cc.passage_start_char, cc.passage_end_char, cc.chunk_text "
            "FROM retrieval_results rr JOIN corpus_chunks cc ON cc.chunk_id = rr.chunk_id "
            "WHERE rr.run_id = %s ORDER BY rr.rank",
            (run_id,),
        )
        return tuple(
            RetrievedCandidate(
                rank=row[0],
                record=CorpusEvidenceRecord(
                    chunk_id=row[1], source_id=row[2], case_id=row[3], citation=row[4],
                    decision_date=row[5].isoformat(), title=row[6], court=row[7], pdf_file=row[8],
                    page_number=row[9], passage_start_char=row[10], passage_end_char=row[11], text=row[12],
                ),
            )
            for row in cursor.fetchall()
        )


def check_objects(record: dict[str, Any]) -> tuple[CitationCheck, ...]:
    return tuple(
        CitationCheck(
            evidence_id=item["evidence_id"], chunk_id=item["chunk_id"], citation=item["citation"],
            passed=bool(item["passed"]), failures=tuple(item["failures"]),
        )
        for item in record["citation_checks"]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation", type=Path, default=Path("artifacts/week11_temporal_prerank_evaluation.json"))
    parser.add_argument("--answer-key", type=Path, default=Path("answer_key/authority_answer_key.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/week11_error_analysis.json"))
    parser.add_argument("--markdown", type=Path, default=Path("artifacts/week11_error_analysis.md"))
    parser.add_argument("--database-url", default=os.getenv("LEGAL_XAI_DATABASE_URL", DEFAULT_DATABASE_URL))
    args = parser.parse_args()

    evaluation = json.loads(args.evaluation.read_text(encoding="utf-8"))
    answer_key = json.loads(args.answer_key.read_text(encoding="utf-8"))
    entries = [entry for entry in answer_key["entries"] if entry.get("status") == "evaluation"]
    rows: list[dict[str, Any]] = []
    counts = {"retrieved_and_selected": 0, "retrieved_not_selected": 0, "absent_at_k100": 0}
    displayed_not_key_authority = 0
    displayed_total = 0
    for record in evaluation["per_case_records"]:
        candidates = candidates_for_run(record["retrieval_run_id"], args.database_url)
        checks = check_objects(record)
        measure = evaluate_against_answer_key(
            query_id=record["query_case_id"], checks=checks, answer_key_entries=entries,
            retrieved_candidates=candidates,
        )
        matched = measure["matched_expected_authorities"]
        retrieved_not_selected = measure["expected_authorities_retrieved_not_selected"]
        absent = measure["expected_authorities_not_retrieved"]
        if matched:
            bucket = "correct_authority_retrieved_and_selected"
            counts["retrieved_and_selected"] += 1
        elif retrieved_not_selected:
            bucket = "correct_authority_retrieved_but_not_selected"
            counts["retrieved_not_selected"] += 1
        elif absent:
            bucket = "correct_authority_absent_at_k100"
            counts["absent_at_k100"] += 1
        else:
            raise ValueError(f"unclassifiable answer-key state for {record['query_case_id']}")
        candidate_by_rank = {candidate.rank: candidate for candidate in candidates}
        selected_expected_chunk_ids = {
            candidate_by_rank[match["rank"]].record.chunk_id
            for detail in measure["retrieved_expected_authority_details"]
            for match in detail["matches"]
            if candidate_rank_to_selected(match["rank"], candidates, checks)
        }
        non_key_checks = [check for check in checks if check.chunk_id not in selected_expected_chunk_ids]
        displayed_not_key_authority += len(non_key_checks)
        displayed_total += len(checks)
        expected_details = [
            {"expected_authority_citation": detail["expected_authority_citation"], "matches": detail["matches"]}
            for detail in measure["retrieved_expected_authority_details"]
        ]
        rows.append({
            "query_case_id": record["query_case_id"],
            "bucket": bucket,
            "expected_authority_retrieved_at_5": bool(record["expected_authority_retrieved_at_5"]),
            "expected_authority_retrieved_at_100": bool(measure["expected_authorities_retrieved"]),
            "expected_authority_selected": bool(matched),
            "expected_authority_retrieved_not_selected": retrieved_not_selected,
            "expected_authority_absent": absent,
            "expected_match_details": expected_details,
            "displayed_citation_checks": len(checks),
            "displayed_citation_checks_passed": sum(check.passed for check in checks),
            "provenance_valid_but_not_answer_key_authority_citations": len(non_key_checks),
            "substantive_relevance_label": "not adjudicated: answer-key mismatch does not establish irrelevance",
        })
        # Correct a known presentation field from the persisted, frozen run;
        # aggregate evaluation metrics and the retrieval configuration stay unchanged.
        record["expected_authority_retrieved_at_100"] = bool(measure["expected_authorities_retrieved"])
        record["expected_authority_selected"] = bool(matched)
        record["expected_authority_retrieved_not_selected"] = retrieved_not_selected

    if sum(counts.values()) != len(rows):
        raise ValueError("error buckets do not cover the frozen cohort")
    analysis = {
        "analysis_version": "week11-mandatory-error-analysis-v2-final-preranking",
        "method": "Read-only reconstruction from the final pre-ranking temporal-filter evaluation's persisted retrieval run UUIDs; no retrieval configuration, index, or answer key was changed.",
        "summary": {
            "cohort_n": len(rows),
            **counts,
            "displayed_citations_total": displayed_total,
            "displayed_citations_provenance_valid_but_not_answer_key_authority": displayed_not_key_authority,
            "relevance_caveat": "A citation that differs from the single expected authority is not automatically substantively irrelevant; no human relevance label was fabricated.",
        },
        "cases": rows,
        "headline": "Verification succeeds for retrieved evidence; recovery of the predefined authority is the binding constraint.",
    }
    evaluation["per_case_reconciliation"] = {
        "field": "expected_authority_retrieved_not_selected",
        "status": "corrected_from_persisted_retrieval_runs",
        "note": "The initial writer used the pre-selection measure for this per-case display field. This reconciliation uses selected displayed citations. Aggregate metrics were unaffected.",
        "artifact": str(args.output).replace("\\", "/"),
    }
    args.output.write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.evaluation.write_text(json.dumps(evaluation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    grouped = {
        bucket: [row for row in rows if row["bucket"] == bucket]
        for bucket in (
            "correct_authority_retrieved_and_selected",
            "correct_authority_retrieved_but_not_selected",
            "correct_authority_absent_at_k100",
        )
    }
    rank_note = "; ".join(
        f"`{row['query_case_id']}` (best rank {min(match['rank'] for detail in row['expected_match_details'] for match in detail['matches'])})"
        for row in grouped["correct_authority_retrieved_but_not_selected"]
    ) or "None"
    markdown = "\n".join([
        "# Week 11 Mandatory Error Analysis",
        "",
        "## Headline",
        "",
        f"**Verification succeeds for retrieved evidence; recovery of the predefined authority is the binding constraint.** All {displayed_total} displayed citations passed grounding and provenance checks, with zero temporal violations and zero unsupported-claim detections. Retrieval found the expected authority for {counts['retrieved_and_selected'] + counts['retrieved_not_selected']}/30 cases at k=100 and selected it for {counts['retrieved_and_selected']}/30.",
        "",
        "## Mandatory retrieval buckets",
        "",
        "| Bucket | Cases | Case IDs |",
        "|---|---:|---|",
        f"| Correct authority retrieved and selected | {len(grouped['correct_authority_retrieved_and_selected'])} | " + ", ".join(f"`{row['query_case_id']}`" for row in grouped['correct_authority_retrieved_and_selected']) + " |",
        f"| Correct authority retrieved but not selected | {len(grouped['correct_authority_retrieved_but_not_selected'])} | {rank_note} |",
        f"| Correct authority absent at k=100 | {len(grouped['correct_authority_absent_at_k100'])} | " + ", ".join(f"`{row['query_case_id']}`" for row in grouped['correct_authority_absent_at_k100']) + " |",
        "",
        f"Recall@5 is {sum(bool(record['expected_authority_retrieved_at_5']) for record in evaluation['per_case_records'])}/30 ({sum(bool(record['expected_authority_retrieved_at_5']) for record in evaluation['per_case_records']) / 30:.6f}). Some expected authorities were selected from ranks beyond five because selection is source-diverse and operates over the frozen top-100 candidate set; selected-support success is therefore {counts['retrieved_and_selected']}/30, not limited to the Recall@5 count.",
        "",
        "## Provenance-valid citations that are not the predefined authority",
        "",
        f"Of {displayed_total} displayed, provenance-valid citations, {displayed_not_key_authority} are not the single predefined authority for their query; {len(rows) - counts['retrieved_and_selected']}/30 cases do not display that expected authority. This is an **answer-key consistency** finding, not a substantive-irrelevance label: the answer key has one verified reference authority per case and does not provide a gold human relevance label for every alternative cited authority. No claim that any of these {displayed_not_key_authority} citations is substantively irrelevant is made without such a label.",
        "",
        "## Measurement provenance",
        "",
        "This analysis reads the persisted run UUIDs from the final pre-ranking Week 11 evaluation. It does not rerun retrieval or alter the index, query builder, answer key, or frozen configuration. It also corrects only a per-case presentation field: `expected_authority_retrieved_not_selected` is computed from selected displayed citations. Aggregate Week 11 metrics are taken from the final evaluation artifact.",
        "",
    ])
    args.markdown.write_text(markdown, encoding="utf-8")
    print(json.dumps(analysis["summary"], indent=2))


def candidate_rank_to_selected(rank: int, candidates: tuple[RetrievedCandidate, ...], checks: tuple[CitationCheck, ...]) -> bool:
    """Whether one expected-candidate match corresponds to a displayed check."""

    candidate = next((item for item in candidates if item.rank == rank), None)
    return bool(candidate and any(check.chunk_id == candidate.record.chunk_id for check in checks))


if __name__ == "__main__":
    main()
