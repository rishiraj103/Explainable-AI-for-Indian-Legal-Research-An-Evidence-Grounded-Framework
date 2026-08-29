"""Perform the one permitted post-decision retrieval confirmation on 11 test cases.

This is intentionally not a tuning tool: it has a fixed query list, reads the
already frozen test answer key, writes one dated record, and makes no config
decision from the results.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import psycopg

from legal_xai.answer_key import is_test_split_case, load_test_split_ids
from legal_xai.evidence_pipeline import retrieve_temporal_candidates, select_diverse_evidence


DATABASE_URL = "postgresql://legal_xai:legal_xai_local_only_2026@127.0.0.1:54329/legal_xai"
TEST_QUERIES = {
    "2008_1629": "resignation revised pay scale retrospective effect public undertaking",
    "1995_425": "panchayat secretary civil post government servant article 311",
    "2002_944": "constitutional 72nd amendment tribal representation constitutional validity",
    "1988_96": "Kerala General Sales Tax cashew shells purchase turnover processing",
    "1995_403": "unlawful assembly section 149 individual membership criminal liability death sentence",
    "1982_29": "temporary railway servant termination continuous service industrial disputes",
    "1994_632": "chief engineer eligibility transfer deputation Punjab service rules",
    "1985_40": "central excise exemption notification synthetic organic dyestuffs classification",
    "1992_84": "Companies Act section 73 interest liability public deposits company",
    "1995_412": "judicial restraint writ petition policy decision State government public interest",
    "1986_397": "dismissal special leave petition labour court writ article 226",
}
EXPECTED_SOURCE_IDS = {
    "2008_1629": "S_2006_2_582_600",
    "1995_425": "1967_1_679_684",
    "2002_944": "1993_1_891_1026",
    "1988_96": "1980_3_1271_1277",
    "1995_403": "1964_8_133_152",
    "1982_29": "1976_3_160_167",
    "1994_632": "1979_2_953_973",
    "1985_40": "1964_2_888_899",
    "1992_84": "1982_1_629_658",
    "1995_412": "1987_1_1_67",
    "1986_397": "1978_3_971_981",
}


def existing_run_status(case_id: str, query: str, expected_source_id: str, config: dict[str, object]) -> dict[str, object] | None:
    """Reuse the one already-persisted confirmation run if an interrupted run exists."""
    with psycopg.connect(DATABASE_URL) as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT run_id FROM retrieval_runs WHERE query_id = %s AND query_text = %s AND index_version = %s "
            "ORDER BY created_at_utc DESC LIMIT 1",
            (case_id, query, str(config["selection_version"])),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        run_id = str(row[0])
        cursor.execute(
            "SELECT r.rank, r.bm25_score, r.temporal_status, c.source_id "
            "FROM retrieval_results r JOIN corpus_chunks c ON c.chunk_id = r.chunk_id "
            "WHERE r.run_id = %s ORDER BY r.rank",
            (run_id,),
        )
        rows = cursor.fetchall()
    expected_rank = next((int(row[0]) for row in rows if row[3] == expected_source_id), None)
    selected_sources: set[str] = set()
    for rank, score, temporal_status, source_id in sorted(rows, key=lambda row: (-float(row[1]), int(row[0]))):
        if temporal_status != "eligible" or source_id in selected_sources:
            continue
        selected_sources.add(str(source_id))
        if len(selected_sources) == int(config["max_selected_evidence"]):
            break
    status = "retrieved_and_selected" if expected_source_id in selected_sources else (
        "retrieved_not_selected" if expected_rank is not None else "absent_at_k_100"
    )
    return {"run_id": run_id, "status": status, "best_bm25_rank": expected_rank}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"REJECTED: confirmation already exists at {args.output}; it must not be rerun.")

    answer_key = json.loads(Path("answer_key/authority_answer_key.json").read_text(encoding="utf-8"))
    entries = {entry["query_case_id"]: entry for entry in answer_key["entries"] if entry.get("status") == "evaluation"}
    if set(TEST_QUERIES) - set(entries):
        raise ValueError("one or more fixed confirmation IDs are absent from the evaluation answer key")
    test_ids = load_test_split_ids("corpus/ildc/single_test.parquet")
    config = json.loads(Path("config/evidence_selection.json").read_text(encoding="utf-8"))
    results: list[dict[str, object]] = []
    for case_id, query in TEST_QUERIES.items():
        if not is_test_split_case(case_id, test_ids):
            raise ValueError(f"non-test case entered final confirmation: {case_id}")
        entry = entries[case_id]
        expected = EXPECTED_SOURCE_IDS[case_id]
        # The first invocation was interrupted immediately after persisting the
        # 2008_1629 retrieval. Reuse only that exact run; all other test cases
        # receive their single post-decision confirmation retrieval below.
        prior = existing_run_status(case_id, query, expected, config) if case_id == "2008_1629" else None
        if prior is None:
            retrieval = retrieve_temporal_candidates(
                query_id=case_id,
                query_year=int(entry["query_decision_date"][:4]),
                query=query,
                candidate_k=int(config["candidate_k"]),
                index_path=Path("retrieval/bm25.sqlite"),
                database_url=DATABASE_URL,
                dedup_matches=Path("corpus/dedup_matches.csv"),
                index_version=str(config["selection_version"]),
            )
            rank = next((candidate.rank for candidate in retrieval.candidates if candidate.source_id == expected), None)
            selected = select_diverse_evidence(retrieval.candidates, int(config["max_selected_evidence"]))
            status = "retrieved_and_selected" if any(candidate.source_id == expected for candidate in selected) else (
                "retrieved_not_selected" if rank is not None else "absent_at_k_100"
            )
            run_id = retrieval.run_id
            excluded = retrieval.query_duplicate_chunks_excluded
        else:
            rank = prior["best_bm25_rank"]
            status = prior["status"]
            run_id = prior["run_id"]
            excluded = "reused_interrupted_confirmation_run"
        results.append({
            "query_case_id": case_id,
            "run_id": run_id,
            "expected_authority_source_id": expected,
            "query": query,
            "status": status,
            "best_bm25_rank": rank,
            "query_duplicate_chunks_excluded": excluded,
        })
    payload = {
        "artifact_version": "finalized-test-confirmation-v1",
        "purpose": "One-time post-freeze-decision confirmation only; results were not used for tuning.",
        "selection_config": config,
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote one-time finalized confirmation for {len(results)} fixed-test cases to {args.output}")


if __name__ == "__main__":
    main()
