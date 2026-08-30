"""Build Week 12's frozen-result error analysis without rerunning any system."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def main() -> None:
    freeze = read("config/week11_evaluation_round.json")
    evaluation = read("artifacts/week11_initial_evaluation.json")
    errors = read("artifacts/week11_error_analysis.json")
    comparison = read("artifacts/e1_e2_comparison.json")
    outcomes = freeze["final_results"]["E3_E4_reference_authority_outcomes"]
    if errors["summary"]["retrieved_and_selected"] != outcomes["retrieved_and_selected"]:
        raise ValueError("error analysis and finalized freeze disagree")
    if sum(errors["summary"][key] for key in ("retrieved_and_selected", "retrieved_not_selected", "absent_at_k100")) != 30:
        raise ValueError("mandatory error buckets do not cover the frozen cohort")

    by_bucket = {}
    for row in errors["cases"]:
        by_bucket.setdefault(row["bucket"], []).append(row)
    selected = by_bucket["correct_authority_retrieved_and_selected"]
    deferred = by_bucket["correct_authority_retrieved_but_not_selected"]
    absent = by_bucket["correct_authority_absent_at_k100"]
    e1 = comparison["E1"]
    e2 = comparison["E2_corrected"]["mean_logits_primary"]
    payload = {
        "analysis_version": "week12-frozen-result-error-analysis-v1",
        "basis": {
            "week11_freeze": "config/week11_evaluation_round.json",
            "week11_metrics": "artifacts/week11_initial_evaluation.json",
            "week11_error_buckets": "artifacts/week11_error_analysis.json",
            "no_reruns_or_configuration_changes": True,
        },
        "mandatory_categories": {
            "E1_vs_E2_outcome_prediction": {
                "aggregate": {
                    "E1_accuracy": e1["accuracy"], "E1_macro_f1": e1["macro_f1"],
                    "E2_mean_logit_accuracy": e2["accuracy"], "E2_mean_logit_macro_f1": e2["macro_f1"],
                    "accuracy_difference_E2_minus_E1": comparison["accuracy_difference_vs_E1"]["mean_logits"],
                },
                "case_level_disagreement_examples": "Unavailable: the frozen E1/E2 artifacts retain aggregate metrics and confusion matrices, not per-case prediction vectors. No model was rerun merely to manufacture post-hoc examples.",
            },
            "correct_authority_retrieved_and_selected": [row["query_case_id"] for row in selected],
            "correct_authority_retrieved_but_not_selected": [
                {"query_case_id": row["query_case_id"], "details": row["expected_match_details"]}
                for row in deferred
            ],
            "correct_authority_absent_at_k100": [row["query_case_id"] for row in absent],
            "provenance_valid_but_substantive_relevance_unadjudicated": {
                "citation_items": errors["summary"]["displayed_citations_provenance_valid_but_not_answer_key_authority"],
                "explanation": errors["summary"]["relevance_caveat"],
            },
            "temporal_integrity": {
                "temporal_violations": 0,
                "interpretation": "No date-rule violation occurred in the frozen 30-case run, so there is no violation example to select."
            },
            "E3_E4_outcome_comparison": "Not applicable: E3/E4 are evidence-retrieval/explanation systems and do not emit an outcome label.",
        },
        "central_finding": "Verification succeeds for retrieved evidence, but expected-authority retrieval coverage is the binding limitation: 11/30 selected, 1/30 retrieved but not selected, and 18/30 absent at k=100.",
    }
    json_path = ROOT / "artifacts/week12_error_analysis.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    selected_ids = ", ".join(f"`{row['query_case_id']}`" for row in selected)
    absent_ids = ", ".join(f"`{row['query_case_id']}`" for row in absent)
    markdown = "\n".join([
        "# Week 12 Error Analysis",
        "",
        "## Basis and scope",
        "",
        "This analysis uses the finalized Week 11 records only. It does not rerun a model, change retrieval, alter the answer key, or tune on test outcomes. E1/E2 outcome metrics are final at n=1,503; E3/E4 authority and integrity measures are final at n=30 for this evaluation round.",
        "",
        "## Central finding",
        "",
        "**Verification succeeds for retrieved evidence; expected-authority retrieval coverage is the binding limitation.** The frozen E4 verifier accepted all 135 displayed citations with zero temporal violations and zero unsupported-claim detections, while only 11/30 expected authorities were selected and 18/30 were absent at k=100.",
        "",
        "## Mandatory categories",
        "",
        "| Category | Result |",
        "|---|---|",
        f"| E1 versus E2 | E1 accuracy/macro F1: {e1['accuracy']:.6f}/{e1['macro_f1']:.6f}; corrected E2 mean-logit: {e2['accuracy']:.6f}/{e2['macro_f1']:.6f}. E2 trails E1 by {-comparison['accuracy_difference_vs_E1']['mean_logits']:.6f} accuracy. Per-case prediction vectors were not retained, so no post-hoc disagreement example is fabricated. |",
        f"| Correct authority retrieved and selected | {len(selected)}/30: {selected_ids}. |",
        f"| Correct authority retrieved but not selected | {len(deferred)}/30: `1980_133`, with its first matching chunk at rank 48. This is the concrete selection-stage miss. |",
        f"| Correct authority absent at k=100 | {len(absent)}/30: {absent_ids}. |",
        f"| Provenance-valid but not answer-key authority | 124/135 displayed citations differ from the one reference authority per case. This is an answer-key-consistency finding, not evidence of substantive irrelevance without a human relevance label. |",
        "| Temporal violations | 0/135. No violation example exists in the frozen evaluation. |",
        "| E3/E4 outcome comparison | Not applicable: E3/E4 do not emit an outcome label. |",
        "",
        "## Interpretation for results/discussion",
        "",
        "The results distinguish two reliability properties. Once evidence is selected, the system reliably preserves provenance, grounding, and temporal eligibility. It does not reliably recover the single predefined authority within its candidate set, so high citation validity must not be presented as high authority coverage. The fixed five-source display policy also caps authority-consistent precision at 0.222222 with 4.5 displayed citations per case; observed precision is 0.081481 (36.7% of that ceiling).",
        "",
    ])
    (ROOT / "artifacts/week12_error_analysis.md").write_text(markdown, encoding="utf-8")
    print(json.dumps({"selected": len(selected), "retrieved_not_selected": len(deferred), "absent": len(absent)}, indent=2))


if __name__ == "__main__":
    main()
