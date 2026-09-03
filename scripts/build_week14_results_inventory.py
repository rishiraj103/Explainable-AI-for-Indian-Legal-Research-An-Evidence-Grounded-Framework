"""Build a read-only inventory of final results available for Week 14 writing."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> dict[str, Any]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def main() -> None:
    comparison = read("artifacts/e1_e2_comparison.json")
    evaluation = read("artifacts/week11_temporal_prerank_evaluation.json")
    errors = read("artifacts/week12_error_analysis.json")
    case_errors = read("artifacts/week11_error_analysis.json")
    review = read("artifacts/week13_review_summary.json")
    review_status = read("artifacts/week13_review_status.json")
    ablation = read("artifacts/week13_rq3_ablation_parity.json")
    retrieval_summary = read_text("artifacts/retrieval_investigation_summary.md")

    e3 = evaluation["E3_retrieval_and_controlled_grounding_answer_key_subset"]
    e4 = evaluation["E4_verified_retrieval_and_grounded_answer_key_subset"]
    case_error_by_id = {row["query_case_id"]: row for row in case_errors["cases"]}
    expected_bucket_by_role = {
        "clean_success": "correct_authority_retrieved_and_selected",
        "clean_success_small_eligible_pool_top5": "correct_authority_retrieved_and_selected",
        "retrieved_not_selected_rank_15": "correct_authority_retrieved_but_not_selected",
        "retrieved_not_selected_rank_28": "correct_authority_retrieved_but_not_selected",
        "retrieved_not_selected_rank_78": "correct_authority_retrieved_but_not_selected",
        "citation_traceable_authority_consistency_failure": "correct_authority_absent_at_k100",
        "absent_at_k100": "correct_authority_absent_at_k100",
    }
    self_review_alignment = []
    for row in ablation["per_case"]:
        case_id = row["case_id"]
        final_case = case_error_by_id.get(case_id)
        expected_bucket = expected_bucket_by_role[row["sample_role"]]
        actual_bucket = final_case["bucket"] if final_case else None
        passed = (
            final_case is not None
            and actual_bucket == expected_bucket
            and row["citation_checks_passed"] == 5
            and row["citation_parity_passed"] is True
        )
        self_review_alignment.append({
            "case_id": case_id,
            "week13_sample_role": row["sample_role"],
            "final_week11_week12_bucket": actual_bucket,
            "expected_bucket_from_sample_role": expected_bucket,
            "displayed_citation_checks_passed": row["citation_checks_passed"],
            "citation_parity_passed": row["citation_parity_passed"],
            "passed": passed,
        })
    era_counts = Counter(f"{row['query_year'] // 10 * 10}s" for row in evaluation["per_case_records"])
    population_checks = [
        {
            "name": "Outcome-prediction population",
            "expected_n": 1503,
            "actual_n": evaluation["sample_sizes"]["E1_E2_outcome_prediction"]["n"],
            "source": "artifacts/week11_temporal_prerank_evaluation.json",
            "passed": evaluation["sample_sizes"]["E1_E2_outcome_prediction"]["n"] == 1503,
        },
        {
            "name": "Citation/grounding population",
            "expected_n": 30,
            "actual_n": evaluation["sample_sizes"]["E3_E4_evidence_citation_grounding_provenance"]["n"],
            "source": "artifacts/week11_temporal_prerank_evaluation.json",
            "passed": evaluation["sample_sizes"]["E3_E4_evidence_citation_grounding_provenance"]["n"] == 30,
        },
        {
            "name": "Explanation-format review population",
            "expected_n": 7,
            "actual_n": review["sample"]["case_count"],
            "source": "artifacts/week13_review_summary.json",
            "passed": review["sample"]["case_count"] == 7,
        },
    ]
    if "Three bounded investigations" not in retrieval_summary or "2013_35" not in retrieval_summary:
        raise ValueError("retrieval investigation summary does not contain the expected final narrative")
    inventory = {
        "inventory_version": "week14-final-results-evidence-inventory-v2-mechanism-and-consistency",
        "scope": "Read-only consolidation of final results for report drafting; no inference, retrieval, evaluation, answer-key edit, or configuration change.",
        "sources": {
            "E1_E2": "artifacts/e1_e2_comparison.json",
            "E3_E4": "artifacts/week11_temporal_prerank_evaluation.json",
            "error_analysis": "artifacts/week12_error_analysis.json",
            "per_case_error_analysis": "artifacts/week11_error_analysis.json",
            "retrieval_investigation": "artifacts/retrieval_investigation_summary.md",
            "review_packet_audit": "artifacts/week13_rq3_ablation_parity.json",
            "explanation_review": "artifacts/week13_review_summary.json",
            "review_status": "artifacts/week13_review_status.json",
        },
        "result_inventory": [
            {
                "area": "Outcome prediction",
                "population": "1,503 eligible fixed ILDC test cases",
                "measures": {
                    "majority_accuracy": comparison["majority_class_baseline"]["accuracy"],
                    "E1_accuracy": comparison["E1"]["accuracy"],
                    "E1_macro_f1": comparison["E1"]["macro_f1"],
                    "E2_mean_logit_accuracy": comparison["E2_corrected"]["mean_logits_primary"]["accuracy"],
                    "E2_mean_logit_macro_f1": comparison["E2_corrected"]["mean_logits_primary"]["macro_f1"],
                },
                "permitted_interpretation": "E1 outperformed corrected E2 mean-logit pooling on this frozen outcome-prediction population; both exceeded the majority-accuracy baseline.",
                "reporting_guard": "Do not use E3/E4 as outcome classifiers or fabricate an E4-minus-E3 prediction delta.",
            },
            {
                "area": "Authority recovery and verified evidence",
                "population": "30 source-verified answer-key-covered fixed-test cases; 150 selected/displayed citations",
                "measures": {
                    "expected_authority_recall_at_5": e3["recall_at_5"],
                    "expected_authority_recall_at_100": e3["recall_at_100"],
                    "retrieved_and_selected": errors["summary"]["retrieved_and_selected"],
                    "retrieved_not_selected": errors["summary"]["retrieved_not_selected"],
                    "absent_at_k100": errors["summary"]["absent_at_k100"],
                    "citation_groundedness_rate": e4["citation_groundedness_rate"],
                    "citation_provenance_validity": e4["citation_provenance_validity"],
                    "temporal_violation_rate": e4["temporal_violation_rate"],
                    "unsupported_claim_rate": e4["unsupported_claim_rate"],
                },
                "permitted_interpretation": "The final system verified every displayed citation while recovering the predefined authority for only part of the answer-key subset; verification quality and expected-authority recall must be reported separately.",
                "reporting_guard": "Authority consistency is defined against the source-first answer key and is not a human substantive-relevance judgment for alternative citations.",
            },
            {
                "area": "Explanation-format review",
                "population": "7 fixed paired cases; author self-review fallback",
                "measures": {
                    "structured_preferences": review["comparative_preferences"]["structured"],
                    "unstructured_preferences": review["comparative_preferences"]["unstructured"],
                    "no_preference": review["comparative_preferences"]["no preference"],
                    "structured_mean_ratings": review["mean_ratings"]["structured"],
                    "unstructured_mean_ratings": review["mean_ratings"]["unstructured"],
                },
                "permitted_interpretation": "The author self-review preferred the structured display on all seven paired cases and identified navigation and retrieval-noise triage as its perceived advantages.",
                "reporting_guard": "This is not independent human-review evidence, is non-random and small, and measures perceived explanation quality rather than legal correctness.",
            },
        ],
        "retrieval_mechanism": {
            "source": "artifacts/retrieval_investigation_summary.md",
            "summary": "Three bounded changes preceded the final freeze; their mechanism and effect must accompany final recall figures in Results.",
            "rounds": [
                {
                    "change": "Replace legacy first-32-term query construction with deterministic TF-IDF salient terms from the full facts-only input.",
                    "effect": "Removed opening procedural boilerplate without changing the BM25 architecture.",
                },
                {
                    "change": "Repair the direct shared-phrase self-match guard by retaining the 100 shared-six-token floor and requiring 80% unique source-phrase coverage.",
                    "effect": "Recovered three additional authorities in the corrected development probe and withdrew the prior broad lexical-mismatch claim.",
                },
                {
                    "change": "Apply the strict earlier-year temporal rule to the BM25 candidate relation before ranking and the top-100 cutoff.",
                    "effect": "Improved held-out Recall@5 from 5/30 to 12/30, Recall@100 from 12/30 to 15/30, and selected expected authorities from 11/30 to 12/30, without losing any original retrieval successes.",
                },
            ],
        },
        "indexed_qualitative_findings": [
            {
                "finding": "Boilerplate-uncertainty miscalibration",
                "source": "artifacts/week13_review_summary.md (Case 2013_35)",
                "summary": "The identical generic uncertainty language was visually clear but did not adapt to the high coherence of 2013_35's evidence; it signalled the same caution level as noisier evidence sets. This is a system-level limitation, not a format-specific result.",
            },
            {
                "finding": "Eligible-pool size and lexical relevance are independent contributors",
                "source": "artifacts/retrieval_investigation_summary.md",
                "summary": "2013_35 remained absent despite 79 eligible candidates in its former raw top-100, while 1980_105 was recovered despite only three eligible raw candidates and became a top-5 hit after the final filter. This indicates residual lexical/relevance or ranking limitations beyond temporal filtering alone.",
            },
        ],
        "answer_key_era_distribution": {
            "source": "artifacts/week11_temporal_prerank_evaluation.json",
            "counts_by_query_decade": dict(sorted(era_counts.items())),
            "1980s_count": era_counts["1980s"],
            "answer_key_case_count": len(evaluation["per_case_records"]),
            "summary": f"The corrected 30-case answer-key subset contains {era_counts['1980s']}/30 cases from the 1980s, so this era is overrepresented in the evaluated authority-recovery sample.",
        },
        "consistency_checks": {
            "self_review_case_alignment": {
                "source": "artifacts/week13_rq3_ablation_parity.json cross-checked with artifacts/week11_error_analysis.json",
                "description": "Each of the seven Week 13 self-review case IDs must occur in the final 30-case answer-key analysis, with a retrieval-outcome bucket consistent with its declared sample role; each must retain five passed displayed citation checks and exact structured/unstructured citation parity.",
                "rows": self_review_alignment,
                "passed": all(row["passed"] for row in self_review_alignment),
            },
            "population_separation": {
                "description": "Outcome prediction, citation/grounding, and explanation-format observations are stored in separate inventory rows and may not be aggregated or compared as one common population.",
                "checks": population_checks,
                "passed": all(check["passed"] for check in population_checks),
            },
        },
        "cross_cutting_reporting_guards": [
            "Keep the 1,503-case outcome-prediction population distinct from the 30-case source-verified answer-key subset and the 7-case self-review sample.",
            "Use only the final pre-ranking temporal-filter evaluation; do not present the superseded post-ranking result as final.",
            "The strict temporal rule is earlier decision year only because ILDC query dates are year-granular.",
            "The Week 13 review status is " + review_status["reviewer_status"] + "; it cannot be generalized as an independent reviewer result.",
        ],
    }
    (ROOT / "artifacts/week14_results_evidence_inventory.json").write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    markdown = [
        "# Week 14 Results Evidence Inventory",
        "",
        "## Scope",
        "",
        inventory["scope"],
        "",
        "## Results available for report drafting",
        "",
        "| Area | Population | Measured result | Permitted interpretation |",
        "|---|---|---|---|",
        (
            "| Outcome prediction | 1,503 eligible fixed test cases | "
            f"E1 accuracy {comparison['E1']['accuracy']:.4f}, macro F1 {comparison['E1']['macro_f1']:.4f}; "
            f"corrected E2 accuracy {comparison['E2_corrected']['mean_logits_primary']['accuracy']:.4f}, macro F1 {comparison['E2_corrected']['mean_logits_primary']['macro_f1']:.4f}; "
            f"majority accuracy {comparison['majority_class_baseline']['accuracy']:.4f} | E1 leads corrected E2 on this frozen outcome task; both exceed majority accuracy. |"
        ),
        (
            "| Authority recovery and verified evidence | 30 answer-key cases; 150 displayed citations | "
            f"Recall@5 {e3['recall_at_5']:.2f}; Recall@100 {e3['recall_at_100']:.2f}; "
            f"12 selected / 3 retrieved-not-selected / 15 absent; 150/150 displayed citations grounded, provenance-valid, and temporally eligible | "
            "Report verification quality separately from predefined-authority recovery. |"
        ),
        (
            "| Explanation-format review | 7 fixed paired cases; author self-review fallback | "
            f"Structured preference {review['comparative_preferences']['structured']}/7; "
            f"structured vs. unstructured source-clarity mean {review['mean_ratings']['structured']['source_clarity']:.2f} vs. {review['mean_ratings']['unstructured']['source_clarity']:.2f} | "
            "Descriptive author self-review only; not an independent human-review or legal-correctness result. |"
        ),
        "",
        "## Mandatory reporting guards",
        "",
        *[f"- {guard}" for guard in inventory["cross_cutting_reporting_guards"]],
        "",
        "## Retrieval mechanism behind the final recall figures",
        "",
        f"Source: `{inventory['retrieval_mechanism']['source']}`. {inventory['retrieval_mechanism']['summary']}",
        "",
        *[f"- **Round {index}:** {round_['change']} {round_['effect']}" for index, round_ in enumerate(inventory["retrieval_mechanism"]["rounds"], start=1)],
        "",
        "## Indexed qualitative findings",
        "",
        *[f"- **{item['finding']}** — Source: `{item['source']}`. {item['summary']}" for item in inventory["indexed_qualitative_findings"]],
        "",
        "## Answer-key era distribution",
        "",
        f"Source: `artifacts/week11_temporal_prerank_evaluation.json`. {inventory['answer_key_era_distribution']['summary']}",
        "",
        "| Query-case decade | Cases |",
        "|---|---:|",
        *[f"| {decade} | {count} |" for decade, count in inventory["answer_key_era_distribution"]["counts_by_query_decade"].items()],
        "",
        "## Explicit consistency checks",
        "",
        f"- **Self-review case alignment:** {'PASS' if inventory['consistency_checks']['self_review_case_alignment']['passed'] else 'FAIL'}. All seven Week 13 sample cases occur in the final 30-case answer-key analysis with the expected retrieval-outcome bucket, five passed displayed citation checks, and exact format-pair citation parity.",
        f"- **Population separation:** {'PASS' if inventory['consistency_checks']['population_separation']['passed'] else 'FAIL'}. Outcome prediction is n=1,503, citation/grounding is n=30, and explanation-format review is n=7; no inventory row merges these populations.",
        "",
    ]
    (ROOT / "artifacts/week14_results_evidence_inventory.md").write_text("\n".join(markdown), encoding="utf-8")
    print(json.dumps({"areas": len(inventory["result_inventory"]), "status": "results_evidence_inventory_written"}, indent=2))


if __name__ == "__main__":
    main()
