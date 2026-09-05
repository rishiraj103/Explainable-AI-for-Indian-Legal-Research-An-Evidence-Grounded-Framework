"""Run the frozen initial Week 11 evaluation without changing any configuration.

E1/E2 full-test values are reconciled from their frozen result artifacts.  E3
and E4 are run only on the separately frozen answer-key-covered test subset.
The script writes one immutable initial-run artifact; rerunning requires an
explicit --force flag so it cannot become iterative tuning on the test set.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import psycopg
import pyarrow.parquet as pq

from build_bm25_index import INDEX_VERSION
from load_provenance import DEFAULT_DATABASE_URL
from legal_xai.citation_verifier import CitationCheck, CorpusEvidenceRecord, RetrievedCandidate, evaluate_against_answer_key
from legal_xai.evidence_pipeline import retrieve_temporal_candidates, select_diverse_evidence
from legal_xai.facts import extract_case_facts, facts_input_is_eligible, load_facts_extraction_rule
from legal_xai.grounded_answer import assert_answer_grounded, render_grounded_answer
from run_grounded_answer_pipeline import verify_rendered_explanation


def ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None or not precision + recall:
        return None
    return round(2 * precision * recall / (precision + recall), 6)


def source_records(candidates: tuple[Any, ...], database_url: str) -> dict[str, CorpusEvidenceRecord]:
    """Load the exact provenance records used to score answer-key authority matches."""

    chunk_ids = [candidate.chunk_id for candidate in candidates]
    if not chunk_ids:
        return {}
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT chunk_id, source_id, case_id, citation, decision_date, title, court, pdf_file, "
            "page_number, passage_start_char, passage_end_char, chunk_text "
            "FROM corpus_chunks WHERE chunk_id = ANY(%s)",
            (chunk_ids,),
        )
        return {
            row[0]: CorpusEvidenceRecord(
                chunk_id=row[0], source_id=row[1], case_id=row[2], citation=row[3],
                decision_date=row[4].isoformat(), title=row[5], court=row[6], pdf_file=row[7],
                page_number=row[8], passage_start_char=row[9], passage_end_char=row[10], text=row[11],
            )
            for row in cursor.fetchall()
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", type=Path, default=Path("config/week11_evaluation_round.json"))
    parser.add_argument("--answer-key", type=Path, default=Path("answer_key/authority_answer_key.json"))
    parser.add_argument("--test-split", type=Path, default=Path("corpus/ildc/single_test.parquet"))
    parser.add_argument("--selection-config", type=Path, default=Path("config/evidence_selection.json"))
    parser.add_argument("--facts-config", type=Path, default=Path("config/facts_extraction.json"))
    parser.add_argument("--index", type=Path, default=Path("retrieval/bm25.sqlite"))
    parser.add_argument("--dedup-matches", type=Path, default=Path("corpus/dedup_matches.csv"))
    parser.add_argument("--e1-e2-results", type=Path, default=Path("artifacts/e1_e2_comparison.json"))
    parser.add_argument("--database-url", default=os.getenv("LEGAL_XAI_DATABASE_URL", DEFAULT_DATABASE_URL))
    parser.add_argument("--output", type=Path, default=Path("artifacts/week11_initial_evaluation.json"))
    parser.add_argument("--force", action="store_true", help="replace the initial-run artifact intentionally")
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        raise FileExistsError(f"{args.output} already exists; refusing to repeat a frozen test evaluation")

    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    answer_key = json.loads(args.answer_key.read_text(encoding="utf-8"))
    selection = json.loads(args.selection_config.read_text(encoding="utf-8"))
    e1_e2 = json.loads(args.e1_e2_results.read_text(encoding="utf-8"))
    expected_n = int(freeze["reference_evidence_set"]["final_case_count"])
    entries = [entry for entry in answer_key["entries"] if entry.get("status") == "evaluation"]
    if len(entries) != expected_n:
        raise ValueError("answer key does not match frozen Week 11 reference set")
    entry_by_id = {str(entry["query_case_id"]): entry for entry in entries}
    if len(entry_by_id) != expected_n:
        raise ValueError("answer key has duplicate evaluation case IDs")

    table = pq.read_table(args.test_split, columns=["id", "text", "label"])
    test_rows = {str(row["id"]): row for row in table.to_pylist()}
    missing = sorted(set(entry_by_id) - set(test_rows))
    if missing:
        raise ValueError(f"frozen answer-key cases missing from fixed test split: {missing}")
    rule = load_facts_extraction_rule(args.facts_config)

    records: list[dict[str, Any]] = []
    totals = {
        "expected": 0,
        "retrieved_at_5": 0,
        "retrieved_at_100": 0,
        "selected_expected": 0,
        "selected_total": 0,
        "citation_checks": 0,
        "citation_checks_passed": 0,
        "answers_all_citations_passed": 0,
        "temporal_violations": 0,
        "unsupported_answers": 0,
    }
    for case_id, entry in entry_by_id.items():
        source_text = str(test_rows[case_id]["text"] or "")
        facts = extract_case_facts(source_text, rule)
        if not facts_input_is_eligible(facts, rule):
            raise ValueError(f"frozen answer-key case {case_id} is ineligible under the shared facts rule")
        query_year = int(str(entry["query_decision_date"])[:4])
        retrieved = retrieve_temporal_candidates(
            query_id=case_id,
            query_year=query_year,
            query=facts.text,
            candidate_k=int(selection["candidate_k"]),
            index_path=args.index,
            database_url=args.database_url,
            dedup_matches=args.dedup_matches,
            index_version=f"{INDEX_VERSION};{selection['selection_version']};week11-initial-evaluation",
            query_mode="salient_tfidf",
        )
        selected = select_diverse_evidence(retrieved.candidates, int(selection["max_selected_evidence"]))
        answer = render_grounded_answer(query=facts.text, selected_evidence=selected).as_dict()
        unsupported = False
        try:
            assert_answer_grounded(answer, selected)
        except AssertionError:
            unsupported = True

        checks = verify_rendered_explanation(
            answer=answer, run_id=retrieved.run_id, query_id=case_id, query_year=query_year,
            database_url=args.database_url, dedup_matches=args.dedup_matches,
        )
        check_objects = tuple(
            CitationCheck(
                evidence_id=check["evidence_id"], chunk_id=check["chunk_id"], citation=check["citation"],
                passed=bool(check["passed"]), failures=tuple(check["failures"]),
            )
            for check in checks
        )
        provenance = source_records(retrieved.candidates, args.database_url)
        candidate_records = tuple(
            RetrievedCandidate(record=provenance[candidate.chunk_id], rank=candidate.rank)
            for candidate in retrieved.candidates if candidate.chunk_id in provenance
        )
        key_measure = evaluate_against_answer_key(
            query_id=case_id, checks=(), answer_key_entries=entries, retrieved_candidates=candidate_records,
        )
        selected_measure = evaluate_against_answer_key(
            query_id=case_id, checks=check_objects, answer_key_entries=entries, retrieved_candidates=candidate_records,
        )
        expected = len(key_measure["expected_authority_citations"])
        retrieved_at_5 = any(
            item["rank"] <= 5
            for detail in key_measure["retrieved_expected_authority_details"] for item in detail["matches"]
        )
        retrieved_at_100 = bool(key_measure["expected_authorities_retrieved"])
        selected_expected = bool(selected_measure["matched_expected_authorities"])
        selected_count = len(selected)
        passed_checks = sum(check["passed"] for check in checks)
        failed_checks = [check for check in checks if not check["passed"]]
        temporal_violations = sum(
            1 for candidate in selected if candidate.temporal_status != "eligible"
        ) + sum(any(failure.startswith("temporal_") for failure in check["failures"]) for check in failed_checks)

        totals["expected"] += expected
        totals["retrieved_at_5"] += int(retrieved_at_5)
        totals["retrieved_at_100"] += int(retrieved_at_100)
        totals["selected_expected"] += int(selected_expected)
        totals["selected_total"] += selected_count
        totals["citation_checks"] += len(checks)
        totals["citation_checks_passed"] += passed_checks
        totals["answers_all_citations_passed"] += int(len(checks) > 0 and passed_checks == len(checks))
        totals["temporal_violations"] += temporal_violations
        totals["unsupported_answers"] += int(unsupported)
        records.append({
            "query_case_id": case_id,
            "query_year": query_year,
            "label": int(test_rows[case_id]["label"]),
            "facts_word_count": len(facts.text.split()),
            "facts_sha256": hashlib.sha256(facts.text.encode("utf-8")).hexdigest(),
            "retrieval_run_id": retrieved.run_id,
            "candidate_count_after_safety_filters": len(retrieved.candidates),
            "selected_evidence_count": selected_count,
            "expected_authority_citations": key_measure["expected_authority_citations"],
            "expected_authority_retrieved_at_5": retrieved_at_5,
            "expected_authority_retrieved_at_100": retrieved_at_100,
            "expected_authority_selected": selected_expected,
            # This classification is selection-aware. `key_measure` intentionally
            # has no displayed checks so it can measure candidate retrieval; using
            # it here would wrongly classify every retrieved-and-selected authority
            # as retrieved-but-not-selected.
            "expected_authority_retrieved_not_selected": selected_measure["expected_authorities_retrieved_not_selected"],
            "citation_check_count": len(checks),
            "citation_checks_passed": passed_checks,
            "citation_checks": checks,
            "temporal_violation_count": temporal_violations,
            "unsupported_claim_detected": unsupported,
        })

    authority_precision = ratio(totals["selected_expected"], totals["selected_total"])
    authority_recall = ratio(totals["selected_expected"], totals["expected"])
    e3_e4_metrics = {
        "n": expected_n,
        "recall_at_5": ratio(totals["retrieved_at_5"], totals["expected"]),
        "recall_at_100": ratio(totals["retrieved_at_100"], totals["expected"]),
        "authority_consistent_precision": authority_precision,
        "authority_consistent_recall": authority_recall,
        "authority_consistent_f1": f1(authority_precision, authority_recall),
        "citation_groundedness_rate": ratio(totals["answers_all_citations_passed"], expected_n),
        "citation_provenance_validity": ratio(totals["citation_checks_passed"], totals["citation_checks"]),
        "temporal_violation_rate": ratio(totals["temporal_violations"], totals["selected_total"]),
        "unsupported_claim_rate": ratio(totals["unsupported_answers"], expected_n),
        "denominators": {
            "expected_authorities": totals["expected"],
            "selected_evidence_items": totals["selected_total"],
            "displayed_citation_checks": totals["citation_checks"],
        },
    }
    e1_e2_metrics = {
        "n": int(e1_e2["majority_class_baseline"]["label_counts"]["0"]) + int(e1_e2["majority_class_baseline"]["label_counts"]["1"]),
        "source": "artifacts/e1_e2_comparison.json; accepted frozen result records reconciled without retraining",
        "E1": {key: e1_e2["E1"][key] for key in ("accuracy", "macro_f1")},
        "E2_mean_logits": {key: e1_e2["E2_corrected"]["mean_logits_primary"][key] for key in ("accuracy", "macro_f1")},
        "E2_majority_vote": {key: e1_e2["E2_corrected"]["majority_vote_secondary"][key] for key in ("accuracy", "macro_f1")},
    }
    payload = {
        "evaluation_version": "week11-initial-quantitative-evaluation-v1",
        "freeze": {
            "evaluation_round_version": freeze["evaluation_round_version"],
            "frozen_from_commit": freeze["frozen_from_commit"],
            "reference_evidence_cases": expected_n,
        },
        "sample_sizes": freeze["metric_scope"],
        "E1_E2_outcome_prediction_full_test": e1_e2_metrics,
        "E3_retrieval_and_controlled_grounding_answer_key_subset": e3_e4_metrics,
        "E4_verified_retrieval_and_grounded_answer_key_subset": e3_e4_metrics,
        "interpretation": {
            "E3": "Frozen retrieval, five-source evidence selection, and controlled extract-only answer rendering. The metrics are measured on the answer-key-covered subset.",
            "E4": "The same frozen E3 pipeline with the citation/provenance/temporal verifier executed on every displayed evidence item. E3 and E4 share retrieval results; E4 adds hard verification rather than a different ranking model.",
            "outcome_prediction_for_E3_E4": "Not available: the frozen retrieval/explanation pipeline does not emit outcome predictions, so no outcome accuracy is fabricated for E3/E4.",
        },
        "per_case_records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "E1_E2_n": e1_e2_metrics["n"],
        "E3_E4_n": expected_n,
        "recall_at_5": e3_e4_metrics["recall_at_5"],
        "recall_at_100": e3_e4_metrics["recall_at_100"],
        "citation_groundedness_rate": e3_e4_metrics["citation_groundedness_rate"],
    }, indent=2))


if __name__ == "__main__":
    main()
