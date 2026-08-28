"""Retrieve BM25 evidence, enforce temporal eligibility, and log every rank."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from legal_xai.evidence_pipeline import retrieve_temporal_candidates
from build_bm25_index import INDEX_VERSION
from load_provenance import DEFAULT_DATABASE_URL


TEMPORAL_POLICY = "precedent_decision_year < ildc_query_year; same-year excluded as ambiguous"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query-id", required=True)
    parser.add_argument("--query-year", type=int, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--candidate-k", type=int, default=100)
    parser.add_argument("--index", type=Path, default=Path("retrieval/bm25.sqlite"))
    parser.add_argument("--database-url", default=os.getenv("LEGAL_XAI_DATABASE_URL", DEFAULT_DATABASE_URL))
    parser.add_argument("--output", type=Path, default=Path("artifacts/retrieval_result.json"))
    parser.add_argument("--dedup-matches", type=Path, default=Path("corpus/dedup_matches.csv"))
    args = parser.parse_args()
    if args.top_k < 1 or args.candidate_k < args.top_k:
        raise ValueError("candidate-k must be at least top-k, and both must be positive")

    retrieved = retrieve_temporal_candidates(
        query_id=args.query_id, query_year=args.query_year, query=args.query,
        candidate_k=args.candidate_k, index_path=args.index, database_url=args.database_url,
        dedup_matches=args.dedup_matches, index_version=INDEX_VERSION,
    )
    eligible = [item.as_dict() for item in retrieved.candidates if item.temporal_status == "eligible"][:args.top_k]
    result = {
        "run_id": retrieved.run_id,
        "query_id": retrieved.query_id,
        "query_year": retrieved.query_year,
        "query": retrieved.query,
        "candidate_count": len(retrieved.candidates),
        "query_duplicate_chunks_excluded": retrieved.query_duplicate_chunks_excluded,
        "eligible_returned": len(eligible),
        "status_counts": retrieved.status_counts,
        "eligible_results": eligible,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "eligible_results"}, indent=2))


if __name__ == "__main__":
    main()
