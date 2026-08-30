"""Run the single, paired real-answer-key query-builder regression check.

This is an audit-only final comparison.  Its fixed six-case population and
both query modes are hard-coded; it cannot select new cases or tune a third
configuration.  It compares the two builders against full frozen facts-only
input using the identical BM25 index and retrieval safeguards.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pyarrow.parquet as pq

from legal_xai.answer_key import is_test_split_case, load_test_split_ids
from legal_xai.evidence_pipeline import retrieve_temporal_candidates, select_diverse_evidence
from legal_xai.facts import extract_case_facts, load_facts_extraction_rule


DATABASE_URL = "postgresql://legal_xai:legal_xai_local_only_2026@127.0.0.1:54329/legal_xai"
CASES = {
    # The two historical retrieved-and-selected controls.
    "1995_412": {"expected_source_id": "1987_1_1_67", "historical_rank": 22, "historical_status": "retrieved_and_selected"},
    "1986_397": {"expected_source_id": "1978_3_971_981", "historical_rank": 2, "historical_status": "retrieved_and_selected"},
    # The four historical retrieved-but-not-selected controls.
    "2008_1629": {"expected_source_id": "S_2006_2_582_600", "historical_rank": 29, "historical_status": "retrieved_not_selected"},
    "1995_425": {"expected_source_id": "1967_1_679_684", "historical_rank": 56, "historical_status": "retrieved_not_selected"},
    "2002_944": {"expected_source_id": "1993_1_891_1026", "historical_rank": 75, "historical_status": "retrieved_not_selected"},
    "1988_96": {"expected_source_id": "1980_3_1271_1277", "historical_rank": 96, "historical_status": "retrieved_not_selected"},
}


def load_test_texts(case_ids: set[str]) -> dict[str, str]:
    table = pq.read_table(
        "corpus/ildc/single_test.parquet", columns=["id", "text"], filters=[("id", "in", sorted(case_ids))]
    )
    texts = {str(row["id"]): str(row["text"] or "") for row in table.to_pylist()}
    if set(texts) != case_ids:
        raise ValueError(f"missing fixed-test facts input: {sorted(case_ids - set(texts))}")
    return texts


def outcome(retrieval: object, expected_source_id: str) -> dict[str, object]:
    rank = next((item.rank for item in retrieval.candidates if item.source_id == expected_source_id), None)
    selected = select_diverse_evidence(retrieval.candidates, 5)
    return {
        "run_id": retrieval.run_id,
        "rank": rank,
        "status": "retrieved_and_selected" if any(item.source_id == expected_source_id for item in selected) else (
            "retrieved_not_selected" if rank is not None else "absent"
        ),
        "query_duplicate_chunks_excluded": retrieval.query_duplicate_chunks_excluded,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("REJECTED: final regression artifact already exists; this pass must not be rerun")

    case_ids = set(CASES)
    test_ids = load_test_split_ids("corpus/ildc/single_test.parquet")
    if any(not is_test_split_case(case_id, test_ids) for case_id in case_ids):
        raise ValueError("final regression includes a non-test case")
    answer_key = json.loads(Path("answer_key/authority_answer_key.json").read_text(encoding="utf-8"))
    entries = {entry["query_case_id"]: entry for entry in answer_key["entries"] if entry.get("status") == "evaluation"}
    if case_ids - set(entries):
        raise ValueError("final regression case is absent from answer key")
    texts = load_test_texts(case_ids)
    rule = load_facts_extraction_rule("config/facts_extraction.json")

    results: list[dict[str, object]] = []
    for case_id, control in CASES.items():
        facts = extract_case_facts(texts[case_id], rule)
        per_mode: dict[str, dict[str, object]] = {}
        for mode in ("legacy_first_32", "salient_tfidf"):
            per_k: dict[str, object] = {}
            for candidate_k in (100, 500):
                retrieval = retrieve_temporal_candidates(
                    query_id=case_id,
                    query_year=int(entries[case_id]["query_decision_date"][:4]),
                    query=facts.text,
                    candidate_k=candidate_k,
                    index_path=Path("retrieval/bm25.sqlite"),
                    database_url=DATABASE_URL,
                    dedup_matches=Path("corpus/dedup_matches.csv"),
                    index_version=f"week9-freeze-regression-{mode}-v1",
                    query_mode=mode,
                )
                per_k[str(candidate_k)] = outcome(retrieval, str(control["expected_source_id"]))
            per_mode[mode] = per_k
        legacy_rank = per_mode["legacy_first_32"]["500"]["rank"]
        salient_rank = per_mode["salient_tfidf"]["500"]["rank"]
        # Any rank deterioration, including a previously found authority
        # disappearing, means the salient candidate cannot dominate this control.
        non_worsening = legacy_rank is None or (salient_rank is not None and salient_rank <= legacy_rank)
        results.append({
            "query_case_id": case_id,
            "expected_authority_source_id": control["expected_source_id"],
            "historical_issue_query_result": {
                "rank": control["historical_rank"], "status": control["historical_status"],
            },
            "facts_boundary_reason": facts.boundary_reason,
            "facts_word_count": len(facts.text.split()),
            "modes": per_mode,
            "salient_non_worsening_at_k500": non_worsening,
        })
    dominates = all(bool(row["salient_non_worsening_at_k500"]) for row in results)
    payload = {
        "artifact_version": "week9-final-freeze-regression-v1",
        "purpose": "One-time, non-iterative regression check; results determine only the final query-construction freeze decision.",
        "input_policy": "Both modes use identical full frozen facts-only input. Historical issue-query ranks identify controls but are not compared numerically to fresh facts-only ranks.",
        "index": "retrieval/bm25.sqlite (unchanged week7 BM25 index)",
        "candidate_ks": [100, 500],
        "results": results,
        "salient_strictly_non_worsening_on_all_six_at_k500": dominates,
        "freeze_recommendation": "adopt_salient_tfidf" if dominates else "keep_legacy_first_32",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote final paired regression for {len(results)} real answer-key cases to {args.output}")


if __name__ == "__main__":
    main()
