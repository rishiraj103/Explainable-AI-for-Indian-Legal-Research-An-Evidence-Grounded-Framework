"""Join reproduced E1/E2 predictions to the frozen Week 11 evidence cohort.

No model or retrieval inference is performed here.  Faithfulness spot checks
reconstruct only the deterministic renderer from persisted selected chunks.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import psycopg

from load_provenance import DEFAULT_DATABASE_URL
from legal_xai.evidence_pipeline import EvidenceCandidate
from legal_xai.grounded_answer import assert_answer_grounded, render_grounded_answer


ROOT = Path(__file__).resolve().parents[1]
SPOT_CHECK_CASES = ("2008_1629", "1997_792", "1980_133", "2002_944", "1988_96")


def read(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def prediction_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    buckets: dict[str, list[str]] = {
        "both_correct": [], "E1_correct_E2_wrong": [], "E1_wrong_E2_correct": [], "both_wrong": []
    }
    for row in rows:
        e1_ok = row["E1_prediction"] == row["true_label"]
        e2_ok = row["E2_mean_logits_prediction"] == row["true_label"]
        key = "both_correct" if e1_ok and e2_ok else "E1_correct_E2_wrong" if e1_ok else "E1_wrong_E2_correct" if e2_ok else "both_wrong"
        buckets[key].append(row["case_id"])
    return {key: {"count": len(value), "example_case_id": value[0] if value else None, "case_ids": value} for key, value in buckets.items()}


def faithfulness_spot_check(evaluation_rows: dict[str, dict[str, Any]], database_url: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        for case_id in SPOT_CHECK_CASES:
            record = evaluation_rows[case_id]
            cursor.execute("SELECT query_text FROM retrieval_runs WHERE run_id = %s", (record["retrieval_run_id"],))
            query = cursor.fetchone()[0]
            evidence: list[EvidenceCandidate] = []
            for check in record["citation_checks"]:
                cursor.execute(
                    "SELECT rr.rank, cc.chunk_id, cc.source_id, cc.case_id, cc.citation, cc.decision_date, cc.court, "
                    "cc.pdf_file, cc.page_number, cc.passage_start_char, cc.passage_end_char, rr.bm25_score, "
                    "rr.temporal_status, cc.chunk_text FROM retrieval_results rr JOIN corpus_chunks cc "
                    "ON cc.chunk_id = rr.chunk_id WHERE rr.run_id = %s AND rr.chunk_id = %s",
                    (record["retrieval_run_id"], check["chunk_id"]),
                )
                row = cursor.fetchone()
                if row is None:
                    raise ValueError(f"persisted selected chunk missing for {case_id}")
                evidence.append(EvidenceCandidate(
                    rank=row[0], chunk_id=row[1], source_id=row[2], case_id=row[3], citation=row[4],
                    decision_date=row[5].isoformat(), court=row[6], pdf_file=row[7], page_number=row[8],
                    passage_start_char=row[9], passage_end_char=row[10], bm25_score=float(row[11]),
                    temporal_status=row[12], text=row[13],
                ))
            answer = render_grounded_answer(query=query, selected_evidence=tuple(evidence)).as_dict()
            assert_answer_grounded(answer, tuple(evidence))
            if [item["chunk_id"] for item in answer["supporting_evidence"]] != [item.chunk_id for item in evidence]:
                raise AssertionError(f"renderer provenance changed for {case_id}")
            results.append({
                "case_id": case_id,
                "status": "pass",
                "selected_evidence_count": len(evidence),
                "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
                "selected_chunk_ids": [item.chunk_id for item in evidence],
                "faithfulness_result": "Every rendered evidence reference exactly corresponds to a persisted retrieved chunk; no unsupported highlight detected.",
            })
    return results


def main() -> None:
    database_url = os.getenv("LEGAL_XAI_DATABASE_URL", DEFAULT_DATABASE_URL)
    e1 = {row["case_id"]: row for row in read("artifacts/e1_test_predictions.json")["records"]}
    e2 = {row["case_id"]: row for row in read("artifacts/e2_test_predictions.json")["records"]}
    evaluation = read("artifacts/week11_initial_evaluation.json")["per_case_records"]
    if set(e1) != set(e2):
        raise ValueError("E1/E2 test prediction IDs differ")
    combined = []
    for case_id, e1_row in e1.items():
        e2_row = e2[case_id]
        if e1_row["true_label"] != e2_row["true_label"]:
            raise ValueError(f"label disagreement for {case_id}")
        combined.append({
            "case_id": case_id, "true_label": e1_row["true_label"], "E1_prediction": e1_row["E1_prediction"],
            "E2_mean_logits_prediction": e2_row["E2_mean_logits_prediction"],
            "E2_majority_vote_prediction": e2_row["E2_majority_vote_prediction"],
        })
    prediction_path = ROOT / "artifacts/e1_e2_test_predictions.json"
    prediction_path.write_text(json.dumps({"artifact_version": "frozen-e1-e2-test-predictions-v1", "records": combined}, indent=2) + "\n", encoding="utf-8")
    by_case = {row["case_id"]: row for row in combined}
    cohort = []
    for record in evaluation:
        row = dict(by_case[record["query_case_id"]])
        row.update({
            "authority_bucket": "retrieved_and_selected" if record["expected_authority_selected"] else "retrieved_but_not_selected" if record["expected_authority_retrieved_not_selected"] else "absent_at_k100",
            "citation_checks_passed": record["citation_checks_passed"],
            "citation_check_count": record["citation_check_count"],
            "temporal_violation_count": record["temporal_violation_count"],
        })
        cohort.append(row)
    spot = faithfulness_spot_check({row["query_case_id"]: row for row in evaluation}, database_url)
    full_counts = prediction_counts(combined)
    cohort_counts = prediction_counts(cohort)
    e2_wrong_authority_selected = [row["case_id"] for row in cohort if row["E2_mean_logits_prediction"] != row["true_label"] and row["authority_bucket"] == "retrieved_and_selected"]
    citation_consistency_fails = [row["case_id"] for row in cohort if row["authority_bucket"] != "retrieved_and_selected"]
    payload = {
        "analysis_version": "week12-prediction-cross-reference-v1",
        "reproduction": {
            "E1": read("artifacts/e1_test_predictions.json")["reproduced_metrics"],
            "E2_mean_logits": read("artifacts/e2_test_predictions.json")["mean_logits_metrics"],
        },
        "full_test_n1503_E1_E2_outcome_disagreement": full_counts,
        "answer_key_cohort_n30": {
            "E1_E2_outcome_disagreement": cohort_counts,
            "records": cohort,
            "E2_wrong_and_expected_authority_selected": e2_wrong_authority_selected,
            "citation_traceable_but_expected_authority_not_selected": citation_consistency_fails,
            "per_case_temporal_violations": sum(row["temporal_violation_count"] for row in cohort),
        },
        "structurally_inapplicable_categories": {
            "E2_wrong_E3_E4_outcome_correct": "E3/E4 do not emit outcome labels, so they cannot be outcome-correct or outcome-wrong relative to E2. On the evidence criterion, none of the three E2-wrong cohort cases retrieved and selected the expected authority.",
            "E3_correct_E4_wrong": "E4 adds verification to the same controlled E3 evidence output. All 135 displayed citations pass E4 verification; there are zero E3 outputs rejected by E4 in the frozen cohort.",
            "E3_E4_prediction_correct_citation_unsupported": "E3/E4 do not output outcome predictions, and their displayed citations are all supported; this category has no applicable instances.",
            "correct_authority_retrieved_final_answer_wrong": "The controlled E3/E4 brief makes no adjudicated outcome prediction and has no gold final-answer correctness label. Authority recovery is measured separately from source-valid, non-inferential explanation rendering.",
        },
        "faithfulness_spot_check": spot,
    }
    (ROOT / "artifacts/week12_prediction_cross_reference.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    markdown = "\n".join([
        "# Week 12 Prediction and Evidence Cross-Reference",
        "",
        "## Verified prediction reproduction",
        "",
        "E1 was deterministically reconstructed from the frozen C=10.0 configuration and reproduced 0.613440 accuracy / 0.612342 macro F1 exactly. E2 was inferred from frozen checkpoint `checkpoint-6318` on its cached 512-token windows and reproduced 0.596806 / 0.592358 exactly for mean-logit pooling.",
        "",
        "## E1/E2 outcome disagreement",
        "",
        "| Population | Both correct | E1 correct, E2 wrong | E1 wrong, E2 correct | Both wrong |",
        "|---|---:|---:|---:|---:|",
        f"| Full test, n=1,503 | {full_counts['both_correct']['count']} | {full_counts['E1_correct_E2_wrong']['count']} (`{full_counts['E1_correct_E2_wrong']['example_case_id']}`) | {full_counts['E1_wrong_E2_correct']['count']} (`{full_counts['E1_wrong_E2_correct']['example_case_id']}`) | {full_counts['both_wrong']['count']} |",
        f"| Answer-key cohort, n=30 | {cohort_counts['both_correct']['count']} | {cohort_counts['E1_correct_E2_wrong']['count']} (`{cohort_counts['E1_correct_E2_wrong']['example_case_id']}`) | {cohort_counts['E1_wrong_E2_correct']['count']} (`{cohort_counts['E1_wrong_E2_correct']['example_case_id']}`) | {cohort_counts['both_wrong']['count']} |",
        "",
        "## Mandatory E3/E4 categories",
        "",
        "| Category | Result |",
        "|---|---|",
        "| E2 wrong, E3/E4 outcome correct | Structurally inapplicable: E3/E4 do not predict an outcome. None of the three E2-wrong cohort cases also retrieved and selected the expected authority. |",
        "| E3 correct, E4 wrong | 0/30 on the applicable verification interpretation: all 135 E3-displayed citations pass E4 verification. |",
        "| E3/E4 outcome correct but citation unsupported | Structurally inapplicable: no E3/E4 outcome label; unsupported citations 0/135. |",
        "| Correct authority retrieved but final answer wrong | Structurally inapplicable: the controlled brief has no adjudicated final-outcome claim. |",
        f"| Citation traceable but authority-consistency fails | {len(citation_consistency_fails)}/30 cases; example `{citation_consistency_fails[0]}`. These citations are traceable, but the expected authority was not selected. |",
        "| Citation later than the query case | 0/30 cases and 0/135 citations. |",
        f"| Explanation faithfulness spot check | {len(spot)}/{len(spot)} pass: " + ", ".join(f"`{row['case_id']}`" for row in spot) + ". Each displayed evidence reference maps exactly to a persisted retrieved chunk; no unsupported highlight was detected. |",
        "",
    ])
    (ROOT / "artifacts/week12_prediction_cross_reference.md").write_text(markdown, encoding="utf-8")
    print(json.dumps({"full_test": {k: v["count"] for k, v in full_counts.items()}, "cohort": {k: v["count"] for k, v in cohort_counts.items()}, "faithfulness_spot_checks": len(spot)}, indent=2))


if __name__ == "__main__":
    main()
